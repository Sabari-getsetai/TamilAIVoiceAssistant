import axios, { AxiosResponse } from 'axios';
import type {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  AuthError,
} from '../../types/auth';

// Configure axios defaults - use relative URLs for proxy
const API_BASE_URL = '/api';

const authApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token storage utilities
class TokenStorage {
  private static ACCESS_TOKEN_KEY = 'access_token';
  private static REFRESH_TOKEN_KEY = 'refresh_token';

  static getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static setAccessToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
  }

  static getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  static setTokens(accessToken: string, refreshToken: string): void {
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  }
}

// Request interceptor to add auth token
authApi.interceptors.request.use(
  (config) => {
    const token = TokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh
authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = TokenStorage.getRefreshToken();
        if (refreshToken) {
          const response = await authApi.post<TokenResponse>('/auth/refresh', {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          TokenStorage.setTokens(access_token, newRefreshToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return authApi(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        TokenStorage.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export class AuthApiService {
  /**
   * Register a new user
   */
  static async register(userData: RegisterRequest): Promise<User> {
    try {
      const response: AxiosResponse<User> = await authApi.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Login user
   */
  static async login(credentials: LoginRequest): Promise<{ user: User; tokens: TokenResponse }> {
    try {
      const response: AxiosResponse<TokenResponse> = await authApi.post('/auth/login', credentials);
      const tokens = response.data;

      // Store tokens
      TokenStorage.setTokens(tokens.access_token, tokens.refresh_token);

      // Get user profile
      const user = await this.getCurrentUser();

      return { user, tokens };
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get current user profile
   */
  static async getCurrentUser(): Promise<User> {
    try {
      const response: AxiosResponse<User> = await authApi.get('/auth/me');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Refresh access token
   */
  static async refreshToken(): Promise<TokenResponse> {
    try {
      const refreshToken = TokenStorage.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response: AxiosResponse<TokenResponse> = await authApi.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const tokens = response.data;
      TokenStorage.setTokens(tokens.access_token, tokens.refresh_token);

      return tokens;
    } catch (error) {
      TokenStorage.clearTokens();
      throw this.handleError(error);
    }
  }

  /**
   * Logout user
   */
  static async logout(): Promise<void> {
    try {
      await authApi.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      TokenStorage.clearTokens();
    }
  }

  /**
   * Update user profile
   */
  static async updateProfile(updateData: Partial<User>): Promise<User> {
    try {
      const response: AxiosResponse<User> = await authApi.put('/auth/me', updateData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated(): boolean {
    return !!TokenStorage.getAccessToken();
  }

  /**
   * Get stored access token
   */
  static getAccessToken(): string | null {
    return TokenStorage.getAccessToken();
  }

  /**
   * Handle API errors and convert to AuthError
   */
  private static handleError(error: unknown): AuthError {
    if (axios.isAxiosError(error)) {
      const response = error.response;
      if (response?.data) {
        // Handle validation errors
        if (response.data.detail) {
          return {
            message: Array.isArray(response.data.detail) 
              ? response.data.detail.map((err: { msg?: string; message?: string }) => err.msg || err.message).join(', ')
              : response.data.detail,
          };
        }
        if (response.data.message) {
          return { message: response.data.message };
        }
      }
      
      // Handle network errors
      if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') {
        return { message: 'Unable to connect to server. Please check your connection.' };
      }
      
      // Handle timeout
      if (error.code === 'ECONNABORTED') {
        return { message: 'Request timeout. Please try again.' };
      }
      
      return { message: error.message || 'An unexpected error occurred' };
    }

    if (error instanceof Error) {
      return { message: error.message };
    }

    return { message: 'An unexpected error occurred' };
  }
}

// Export the configured axios instance for use in other services
export { authApi };

// Export token storage for use in other parts of the app
export { TokenStorage };

export default AuthApiService;
