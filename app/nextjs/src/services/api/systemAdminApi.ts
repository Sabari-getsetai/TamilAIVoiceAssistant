/**
 * System Admin API Service
 *
 * Handles all API calls for the new /api/admin/* endpoints
 * For system-wide administration (ADMIN + SUPERADMIN roles only)
 */

import { api } from './index';

// Types for System Admin API
export interface SystemDocument {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  upload_date: string;
  processed_date: string | null;
  user_id: string;
  organization_id: string;
}

export interface SystemUser {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  subscription_tier: string;
  created_at: string;
  last_login: string | null;
}

export interface SystemOrganization {
  id: string;
  name: string;
  description: string | null;
  size: string;
  tier_type: string;
  subscription_plan: string;
  subscription_status: string;
  is_active: boolean;
  created_at: string;
  creator_id: string;
}

export interface SystemDocumentStats {
  total_documents: number;
  total_chunks: number;
  documents_by_status: Record<string, number>;
  last_updated: string | null;
  additional_info?: Record<string, any>;
}

export interface SystemInfo {
  system_statistics: {
    total_users: number;
    active_users: number;
    total_organizations: number;
    active_organizations: number;
    total_documents: number;
  };
  admin_info: {
    admin_user_id: string;
    admin_email: string;
    admin_role: string;
  };
  timestamp: string;
}

// System Admin Document Management API
export const systemDocumentsApi = {
  // Get all documents across all organizations
  getAllDocuments: async (skip = 0, limit = 100): Promise<SystemDocument[]> => {
    const response = await api.get<SystemDocument[]>('/api/admin/documents', {
      params: { skip, limit }
    });
    return response.data;
  },

  // Get specific document (any organization)
  getDocument: async (documentId: string): Promise<SystemDocument> => {
    const response = await api.get<SystemDocument>(`/api/admin/documents/${documentId}`);
    return response.data;
  },

  // Delete any document (system admin privilege)
  deleteDocument: async (documentId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/api/admin/documents/${documentId}`);
    return response.data;
  },

  // Get system-wide document statistics
  getStats: async (): Promise<SystemDocumentStats> => {
    const response = await api.get<SystemDocumentStats>('/api/admin/stats');
    return response.data;
  },
};

// System Admin User Management API
export const systemUsersApi = {
  // Get all users in the system
  getAllUsers: async (skip = 0, limit = 100): Promise<SystemUser[]> => {
    const response = await api.get<SystemUser[]>('/api/admin/users', {
      params: { skip, limit }
    });
    return response.data;
  },

  // Get specific user details
  getUser: async (userId: string): Promise<SystemUser> => {
    const response = await api.get<SystemUser>(`/api/admin/users/${userId}`);
    return response.data;
  },

  // Update user (system admin operation)
  updateUser: async (userId: string, updates: Partial<SystemUser>): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>(`/api/admin/users/${userId}`, updates);
    return response.data;
  },

  // Deactivate/activate user
  setUserActiveStatus: async (userId: string, isActive: boolean): Promise<{ message: string }> => {
    const response = await api.patch<{ message: string }>(`/api/admin/users/${userId}/status`, {
      is_active: isActive
    });
    return response.data;
  },
};

// System Admin Organization Management API
export const systemOrganizationsApi = {
  // Get all organizations in the system
  getAllOrganizations: async (skip = 0, limit = 100): Promise<SystemOrganization[]> => {
    const response = await api.get<SystemOrganization[]>('/api/admin/organizations', {
      params: { skip, limit }
    });
    return response.data;
  },

  // Get specific organization details
  getOrganization: async (organizationId: string): Promise<SystemOrganization> => {
    const response = await api.get<SystemOrganization>(`/api/admin/organizations/${organizationId}`);
    return response.data;
  },

  // Update organization (system admin operation)
  updateOrganization: async (organizationId: string, updates: Partial<SystemOrganization>): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>(`/api/admin/organizations/${organizationId}`, updates);
    return response.data;
  },

  // Set organization active status
  setOrganizationActiveStatus: async (organizationId: string, isActive: boolean): Promise<{ message: string }> => {
    const response = await api.patch<{ message: string }>(`/api/admin/organizations/${organizationId}/status`, {
      is_active: isActive
    });
    return response.data;
  },
};

// System Admin Info and Analytics API
export const systemInfoApi = {
  // Get comprehensive system information
  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await api.get<SystemInfo>('/api/admin/system-info');
    return response.data;
  },

  // Get platform analytics
  getAnalytics: async (timeRange = '30d'): Promise<any> => {
    const response = await api.get('/api/admin/analytics', {
      params: { time_range: timeRange }
    });
    return response.data;
  },

  // Get system health metrics
  getHealthMetrics: async (): Promise<any> => {
    const response = await api.get('/api/admin/health-metrics');
    return response.data;
  },
};

// Combined system admin API
export const systemAdminApi = {
  documents: systemDocumentsApi,
  users: systemUsersApi,
  organizations: systemOrganizationsApi,
  info: systemInfoApi,
};

export default systemAdminApi;