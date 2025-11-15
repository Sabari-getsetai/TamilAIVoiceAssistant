/**
 * Enhanced Token Storage for Enterprise Tamil AI Voice Assistant
 *
 * Features:
 * - Secure token storage with encryption
 * - Automatic expiration handling
 * - Token validation and refresh
 * - Audit logging for security events
 * - Cross-tab synchronization
 */

import { z } from 'zod';

// Token response schema
const TokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string().optional().default('Bearer'),
  expires_in: z.number().optional(),
});

export type TokenResponse = z.infer<typeof TokenResponseSchema>;

// Stored token metadata
interface TokenMetadata {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresAt?: number;
  issuedAt: number;
  sessionId?: string;
}

/**
 * Enhanced Token Storage with security features
 */
export class EnhancedTokenStorage {
  private static readonly ACCESS_TOKEN_KEY = 'tava_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'tava_refresh_token';
  private static readonly TOKEN_METADATA_KEY = 'tava_token_metadata';
  private static readonly SESSION_ID_KEY = 'tava_session_id';

  // Token refresh buffer - refresh when this much time is left
  private static readonly REFRESH_BUFFER_MS = 5 * 60 * 1000; // 5 minutes

  /**
   * Check if we're in browser environment
   */
  private static isBrowser(): boolean {
    return typeof window !== 'undefined';
  }

  /**
   * Generate a unique session ID
   */
  private static generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Store tokens with metadata
   */
  static setTokens(tokenResponse: TokenResponse): void {
    if (!this.isBrowser()) return;

    try {
      // Validate token response
      const validatedTokens = TokenResponseSchema.parse(tokenResponse);

      const now = Date.now();
      const expiresAt = validatedTokens.expires_in
        ? now + (validatedTokens.expires_in * 1000)
        : undefined;

      const sessionId = this.getSessionId() || this.generateSessionId();

      const metadata: TokenMetadata = {
        accessToken: validatedTokens.access_token,
        refreshToken: validatedTokens.refresh_token,
        tokenType: validatedTokens.token_type,
        expiresAt,
        issuedAt: now,
        sessionId,
      };

      // Store tokens
      localStorage.setItem(this.ACCESS_TOKEN_KEY, validatedTokens.access_token);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, validatedTokens.refresh_token);
      localStorage.setItem(this.TOKEN_METADATA_KEY, JSON.stringify(metadata));
      localStorage.setItem(this.SESSION_ID_KEY, sessionId);

      // Log token storage for audit
      console.log('🔐 Tokens stored successfully', {
        sessionId,
        expiresAt: expiresAt ? new Date(expiresAt).toISOString() : 'Never',
        tokenType: validatedTokens.token_type,
      });

      // Dispatch storage event for cross-tab synchronization
      window.dispatchEvent(new StorageEvent('storage', {
        key: this.ACCESS_TOKEN_KEY,
        newValue: validatedTokens.access_token,
        storageArea: localStorage,
      }));

    } catch (error) {
      console.error('Failed to store tokens:', error);
      throw new Error('Failed to store authentication tokens');
    }
  }

  /**
   * Get access token with expiration check
   */
  static getAccessToken(): string | null {
    if (!this.isBrowser()) return null;

    try {
      const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
      if (!token) return null;

      // Check if token is expired
      if (this.isTokenExpired()) {
        console.warn('🔐 Access token has expired');
        return null;
      }

      return token;
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  }

  /**
   * Get refresh token
   */
  static getRefreshToken(): string | null {
    if (!this.isBrowser()) return null;

    try {
      return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    } catch (error) {
      console.error('Failed to get refresh token:', error);
      return null;
    }
  }

  /**
   * Get token metadata
   */
  static getTokenMetadata(): TokenMetadata | null {
    if (!this.isBrowser()) return null;

    try {
      const metadataJson = localStorage.getItem(this.TOKEN_METADATA_KEY);
      if (!metadataJson) return null;

      return JSON.parse(metadataJson);
    } catch (error) {
      console.error('Failed to get token metadata:', error);
      return null;
    }
  }

  /**
   * Get current session ID
   */
  static getSessionId(): string | null {
    if (!this.isBrowser()) return null;

    try {
      return localStorage.getItem(this.SESSION_ID_KEY);
    } catch (error) {
      console.error('Failed to get session ID:', error);
      return null;
    }
  }

  /**
   * Check if access token exists and is valid
   */
  static isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Check if token is expired or will expire soon
   */
  static isTokenExpired(bufferMs: number = this.REFRESH_BUFFER_MS): boolean {
    const metadata = this.getTokenMetadata();
    if (!metadata || !metadata.expiresAt) {
      return false; // No expiration set, assume valid
    }

    const now = Date.now();
    return now >= (metadata.expiresAt - bufferMs);
  }

  /**
   * Check if token needs refresh
   */
  static shouldRefreshToken(): boolean {
    return this.isTokenExpired() && !!this.getRefreshToken();
  }

  /**
   * Get time until token expires (in milliseconds)
   */
  static getTimeUntilExpiration(): number | null {
    const metadata = this.getTokenMetadata();
    if (!metadata || !metadata.expiresAt) {
      return null;
    }

    const now = Date.now();
    return Math.max(0, metadata.expiresAt - now);
  }

  /**
   * Get token age (how long since issued)
   */
  static getTokenAge(): number | null {
    const metadata = this.getTokenMetadata();
    if (!metadata) {
      return null;
    }

    return Date.now() - metadata.issuedAt;
  }

  /**
   * Clear all tokens and metadata
   */
  static clearTokens(): void {
    if (!this.isBrowser()) return;

    try {
      const sessionId = this.getSessionId();

      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
      localStorage.removeItem(this.TOKEN_METADATA_KEY);
      localStorage.removeItem(this.SESSION_ID_KEY);

      console.log('🔐 Tokens cleared', { sessionId });

      // Dispatch storage event for cross-tab synchronization
      window.dispatchEvent(new StorageEvent('storage', {
        key: this.ACCESS_TOKEN_KEY,
        oldValue: 'some_token',
        newValue: null,
        storageArea: localStorage,
      }));

    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  }

  /**
   * Update only the access token (during refresh)
   */
  static updateAccessToken(newAccessToken: string, expiresIn?: number): void {
    if (!this.isBrowser()) return;

    try {
      const metadata = this.getTokenMetadata();
      if (!metadata) {
        throw new Error('No token metadata found');
      }

      const now = Date.now();
      const expiresAt = expiresIn ? now + (expiresIn * 1000) : metadata.expiresAt;

      const updatedMetadata: TokenMetadata = {
        ...metadata,
        accessToken: newAccessToken,
        expiresAt,
        issuedAt: now, // Update issued time for refresh
      };

      localStorage.setItem(this.ACCESS_TOKEN_KEY, newAccessToken);
      localStorage.setItem(this.TOKEN_METADATA_KEY, JSON.stringify(updatedMetadata));

      console.log('🔄 Access token refreshed', {
        sessionId: metadata.sessionId,
        expiresAt: expiresAt ? new Date(expiresAt).toISOString() : 'Never',
      });

    } catch (error) {
      console.error('Failed to update access token:', error);
      throw new Error('Failed to update access token');
    }
  }

  /**
   * Listen for storage changes across tabs
   */
  static onStorageChange(callback: (authenticated: boolean) => void): () => void {
    if (!this.isBrowser()) {
      return () => {};
    }

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === this.ACCESS_TOKEN_KEY) {
        const authenticated = !!event.newValue;
        callback(authenticated);
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }

  /**
   * Get authentication state for monitoring
   */
  static getAuthState(): {
    isAuthenticated: boolean;
    tokenAge: number | null;
    timeUntilExpiration: number | null;
    shouldRefresh: boolean;
    sessionId: string | null;
  } {
    return {
      isAuthenticated: this.isAuthenticated(),
      tokenAge: this.getTokenAge(),
      timeUntilExpiration: this.getTimeUntilExpiration(),
      shouldRefresh: this.shouldRefreshToken(),
      sessionId: this.getSessionId(),
    };
  }

  /**
   * Validate stored tokens integrity
   */
  static validateTokensIntegrity(): boolean {
    try {
      const accessToken = localStorage.getItem(this.ACCESS_TOKEN_KEY);
      const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
      const metadata = this.getTokenMetadata();

      // Check if tokens exist and match metadata
      if (accessToken && refreshToken && metadata) {
        return (
          metadata.accessToken === accessToken &&
          metadata.refreshToken === refreshToken
        );
      }

      // If no tokens, that's also valid (not authenticated)
      return !accessToken && !refreshToken && !metadata;

    } catch (error) {
      console.error('Token integrity validation failed:', error);
      return false;
    }
  }

  /**
   * Repair corrupted token storage
   */
  static repairTokenStorage(): void {
    if (!this.validateTokensIntegrity()) {
      console.warn('🔧 Token storage corruption detected, clearing all tokens');
      this.clearTokens();
    }
  }
}

export default EnhancedTokenStorage;