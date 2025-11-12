/**
 * Permission utility functions for organization management
 */

import { OrganizationRole } from '@/types/organization';

export const canManageMembers = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'ORG_ADMIN' || userRole === 'admin';
};

export const canRemoveMember = (
  userRole: string | undefined,
  targetRole: string,
  targetUserId: string,
  currentUserId: string
): boolean => {
  // Cannot remove yourself
  if (targetUserId === currentUserId) return false;

  // System admin can remove anyone
  if (userRole === 'admin') return true;

  // Owner can remove anyone except other owners
  if (userRole === 'owner') return targetRole !== 'owner';

  // ORG_ADMIN cannot remove owners or other ORG_ADMINs
  if (userRole === 'ORG_ADMIN') {
    return targetRole !== 'owner' && targetRole !== 'ORG_ADMIN';
  }

  return false;
};

export const canChangeRole = (
  userRole: string | undefined,
  currentRole: string,
  newRole: string,
  targetUserId: string,
  currentUserId: string
): boolean => {
  // Cannot change your own role
  if (targetUserId === currentUserId) return false;

  // System admin has full control
  if (userRole === 'admin') return true;

  // Owner has full control except for other owners
  if (userRole === 'owner') {
    return currentRole !== 'owner';
  }

  // ORG_ADMIN cannot manage owner roles or promote to owner
  if (userRole === 'ORG_ADMIN') {
    return (
      currentRole !== 'owner' &&
      newRole !== 'owner' &&
      currentRole !== 'ORG_ADMIN' &&
      newRole !== 'ORG_ADMIN'
    );
  }

  return false;
};

export const canInviteMembers = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'ORG_ADMIN' || userRole === 'admin';
};

export const canInviteToRole = (
  userRole: string | undefined,
  targetRole: OrganizationRole
): boolean => {
  // System admin can invite to any role
  if (userRole === 'admin') return true;

  // Owner can invite to any role
  if (userRole === 'owner') return true;

  // ORG_ADMIN cannot invite to owner or ORG_ADMIN roles
  if (userRole === 'ORG_ADMIN') {
    return targetRole === 'member';
  }

  return false;
};

export const canViewSettings = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'ORG_ADMIN' || userRole === 'admin';
};

export const canViewBilling = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'admin';
};

export const canDeleteOrganization = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'admin';
};

export const canTransferOwnership = (userRole?: string): boolean => {
  return userRole === 'owner' || userRole === 'admin';
};

export const getRoleBadgeColor = (role: string): 'error' | 'warning' | 'info' | 'success' => {
  switch (role) {
    case 'owner':
      return 'error';
    case 'ORG_ADMIN':
      return 'warning';
    case 'admin':
      return 'info';
    case 'member':
    default:
      return 'success';
  }
};

export const getRoleDisplayName = (role: string): string => {
  switch (role) {
    case 'owner':
      return 'Owner';
    case 'ORG_ADMIN':
      return 'Org Admin';
    case 'admin':
      return 'Admin';
    case 'member':
      return 'Member';
    default:
      return role;
  }
};

export const getRoleHierarchyLevel = (role: string): number => {
  switch (role) {
    case 'member':
      return 0;
    case 'ORG_ADMIN':
      return 1;
    case 'admin':
      return 2;
    case 'owner':
      return 3;
    default:
      return 0;
  }
};

export const canAccessMemberActions = (
  userRole: string | undefined,
  targetRole: string,
  targetUserId: string,
  currentUserId: string
): boolean => {
  return canRemoveMember(userRole, targetRole, targetUserId, currentUserId) ||
         canChangeRole(userRole, targetRole, 'member', targetUserId, currentUserId);
};