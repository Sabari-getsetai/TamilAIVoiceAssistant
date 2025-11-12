/**
 * Organization API Service
 *
 * Handles all organization-related API calls
 */

import { authApi } from './authApi';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  OrganizationMember,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  OrganizationLimits
} from '../../types/organization';

const BASE_URL = '/auth/organizations';

export class OrganizationApiService {
  /**
   * Get all organizations for the current user (backend: GET /auth/organizations/my)
   */
  static async getUserOrganizations(): Promise<Organization[]> {
    const response = await authApi.get<Organization[]>(`${BASE_URL}/my`);
    return response.data;
  }

  /**
   * Get current organization details (backend: GET /auth/organizations/current)
   */
  static async getCurrentOrganization(): Promise<Organization> {
    const response = await authApi.get<Organization>(`${BASE_URL}/current`);
    return response.data;
  }

  /**
   * Create a new organization (backend: POST /auth/organizations)
   */
  static async createOrganization(data: CreateOrganizationRequest): Promise<Organization> {
    const response = await authApi.post<Organization>(BASE_URL, data);
    return response.data;
  }

  /**
   * Set active organization (backend: PUT /auth/organizations/set-active)
   */
  static async setActiveOrganization(organization_id: string): Promise<{ message: string }> {
    const response = await authApi.put<{ message: string }>(`${BASE_URL}/set-active`, {
      organization_id
    });
    return response.data;
  }

  /**
   * Get auth status including organization info (backend: GET /auth/auth-status)
   */
  static async getAuthStatus(): Promise<{
    authenticated: boolean;
    has_organization: boolean;
    has_active_organization: boolean;
    user: any;
    organization: Organization | null;
  }> {
    const response = await authApi.get('/auth/auth-status');
    return response.data;
  }

  /**
   * Get organization members (backend: GET /organizations/{orgId}/members)
   */
  static async getOrganizationMembers(orgId: string): Promise<OrganizationMember[]> {
    const response = await authApi.get<OrganizationMember[]>(`/organizations/${orgId}/members`);
    return response.data;
  }

  /**
   * Invite a member to the organization (backend: POST /organizations/{orgId}/members/invite)
   */
  static async inviteMember(orgId: string, request: InviteMemberRequest): Promise<{ message: string; member_id: string; user_email: string; role: string }> {
    const response = await authApi.post(`/organizations/${orgId}/members/invite`, request);
    return response.data;
  }

  /**
   * Update member role (backend: PUT /organizations/{orgId}/members/{memberId}/role)
   */
  static async updateMemberRole(
    orgId: string,
    memberId: string,
    request: UpdateMemberRoleRequest
  ): Promise<{ message: string; member_id: string; user_email: string; old_role: string; new_role: string }> {
    const response = await authApi.put(`/organizations/${orgId}/members/${memberId}/role`, request);
    return response.data;
  }

  /**
   * Remove member from organization (backend: DELETE /organizations/{orgId}/members/{memberId})
   */
  static async removeMember(orgId: string, memberId: string): Promise<void> {
    await authApi.delete(`/organizations/${orgId}/members/${memberId}`);
  }

  /**
   * Update organization details (backend: PUT /organizations/{orgId})
   */
  static async updateOrganization(orgId: string, data: UpdateOrganizationRequest): Promise<Organization> {
    const response = await authApi.put<Organization>(`/organizations/${orgId}`, data);
    return response.data;
  }

  /**
   * Delete organization (backend: DELETE /organizations/{orgId})
   */
  static async deleteOrganization(orgId: string): Promise<void> {
    await authApi.delete(`/organizations/${orgId}`);
  }

  /**
   * Get user's organization limits (backend: GET /organizations/limits)
   */
  static async getOrganizationLimits(): Promise<OrganizationLimits> {
    const response = await authApi.get<OrganizationLimits>('/organizations/limits');
    return response.data;
  }
}

// Export individual functions for convenience
export const {
  getUserOrganizations,
  getCurrentOrganization,
  createOrganization,
  setActiveOrganization,
  getAuthStatus,
  getOrganizationMembers,
  inviteMember,
  updateMemberRole,
  removeMember,
  updateOrganization,
  deleteOrganization,
  getOrganizationLimits,
} = OrganizationApiService;

// Create a default export object that matches our context needs
export const organizationApi = {
  getUserOrganizations: OrganizationApiService.getUserOrganizations,
  getCurrentOrganization: OrganizationApiService.getCurrentOrganization,
  createOrganization: OrganizationApiService.createOrganization,
  setActiveOrganization: OrganizationApiService.setActiveOrganization,
  getAuthStatus: OrganizationApiService.getAuthStatus,
  getOrganizationMembers: OrganizationApiService.getOrganizationMembers,
  inviteMember: OrganizationApiService.inviteMember,
  updateMemberRole: OrganizationApiService.updateMemberRole,
  removeMember: OrganizationApiService.removeMember,
  updateOrganization: OrganizationApiService.updateOrganization,
  deleteOrganization: OrganizationApiService.deleteOrganization,
  getOrganizationLimits: OrganizationApiService.getOrganizationLimits,
};
