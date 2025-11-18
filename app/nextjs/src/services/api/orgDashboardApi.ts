/**
 * Organization Dashboard API Service
 *
 * Handles all API calls for the new /api/org/* endpoints
 * This is separate from the existing organizationApi.ts which handles /auth/organizations/*
 */

import { api } from './index';

// Types for Organization Dashboard API
export interface OrgDocument {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  upload_date: string;
  processed_date: string | null;
  uploader: string;
}

export interface OrgMember {
  id: string;
  user_id: string;
  email: string;
  username: string;
  full_name: string;
  role: 'OWNER' | 'ORG_ADMIN' | 'MEMBER';
  joined_at: string;
  invited_by: string | null;
}

export interface OrganizationInfo {
  id: string;
  name: string;
  description: string | null;
  website: string | null;
  industry: string | null;
  size: string;
  timezone: string;
  tier_type: string;
  subscription_plan: string;
  subscription_status: string;
  created_at: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  documents: OrgDocument[];
  errors: Array<{
    filename: string;
    error: string;
  }>;
}

export interface ProcessingRequest {
  document_ids: string[];
  force_reprocess?: boolean;
}

export interface ProcessingResponse {
  success: boolean;
  message: string;
  session_id: string;
  processed_count: number;
  failed_count: number;
  details: Array<{
    status: string;
  }>;
}

export interface DocumentStats {
  total_documents: number;
  total_chunks: number;
  documents_by_status: Record<string, number>;
  last_updated: string | null;
  additional_info?: Record<string, any>;
}

export interface InviteMemberRequest {
  email: string;
  role: string;
}

export interface InviteMemberResponse {
  message: string;
  invitation_id: string;
}

export interface ChangeRoleRequest {
  memberId: string;
  newRole: string;
}

export interface OrganizationSettings {
  organization: OrganizationInfo;
  user_role: string | null;
}

export interface UpdateSettingsRequest {
  name?: string;
  description?: string;
  website?: string;
  industry?: string;
  timezone?: string;
}

// Organization Document Management API
export const orgDocumentsApi = {
  // Upload documents to organization
  uploadDocuments: async (files: FileList): Promise<UploadResponse> => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    const response = await api.post<UploadResponse>('/api/org/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Process uploaded documents
  processDocuments: async (request: ProcessingRequest): Promise<ProcessingResponse> => {
    const response = await api.post<ProcessingResponse>('/api/org/documents/process', request);
    return response.data;
  },

  // Get organization documents
  getDocuments: async (skip = 0, limit = 100): Promise<OrgDocument[]> => {
    const response = await api.get<OrgDocument[]>('/api/org/documents', {
      params: { skip, limit }
    });
    return response.data;
  },

  // Get specific document
  getDocument: async (documentId: string): Promise<OrgDocument> => {
    const response = await api.get<OrgDocument>(`/api/org/documents/${documentId}`);
    return response.data;
  },

  // Delete document
  deleteDocument: async (documentId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/api/org/documents/${documentId}`);
    return response.data;
  },

  // Reprocess document
  reprocessDocument: async (documentId: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(`/api/org/documents/${documentId}/reprocess`);
    return response.data;
  },

  // Get organization document statistics
  getStats: async (): Promise<DocumentStats> => {
    const response = await api.get<DocumentStats>('/api/org/stats');
    return response.data;
  },
};

// Organization Member Management API
export const orgMembersApi = {
  // Get organization members
  getMembers: async (): Promise<OrgMember[]> => {
    const response = await api.get<OrgMember[]>('/api/org/members');
    return response.data;
  },

  // Invite new member
  inviteMember: async (request: InviteMemberRequest): Promise<InviteMemberResponse> => {
    const response = await api.post<InviteMemberResponse>('/api/org/members/invite', null, {
      params: request
    });
    return response.data;
  },

  // Change member role
  changeMemberRole: async (request: ChangeRoleRequest): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(
      `/api/org/members/${request.memberId}/change-role`,
      null,
      {
        params: { new_role: request.newRole }
      }
    );
    return response.data;
  },

  // Remove member
  removeMember: async (memberId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/api/org/members/${memberId}`);
    return response.data;
  },
};

// Organization Settings API
export const orgSettingsApi = {
  // Get organization settings
  getSettings: async (): Promise<OrganizationSettings> => {
    const response = await api.get<OrganizationSettings>('/api/org/settings');
    return response.data;
  },

  // Update organization settings
  updateSettings: async (updates: UpdateSettingsRequest): Promise<{ message: string; updated_fields: string[] }> => {
    const response = await api.put<{ message: string; updated_fields: string[] }>(
      '/api/org/settings',
      null,
      { params: updates }
    );
    return response.data;
  },
};

// Combined organization dashboard API
export const orgDashboardApi = {
  documents: orgDocumentsApi,
  members: orgMembersApi,
  settings: orgSettingsApi,
};

export default orgDashboardApi;