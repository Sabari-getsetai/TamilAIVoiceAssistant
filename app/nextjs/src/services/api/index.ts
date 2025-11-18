/**
 * Base API Configuration
 *
 * Central configuration for API calls to the backend
 * Provides Axios instance with proper error handling and interceptors
 */

import axios, { AxiosResponse, AxiosError } from 'axios';

// API Base URL Configuration
// In development, this can point directly to backend
// In production, this should be proxied by Next.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug API URL configuration
console.log('🔧 API Configuration:', {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_BASE_URL: API_BASE_URL,
  NODE_ENV: process.env.NODE_ENV
});

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication and logging
api.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log API requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and logging
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    }
    return response;
  },
  (error: AxiosError) => {
    // Enhanced error handling
    console.error(`❌ API Error:`, {
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      status: error.response?.status,
      statusText: error.response?.statusText,
      message: error.message,
    });

    // Handle specific error scenarios
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      // Handle forbidden
      console.warn('Access denied - insufficient permissions');
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error - please try again later');
    } else if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') {
      // Handle network errors
      console.error('Network error - check your connection');
    }

    return Promise.reject(error);
  }
);

// Helper function to handle API errors consistently
export const handleApiError = (error: AxiosError): string => {
  if (error.response?.data && typeof error.response.data === 'object') {
    const data = error.response.data as any;
    if (data.detail) return data.detail;
    if (data.message) return data.message;
    if (data.error) return data.error;
  }

  if (error.response?.status) {
    switch (error.response.status) {
      case 400:
        return 'Bad request - please check your input';
      case 401:
        return 'Authentication required';
      case 403:
        return 'Access denied';
      case 404:
        return 'Resource not found';
      case 500:
        return 'Server error - please try again later';
      default:
        return `Request failed with status ${error.response.status}`;
    }
  }

  if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') {
    return 'Unable to connect to server';
  }

  return error.message || 'An unexpected error occurred';
};

// Export API client services
export { default as orgDashboardApi } from './orgDashboardApi';
export { default as systemAdminApi } from './systemAdminApi';
export { organizationApi } from './organizationApi'; // Legacy organization API
export { default as AuthApiService } from './authApi';

// Export default instance
export default api;