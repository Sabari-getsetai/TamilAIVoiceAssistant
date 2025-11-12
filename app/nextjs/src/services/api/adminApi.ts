import axios from 'axios';
import { TokenStorage } from './authApi';
import type {
  UploadResponse,
  IngestionStatusResponse,
  DocumentsResponse,
  DocumentDetailResponse,
  IndexStatsResponse,
  ReindexResponse,
  ApiError,
} from '../../types';

// Configure axios defaults - use relative URLs for proxy
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
});

// Request interceptor for authentication and logging
api.interceptors.request.use(
  (config) => {
    // Add authentication token
    const token = TokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = TokenStorage.getRefreshToken();
        if (refreshToken) {
          // Use the auth API to refresh token
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = refreshResponse.data;
          TokenStorage.setTokens(access_token, newRefreshToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
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

    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class AdminApiService {
  /**
   * Upload documents for ingestion
   */
  static async uploadDocuments(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post<UploadResponse>('/admin/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Trigger document ingestion workflow
   */
  static async triggerIngestion(
    filePaths: string[],
    vectorStoreName: string = "default"
  ): Promise<IngestionStatusResponse> {
    const response = await api.post<IngestionStatusResponse>('/admin/ingest', {
      file_paths: filePaths,
      vector_store_name: vectorStoreName
    });
    return response.data;
  }

  /**
   * Get ingestion status
   */
  static async getIngestionStatus(jobId?: string): Promise<IngestionStatusResponse> {
    const params = jobId ? { job_id: jobId } : {};
    const response = await api.get<IngestionStatusResponse>('/admin/status', { params });
    return response.data;
  }

  /**
   * Get list of indexed documents
   */
  static async getDocuments(): Promise<DocumentsResponse> {
    const response = await api.get<DocumentsResponse>('/admin/documents');
    return response.data;
  }

  /**
   * Delete a document by ID
   */
  static async deleteDocument(docId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/admin/documents/${docId}`);
    return response.data;
  }

  /**
   * Get a specific document by ID
   */
  static async getDocument(docId: string): Promise<DocumentDetailResponse> {
    const response = await api.get<DocumentDetailResponse>(`/admin/documents/${docId}`);
    return response.data;
  }

  /**
   * Reindex a specific document by ID
   */
  static async reindexDocument(docId: string): Promise<ReindexResponse> {
    const response = await api.post<ReindexResponse>(`/admin/documents/${docId}/reindex`);
    return response.data;
  }

  /**
   * Get index statistics
   */
  static async getIndexStats(): Promise<IndexStatsResponse> {
    const response = await api.get<IndexStatsResponse>('/admin/stats');
    return response.data;
  }

  /**
   * Clear all documents and reindex
   */
  static async clearAndReindex(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/admin/clear');
    return response.data;
  }

  /**
   * Reindex all documents
   */
  static async reindexDocuments(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/admin/reindex');
    return response.data;
  }

  /**
   * Clear the index
   */
  static async clearIndex(): Promise<{ success: boolean; message: string }> {
    const response = await api.delete('/admin/index');
    return response.data;
  }

  /**
   * Health check
   */
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/health');
    return response.data;
  }
}

// Utility function to handle API errors
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError;
    if (apiError?.detail) {
      return apiError.detail;
    }
    if (apiError?.message) {
      return apiError.message;
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// File validation utilities
export const validateFiles = (files: File[]): { valid: File[]; invalid: { file: File; reason: string }[] } => {
  const valid: File[] = [];
  const invalid: { file: File; reason: string }[] = [];

  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
  ];

  const maxSize = 50 * 1024 * 1024; // 50MB

  files.forEach((file) => {
    if (!allowedTypes.includes(file.type)) {
      invalid.push({
        file,
        reason: 'File type not supported. Please upload PDF, DOCX, DOC, or TXT files.',
      });
    } else if (file.size > maxSize) {
      invalid.push({
        file,
        reason: 'File size too large. Maximum size is 50MB.',
      });
    } else {
      valid.push(file);
    }
  });

  return { valid, invalid };
};

export default AdminApiService;
