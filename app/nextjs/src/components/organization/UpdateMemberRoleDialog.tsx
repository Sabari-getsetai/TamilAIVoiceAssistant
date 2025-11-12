/**
 * UpdateMemberRoleDialog Component
 *
 * Dialog for updating member roles with ORG_ADMIN restrictions and role change validation
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Avatar,
  Alert,
  CircularProgress,
  Chip,
  FormHelperText
} from '@mui/material';
import {
  Edit as EditIcon,
  TrendingUp as PromoteIcon,
  TrendingDown as DemoteIcon,
  Person as PersonIcon
} from '@mui/icons-material';

import { OrganizationMember, OrganizationRole, UpdateMemberRoleRequest } from '@/types/organization';
import { useOrganization } from '@/contexts/OrganizationContext';
import { organizationApi } from '@/services/api/organizationApi';
import {
  canChangeRole,
  getRoleDisplayName,
  getRoleBadgeColor,
  getRoleHierarchyLevel
} from '@/utils/permissions';

interface UpdateMemberRoleDialogProps {
  open: boolean;
  member: OrganizationMember | null;
  onClose: () => void;
  onSuccess: () => void;
}

const getInitials = (name?: string, username?: string): string => {
  const displayName = name || username || '';
  const parts = displayName.split(' ');
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return displayName.substring(0, 2).toUpperCase();
};

const UpdateMemberRoleDialog: React.FC<UpdateMemberRoleDialogProps> = ({
  open,
  member,
  onClose,
  onSuccess
}) => {
  const [newRole, setNewRole] = useState<OrganizationRole>('member');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { currentOrganization } = useOrganization();
  const userRole = currentOrganization?.user_role;

  // Reset form when member changes
  useEffect(() => {
    if (member) {
      setNewRole(member.role);
      setError(null);
    }
  }, [member]);

  // Get available roles based on user's permissions and target member
  const getAvailableRoles = (): OrganizationRole[] => {
    if (!member) return [];

    const allRoles: OrganizationRole[] = ['member', 'ORG_ADMIN', 'admin', 'owner'];
    return allRoles.filter(targetRole =>
      canChangeRole(userRole, member.role, targetRole, member.user_id, 'current_user_id')
    );
  };

  const availableRoles = getAvailableRoles();

  const getRoleDescription = (role: OrganizationRole): string => {
    switch (role) {
      case 'owner':
        return 'Full access to all organization features and settings. Can manage billing and delete organization.';
      case 'ORG_ADMIN':
        return 'Can manage members and organization settings. Cannot promote to owner or manage billing.';
      case 'admin':
        return 'Administrative access with full system permissions.';
      case 'member':
        return 'Basic access to organization features. Can view content and participate in discussions.';
      default:
        return '';
    }
  };

  const getChangeType = (): 'promote' | 'demote' | 'same' => {
    if (!member) return 'same';

    const currentLevel = getRoleHierarchyLevel(member.role);
    const newLevel = getRoleHierarchyLevel(newRole);

    if (newLevel > currentLevel) return 'promote';
    if (newLevel < currentLevel) return 'demote';
    return 'same';
  };

  const getChangeIcon = () => {
    const changeType = getChangeType();
    switch (changeType) {
      case 'promote':
        return <PromoteIcon color="success" />;
      case 'demote':
        return <DemoteIcon color="warning" />;
      default:
        return <EditIcon color="primary" />;
    }
  };

  const getChangeMessage = (): string => {
    const changeType = getChangeType();
    const currentRoleName = getRoleDisplayName(member?.role || 'member');
    const newRoleName = getRoleDisplayName(newRole);

    switch (changeType) {
      case 'promote':
        return `This will promote ${member?.full_name || member?.username} from ${currentRoleName} to ${newRoleName}.`;
      case 'demote':
        return `This will demote ${member?.full_name || member?.username} from ${currentRoleName} to ${newRoleName}.`;
      case 'same':
        return `${member?.full_name || member?.username} will remain a ${currentRoleName}.`;
      default:
        return '';
    }
  };

  const handleConfirm = async () => {
    if (!member || !currentOrganization?.id) return;

    // Check if role actually changed
    if (newRole === member.role) {
      setError('Please select a different role to update');
      return;
    }

    // Validate permission
    if (!canChangeRole(userRole, member.role, newRole, member.user_id, 'current_user_id')) {
      setError('You do not have permission to change this member\'s role');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: UpdateMemberRoleRequest = {
        role: newRole
      };

      await organizationApi.updateMemberRole(
        currentOrganization.id,
        member.id,
        request
      );

      // Success
      handleClose();
      onSuccess();
    } catch (err: any) {
      console.error('Failed to update member role:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to update member role';

      // Handle specific errors
      if (errorMessage.includes('Cannot change own role')) {
        setError('You cannot change your own role');
      } else if (errorMessage.includes('permission')) {
        setError('You do not have permission to change this member\'s role');
      } else if (errorMessage.includes('ORG_ADMIN cannot manage owner')) {
        setError('Organization admins cannot promote users to owner or demote owners');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  if (!member) return null;

  const changeType = getChangeType();
  const isRoleChanged = newRole !== member.role;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2
        }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EditIcon color="primary" />
          <Typography variant="h6">
            Update Member Role
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Change the role and permissions for this team member
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Member Info */}
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          p: 2,
          bgcolor: 'grey.50',
          borderRadius: 1,
          mb: 3
        }}>
          <Avatar
            sx={{
              width: 50,
              height: 50,
              bgcolor: 'primary.main',
              fontSize: '1rem'
            }}
          >
            {getInitials(member.full_name, member.username)}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {member.full_name || member.username}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {member.email}
            </Typography>
            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Current role:
              </Typography>
              <Chip
                label={getRoleDisplayName(member.role)}
                color={getRoleBadgeColor(member.role)}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>

        {/* Role Selection */}
        <FormControl fullWidth required disabled={loading}>
          <InputLabel>New Role</InputLabel>
          <Select
            value={newRole}
            label="New Role"
            onChange={(e) => setNewRole(e.target.value as OrganizationRole)}
          >
            {availableRoles.map((roleOption) => (
              <MenuItem key={roleOption} value={roleOption}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  <Chip
                    label={getRoleDisplayName(roleOption)}
                    color={getRoleBadgeColor(roleOption)}
                    size="small"
                    variant={roleOption === member.role ? 'filled' : 'outlined'}
                  />
                  {roleOption === member.role && (
                    <Typography variant="caption" color="text.secondary">
                      (current)
                    </Typography>
                  )}
                </Box>
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>
            {getRoleDescription(newRole)}
          </FormHelperText>
        </FormControl>

        {/* Permission Notice */}
        {userRole === 'ORG_ADMIN' && (
          <Alert severity="info" sx={{ mt: 2 }}>
            As an Organization Admin, you cannot promote users to owner or demote existing owners.
          </Alert>
        )}

        {/* Change Preview */}
        {isRoleChanged && (
          <Box sx={{
            mt: 3,
            p: 2,
            bgcolor: changeType === 'promote' ? 'success.50' : changeType === 'demote' ? 'warning.50' : 'info.50',
            borderRadius: 1,
            border: '1px solid',
            borderColor: changeType === 'promote' ? 'success.200' : changeType === 'demote' ? 'warning.200' : 'info.200'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {getChangeIcon()}
              <Typography variant="subtitle2" sx={{
                color: changeType === 'promote' ? 'success.main' : changeType === 'demote' ? 'warning.main' : 'info.main'
              }}>
                Role Change Preview
              </Typography>
            </Box>
            <Typography variant="body2">
              {getChangeMessage()}
            </Typography>
          </Box>
        )}

        {/* Role Change Impact */}
        {isRoleChanged && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Permission Changes:
            </Typography>
            <Box component="ul" sx={{ m: 0, pl: 2 }}>
              {newRole === 'owner' && (
                <>
                  <li>
                    <Typography variant="body2" color="success.main">
                      ✓ Full administrative access
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" color="success.main">
                      ✓ Billing and subscription management
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" color="success.main">
                      ✓ Organization deletion capabilities
                    </Typography>
                  </li>
                </>
              )}
              {newRole === 'ORG_ADMIN' && (
                <>
                  <li>
                    <Typography variant="body2" color="success.main">
                      ✓ Member management permissions
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" color="success.main">
                      ✓ Organization settings access
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" color="warning.main">
                      ⚠ Cannot manage owner roles
                    </Typography>
                  </li>
                </>
              )}
              {newRole === 'member' && member.role !== 'member' && (
                <>
                  <li>
                    <Typography variant="body2" color="error.main">
                      ✗ Loss of administrative privileges
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" color="error.main">
                      ✗ Cannot manage other members
                    </Typography>
                  </li>
                </>
              )}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          color="inherit"
        >
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          disabled={loading || !isRoleChanged}
          variant="contained"
          color={changeType === 'demote' ? 'warning' : 'primary'}
          startIcon={
            loading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              getChangeIcon()
            )
          }
        >
          {loading ? 'Updating...' : `Update Role`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UpdateMemberRoleDialog;