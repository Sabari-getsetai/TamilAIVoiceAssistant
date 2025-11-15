/**
 * Centralized Error Handling for Enterprise Tamil AI Voice Assistant
 *
 * Features:
 * - Error classification and transformation
 * - User-friendly error messages
 * - Error reporting and logging
 * - Recovery suggestions
 * - Enterprise audit integration
 */

import { ApiError } from './apiClient';

// Error types for classification
export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  VALIDATION = 'VALIDATION',
  SERVER_ERROR = 'SERVER_ERROR',
  TIMEOUT = 'TIMEOUT',
  CIRCUIT_BREAKER = 'CIRCUIT_BREAKER',
  UNKNOWN = 'UNKNOWN',
}

// Error severity levels
export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

// Structured error interface
export interface EnhancedError {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  userMessage: string;
  code?: string;
  status?: number;
  correlationId?: string;
  timestamp: number;
  stack?: string;
  context?: Record<string, any>;
  recoveryActions?: string[];
  shouldReport?: boolean;
}

/**
 * Error classification and transformation
 */
export class ErrorHandler {
  /**
   * Transform any error into a structured EnhancedError
   */
  static transformError(error: unknown, context?: Record<string, any>): EnhancedError {
    // Handle API errors
    if (this.isApiError(error)) {
      return this.transformApiError(error, context);
    }

    // Handle standard JavaScript errors
    if (error instanceof Error) {
      return this.transformJavaScriptError(error, context);
    }

    // Handle unknown errors
    return {
      type: ErrorType.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      message: 'An unknown error occurred',
      userMessage: 'Something unexpected happened. Please try again.',
      timestamp: Date.now(),
      context,
      recoveryActions: ['Refresh the page', 'Try again later', 'Contact support if the problem persists'],
      shouldReport: true,
    };
  }

  /**
   * Transform API errors
   */
  private static transformApiError(error: ApiError, context?: Record<string, any>): EnhancedError {
    const type = this.classifyApiError(error);
    const severity = this.determineSeverity(type, error.status);

    return {
      type,
      severity,
      message: error.message,
      userMessage: this.generateUserMessage(type, error),
      code: error.code,
      status: error.status,
      correlationId: error.correlationId,
      timestamp: error.timestamp || Date.now(),
      context: { ...context, details: error.details },
      recoveryActions: this.generateRecoveryActions(type, error),
      shouldReport: this.shouldReportError(type, error.status),
    };
  }

  /**
   * Transform JavaScript errors
   */
  private static transformJavaScriptError(error: Error, context?: Record<string, any>): EnhancedError {
    const type = this.classifyJavaScriptError(error);
    const severity = this.determineSeverity(type);

    return {
      type,
      severity,
      message: error.message,
      userMessage: this.generateUserMessage(type, error),
      timestamp: Date.now(),
      stack: error.stack,
      context,
      recoveryActions: this.generateRecoveryActions(type),
      shouldReport: true,
    };
  }

  /**
   * Classify API errors based on status code and content
   */
  private static classifyApiError(error: ApiError): ErrorType {
    const status = error.status;

    if (!status) {
      if (error.code === 'ECONNABORTED') return ErrorType.TIMEOUT;
      if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') return ErrorType.NETWORK;
      if (error.message.includes('Circuit breaker')) return ErrorType.CIRCUIT_BREAKER;
      return ErrorType.NETWORK;
    }

    if (status === 401) return ErrorType.AUTHENTICATION;
    if (status === 403) return ErrorType.AUTHORIZATION;
    if (status >= 400 && status < 500) return ErrorType.VALIDATION;
    if (status >= 500) return ErrorType.SERVER_ERROR;

    return ErrorType.UNKNOWN;
  }

  /**
   * Classify JavaScript errors
   */
  private static classifyJavaScriptError(error: Error): ErrorType {
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('fetch')) {
      return ErrorType.NETWORK;
    }

    if (message.includes('timeout')) {
      return ErrorType.TIMEOUT;
    }

    if (message.includes('permission') || message.includes('denied')) {
      return ErrorType.AUTHORIZATION;
    }

    return ErrorType.UNKNOWN;
  }

  /**
   * Determine error severity
   */
  private static determineSeverity(type: ErrorType, status?: number): ErrorSeverity {
    switch (type) {
      case ErrorType.AUTHENTICATION:
      case ErrorType.AUTHORIZATION:
        return ErrorSeverity.HIGH;

      case ErrorType.SERVER_ERROR:
        return status && status >= 503 ? ErrorSeverity.CRITICAL : ErrorSeverity.HIGH;

      case ErrorType.CIRCUIT_BREAKER:
        return ErrorSeverity.CRITICAL;

      case ErrorType.NETWORK:
      case ErrorType.TIMEOUT:
        return ErrorSeverity.MEDIUM;

      case ErrorType.VALIDATION:
        return ErrorSeverity.LOW;

      default:
        return ErrorSeverity.MEDIUM;
    }
  }

  /**
   * Generate user-friendly error messages
   */
  private static generateUserMessage(type: ErrorType, error: any): string {
    switch (type) {
      case ErrorType.NETWORK:
        return 'Unable to connect to the server. Please check your internet connection.';

      case ErrorType.AUTHENTICATION:
        return 'Your session has expired. Please log in again.';

      case ErrorType.AUTHORIZATION:
        return 'You don\'t have permission to perform this action.';

      case ErrorType.VALIDATION:
        return error.message || 'Please check your input and try again.';

      case ErrorType.SERVER_ERROR:
        return 'A server error occurred. Our team has been notified. Please try again later.';

      case ErrorType.TIMEOUT:
        return 'The request took too long to complete. Please try again.';

      case ErrorType.CIRCUIT_BREAKER:
        return 'The service is temporarily unavailable due to high load. Please try again in a few minutes.';

      default:
        return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
    }
  }

  /**
   * Generate recovery action suggestions
   */
  private static generateRecoveryActions(type: ErrorType, error?: any): string[] {
    switch (type) {
      case ErrorType.NETWORK:
        return [
          'Check your internet connection',
          'Try refreshing the page',
          'Try again in a few moments',
        ];

      case ErrorType.AUTHENTICATION:
        return [
          'Log in again',
          'Clear your browser cache',
          'Contact support if you continue to have issues',
        ];

      case ErrorType.AUTHORIZATION:
        return [
          'Contact your administrator for access',
          'Ensure you have the correct permissions',
          'Try logging out and back in',
        ];

      case ErrorType.VALIDATION:
        return [
          'Check your input for errors',
          'Ensure all required fields are filled',
          'Try again with different values',
        ];

      case ErrorType.SERVER_ERROR:
        return [
          'Try again in a few minutes',
          'Refresh the page',
          'Contact support if the problem persists',
        ];

      case ErrorType.TIMEOUT:
        return [
          'Try again with a smaller request',
          'Check your internet connection',
          'Try again later',
        ];

      case ErrorType.CIRCUIT_BREAKER:
        return [
          'Wait a few minutes and try again',
          'Check service status page',
          'Contact support for urgent issues',
        ];

      default:
        return [
          'Refresh the page',
          'Try again later',
          'Contact support if the problem persists',
        ];
    }
  }

  /**
   * Determine if error should be reported to monitoring
   */
  private static shouldReportError(type: ErrorType, status?: number): boolean {
    // Always report server errors and unknown errors
    if (type === ErrorType.SERVER_ERROR || type === ErrorType.UNKNOWN) {
      return true;
    }

    // Report circuit breaker activations
    if (type === ErrorType.CIRCUIT_BREAKER) {
      return true;
    }

    // Don't report client validation errors
    if (type === ErrorType.VALIDATION && status && status < 500) {
      return false;
    }

    // Report everything else
    return true;
  }

  /**
   * Check if error is an API error
   */
  private static isApiError(error: unknown): error is ApiError {
    return (
      typeof error === 'object' &&
      error !== null &&
      'message' in error &&
      typeof (error as any).message === 'string'
    );
  }

  /**
   * Report error to monitoring/audit system
   */
  static async reportError(error: EnhancedError): Promise<void> {
    if (!error.shouldReport) {
      return;
    }

    try {
      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group(`🚨 Error Report [${error.severity}]`);
        console.error('Type:', error.type);
        console.error('Message:', error.message);
        console.error('User Message:', error.userMessage);
        console.error('Context:', error.context);
        console.error('Recovery Actions:', error.recoveryActions);
        if (error.stack) console.error('Stack:', error.stack);
        console.groupEnd();
      }

      // TODO: Send to error monitoring service (e.g., Sentry, DataDog)
      // TODO: Send to audit service for enterprise compliance
      // TODO: Send alerts for critical errors

      // For now, we'll store in local storage for development
      if (typeof window !== 'undefined') {
        const errorLog = localStorage.getItem('error_log');
        const errors = errorLog ? JSON.parse(errorLog) : [];
        errors.push({
          ...error,
          // Don't store stack traces in localStorage for privacy
          stack: undefined,
        });
        // Keep only last 50 errors
        if (errors.length > 50) {
          errors.splice(0, errors.length - 50);
        }
        localStorage.setItem('error_log', JSON.stringify(errors));
      }
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  /**
   * Get error statistics for monitoring dashboard
   */
  static getErrorStatistics(): any {
    if (typeof window === 'undefined') {
      return null;
    }

    try {
      const errorLog = localStorage.getItem('error_log');
      if (!errorLog) {
        return null;
      }

      const errors: EnhancedError[] = JSON.parse(errorLog);
      const last24Hours = Date.now() - 24 * 60 * 60 * 1000;
      const recentErrors = errors.filter(e => e.timestamp >= last24Hours);

      return {
        total: recentErrors.length,
        byType: recentErrors.reduce((acc, error) => {
          acc[error.type] = (acc[error.type] || 0) + 1;
          return acc;
        }, {} as Record<ErrorType, number>),
        bySeverity: recentErrors.reduce((acc, error) => {
          acc[error.severity] = (acc[error.severity] || 0) + 1;
          return acc;
        }, {} as Record<ErrorSeverity, number>),
        mostRecent: recentErrors.slice(-5),
      };
    } catch (error) {
      console.error('Failed to get error statistics:', error);
      return null;
    }
  }

  /**
   * Clear error log (for admin use)
   */
  static clearErrorLog(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('error_log');
    }
  }
}

export default ErrorHandler;