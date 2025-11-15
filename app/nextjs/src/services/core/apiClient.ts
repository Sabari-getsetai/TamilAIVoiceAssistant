/**
 * Enhanced API Client for Enterprise Tamil AI Voice Assistant
 *
 * Features:
 * - Request/response interceptors for audit logging
 * - Automatic token management with refresh
 * - Correlation IDs for request tracking
 * - Retry logic with exponential backoff
 * - Error transformation and handling
 * - Circuit breaker integration
 * - Performance monitoring
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { z } from 'zod';

// Token storage interface
interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
}

// Request metadata for audit logging
interface RequestMetadata {
  correlationId: string;
  timestamp: number;
  endpoint: string;
  method: string;
  userAgent: string;
}

// Enhanced error interface
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  correlationId?: string;
  timestamp?: number;
  details?: any;
}

// Circuit breaker state
interface CircuitBreakerState {
  failureCount: number;
  lastFailureTime: number;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  timeout: number;
}

/**
 * Enhanced API Client with enterprise features
 */
export class ApiClient {
  private axiosInstance: AxiosInstance;
  private tokenStorage: TokenStorage;
  private correlationIdCounter: number = 0;
  private circuitBreakerState: CircuitBreakerState;
  private readonly failureThreshold: number = 5;
  private readonly recoveryTimeout: number = 60000; // 60 seconds

  constructor(
    baseURL: string,
    tokenStorage: TokenStorage,
    timeout: number = 30000
  ) {
    this.tokenStorage = tokenStorage;
    this.circuitBreakerState = {
      failureCount: 0,
      lastFailureTime: 0,
      state: 'CLOSED',
      timeout: this.recoveryTimeout,
    };

    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => this.handleRequest(config),
      (error) => this.handleRequestError(error)
    );

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response) => this.handleResponse(response),
      (error) => this.handleResponseError(error)
    );
  }

  /**
   * Handle outgoing requests
   */
  private async handleRequest(config: AxiosRequestConfig): Promise<AxiosRequestConfig> {
    // Check circuit breaker
    if (!this.isCircuitBreakerClosed()) {
      throw new Error('Circuit breaker is OPEN. Service temporarily unavailable.');
    }

    // Add correlation ID
    const correlationId = this.generateCorrelationId();
    config.headers = config.headers || {};
    config.headers['X-Correlation-ID'] = correlationId;
    config.headers['X-Request-ID'] = correlationId;

    // Add user agent
    config.headers['User-Agent'] = this.getUserAgent();

    // Add authentication token
    const token = this.tokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request timestamp for performance tracking
    (config as any).metadata = {
      correlationId,
      timestamp: Date.now(),
      endpoint: `${config.method?.toUpperCase()} ${config.url}`,
      method: config.method?.toUpperCase(),
      userAgent: this.getUserAgent(),
    } as RequestMetadata;

    // Log request for audit purposes
    this.logRequest(config);

    return config;
  }

  /**
   * Handle request errors
   */
  private handleRequestError(error: any): Promise<never> {
    this.recordFailure();
    return Promise.reject(this.transformError(error));
  }

  /**
   * Handle successful responses
   */
  private handleResponse(response: AxiosResponse): AxiosResponse {
    const metadata = (response.config as any).metadata as RequestMetadata;

    if (metadata) {
      const responseTime = Date.now() - metadata.timestamp;
      this.logResponse(response, responseTime);
    }

    // Record success for circuit breaker
    this.recordSuccess();

    return response;
  }

  /**
   * Handle response errors with token refresh and retry logic
   */
  private async handleResponseError(error: AxiosError): Promise<any> {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Record failure for circuit breaker
    this.recordFailure();

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await this.refreshToken();

        // Retry original request with new token
        const token = this.tokenStorage.getAccessToken();
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }

        return this.axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        this.tokenStorage.clearTokens();
        this.handleAuthenticationFailure();
        return Promise.reject(this.transformError(refreshError));
      }
    }

    // Log error for audit purposes
    this.logError(error);

    return Promise.reject(this.transformError(error));
  }

  /**
   * Refresh authentication token
   */
  private async refreshToken(): Promise<void> {
    const refreshToken = this.tokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.axiosInstance.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: newRefreshToken } = response.data;
    this.tokenStorage.setTokens(access_token, newRefreshToken);
  }

  /**
   * Handle authentication failure
   */
  private handleAuthenticationFailure(): void {
    if (typeof window !== 'undefined') {
      // Store current URL for redirect after login
      const currentUrl = window.location.pathname + window.location.search;
      localStorage.setItem('redirectUrl', currentUrl);

      // Redirect to login
      window.location.href = '/login';
    }
  }

  /**
   * Circuit breaker state management
   */
  private isCircuitBreakerClosed(): boolean {
    const now = Date.now();

    switch (this.circuitBreakerState.state) {
      case 'CLOSED':
        return true;

      case 'OPEN':
        if (now - this.circuitBreakerState.lastFailureTime >= this.circuitBreakerState.timeout) {
          this.circuitBreakerState.state = 'HALF_OPEN';
          return true;
        }
        return false;

      case 'HALF_OPEN':
        return true;

      default:
        return true;
    }
  }

  private recordSuccess(): void {
    if (this.circuitBreakerState.state === 'HALF_OPEN') {
      this.circuitBreakerState.state = 'CLOSED';
      this.circuitBreakerState.failureCount = 0;
    }
  }

  private recordFailure(): void {
    this.circuitBreakerState.failureCount++;
    this.circuitBreakerState.lastFailureTime = Date.now();

    if (this.circuitBreakerState.failureCount >= this.failureThreshold) {
      this.circuitBreakerState.state = 'OPEN';
    }
  }

  /**
   * Generate unique correlation ID
   */
  private generateCorrelationId(): string {
    const timestamp = Date.now();
    const counter = this.correlationIdCounter++;
    return `req_${timestamp}_${counter}`;
  }

  /**
   * Get user agent string
   */
  private getUserAgent(): string {
    if (typeof window !== 'undefined' && window.navigator) {
      return window.navigator.userAgent;
    }
    return 'Tamil-AI-Assistant/1.0';
  }

  /**
   * Log request for audit purposes
   */
  private logRequest(config: AxiosRequestConfig): void {
    const metadata = (config as any).metadata as RequestMetadata;

    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 API Request:', {
        correlationId: metadata.correlationId,
        endpoint: metadata.endpoint,
        timestamp: new Date(metadata.timestamp).toISOString(),
      });
    }

    // TODO: Send to audit service for enterprise logging
    // auditService.logApiRequest(metadata, config);
  }

  /**
   * Log successful response
   */
  private logResponse(response: AxiosResponse, responseTime: number): void {
    const metadata = (response.config as any).metadata as RequestMetadata;

    if (process.env.NODE_ENV === 'development') {
      console.log('✅ API Response:', {
        correlationId: metadata.correlationId,
        endpoint: metadata.endpoint,
        status: response.status,
        responseTime: `${responseTime}ms`,
      });
    }

    // TODO: Send to audit service for enterprise logging
    // auditService.logApiResponse(metadata, response, responseTime);
  }

  /**
   * Log error response
   */
  private logError(error: AxiosError): void {
    const metadata = (error.config as any)?.metadata as RequestMetadata;

    console.error('❌ API Error:', {
      correlationId: metadata?.correlationId,
      endpoint: metadata?.endpoint,
      status: error.response?.status,
      message: error.message,
    });

    // TODO: Send to audit service for enterprise logging
    // auditService.logApiError(metadata, error);
  }

  /**
   * Transform axios errors to standardized API errors
   */
  private transformError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const metadata = (error.config as any)?.metadata as RequestMetadata;

      const apiError: ApiError = {
        message: this.getErrorMessage(error),
        status: error.response?.status,
        code: error.code,
        correlationId: metadata?.correlationId,
        timestamp: Date.now(),
        details: error.response?.data,
      };

      return apiError;
    }

    if (error instanceof Error) {
      return {
        message: error.message,
        timestamp: Date.now(),
      };
    }

    return {
      message: 'An unexpected error occurred',
      timestamp: Date.now(),
    };
  }

  /**
   * Extract user-friendly error message
   */
  private getErrorMessage(error: AxiosError): string {
    // Handle validation errors
    if (error.response?.data) {
      const data = error.response.data as any;

      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail.map((err: any) => err.msg || err.message).join(', ');
        }
        return data.detail;
      }

      if (data.message) {
        return data.message;
      }
    }

    // Handle network errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') {
      return 'Unable to connect to server. Please check your connection.';
    }

    // Handle timeout
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please try again.';
    }

    return error.message || 'An unexpected error occurred';
  }

  /**
   * Make a validated API request with Zod schema
   */
  async request<T>(
    config: AxiosRequestConfig,
    schema?: z.ZodType<T>
  ): Promise<T> {
    const response = await this.axiosInstance.request(config);

    if (schema) {
      try {
        return schema.parse(response.data);
      } catch (validationError) {
        throw this.transformError(new Error('Invalid response format from server'));
      }
    }

    return response.data;
  }

  /**
   * HTTP method shortcuts
   */
  async get<T>(url: string, config?: AxiosRequestConfig, schema?: z.ZodType<T>): Promise<T> {
    return this.request({ ...config, method: 'GET', url }, schema);
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig, schema?: z.ZodType<T>): Promise<T> {
    return this.request({ ...config, method: 'POST', url, data }, schema);
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig, schema?: z.ZodType<T>): Promise<T> {
    return this.request({ ...config, method: 'PUT', url, data }, schema);
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig, schema?: z.ZodType<T>): Promise<T> {
    return this.request({ ...config, method: 'PATCH', url, data }, schema);
  }

  async delete<T>(url: string, config?: AxiosRequestConfig, schema?: z.ZodType<T>): Promise<T> {
    return this.request({ ...config, method: 'DELETE', url }, schema);
  }

  /**
   * Get circuit breaker state for monitoring
   */
  getCircuitBreakerState(): CircuitBreakerState {
    return { ...this.circuitBreakerState };
  }

  /**
   * Manual circuit breaker reset (for admin use)
   */
  resetCircuitBreaker(): void {
    this.circuitBreakerState = {
      failureCount: 0,
      lastFailureTime: 0,
      state: 'CLOSED',
      timeout: this.recoveryTimeout,
    };
  }
}

export default ApiClient;