/**
 * Organization-related TypeScript types and interfaces
 */

export type OrganizationSize = 'startup' | 'small' | 'medium' | 'large' | 'enterprise';

export type OrganizationRole = 'member' | 'ORG_ADMIN' | 'admin' | 'owner';

export interface Organization {
  id: string;
  name: string;
  description?: string;
  website?: string;
  industry?: string;
  size: OrganizationSize;
  timezone: string;
  creator_id?: string;
  is_active: boolean;
  settings?: Record<string, unknown>;
  billing_email?: string;
  subscription_plan: string;
  subscription_status: string;
  trial_ends_at?: string;
  created_at: string;
  updated_at?: string;
  member_count?: number;
  user_role?: OrganizationRole | 'admin'; // 'admin' for system admins
  current_user_role?: OrganizationRole | 'admin'; // Backend field name
}

export interface CreateOrganizationRequest {
  name: string;
  description?: string;
  website?: string;
  industry?: string;
  size: OrganizationSize;
  timezone: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
  website?: string;
  industry?: string;
  size?: OrganizationSize;
  timezone?: string;
  billing_email?: string;
  settings?: Record<string, unknown>;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  username: string;
  full_name?: string;
  email: string;
  role: OrganizationRole;
  joined_at: string;
}

export interface SwitchOrganizationRequest {
  organization_id: string;
}

export interface SwitchOrganizationResponse {
  message: string;
  organization_id: string;
}

export interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  error: string | null;
  hasOrganizations: boolean;
  needsOrganizationSetup: boolean;
  switchOrganization: (orgId: string) => Promise<void>;
  createOrganization: (data: CreateOrganizationRequest) => Promise<Organization>;
  updateOrganization?: (orgId: string, data: UpdateOrganizationRequest) => Promise<Organization>;
  deleteOrganization?: (orgId: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  clearError: () => void;
}

export interface InviteMemberRequest {
  email: string;
  role: OrganizationRole;
}

export interface UpdateMemberRoleRequest {
  role: OrganizationRole;
}

export interface RemoveMemberRequest {
  user_id: string;
}

export interface OrganizationLimits {
  subscription_tier: string;
  max_organizations_allowed: number;
  current_owned_organizations: number;
  total_memberships: number;
  can_create_more: boolean;
}

export interface OrganizationInvitation {
  id: string;
  organization_id: string;
  organization_name: string;
  email: string;
  role: OrganizationRole;
  invited_by: string;
  inviter_name: string;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  created_at: string;
  expires_at: string;
}
