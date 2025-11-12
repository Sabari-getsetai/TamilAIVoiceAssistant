/**
 * RemoveMemberConfirmDialog Component
 *
 * Confirmation dialog for removing members with safety checks
 */

'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Avatar,
  Alert,
  TextField,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  Warning as WarningIcon,
  PersonRemove as PersonRemoveIcon,
  Person as PersonIcon
} from '@mui/icons-material';

import { OrganizationMember } from '@/types/organization';
import { useOrganization } from '@/contexts/OrganizationContext';
import { organizationApi } from '@/services/api/organizationApi';
import { getRoleDisplayName, getRoleBadgeColor } from '@/utils/permissions';

interface RemoveMemberConfirmDialogProps {
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

const RemoveMemberConfirmDialog: React.FC<RemoveMemberConfirmDialogProps> = ({
  open,
  member,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmationText, setConfirmationText] = useState('');

  const { currentOrganization } = useOrganization();

  const isOwnerRemoval = member?.role === 'owner';
  const confirmationRequired = isOwnerRemoval;
  const expectedConfirmation = member?.email || '';

  const handleConfirm = async () => {
    if (!member || !currentOrganization?.id) return;

    // Validate confirmation for critical roles
    if (confirmationRequired && confirmationText !== expectedConfirmation) {
      setError('Please type the member\'s email address to confirm');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await organizationApi.removeMember(currentOrganization.id, member.id);

      // Success
      handleClose();
      onSuccess();
    } catch (err: any) {
      console.error('Failed to remove member:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to remove member';

      // Handle specific errors
      if (errorMessage.includes('Cannot remove yourself')) {
        setError('You cannot remove yourself from the organization');
      } else if (errorMessage.includes('last owner')) {
        setError('Cannot remove the last owner of the organization');
      } else if (errorMessage.includes('permission')) {
        setError('You do not have permission to remove this member');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setConfirmationText('');
      setError(null);
      onClose();
    }
  };

  if (!member) return null;

  const getWarningMessage = (): string => {
    if (member.role === 'owner') {
      return 'Removing an owner will revoke all administrative privileges. This action cannot be undone.';
    }
    if (member.role === 'ORG_ADMIN') {
      return 'Removing an organization admin will revoke their management privileges.';
    }
    return 'This member will lose access to the organization and all its resources.';
  };

  const getSeverity = (): 'warning' | 'error' => {
    return member.role === 'owner' ? 'error' : 'warning';
  };

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
          <WarningIcon color="error" />
          <Typography variant="h6">
            Remove Team Member
          </Typography>
        </Box>
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
            <Box sx={{ mt: 1 }}>
              <Chip
                label={getRoleDisplayName(member.role)}
                color={getRoleBadgeColor(member.role)}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>

        {/* Warning Message */}
        <Alert severity={getSeverity()} sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Are you sure you want to remove this member?</strong>
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {getWarningMessage()}
          </Typography>
        </Alert>

        {/* Additional Warnings */}
        {member.role === 'owner' && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Important:</strong> Make sure there is at least one other owner before removing this member to avoid losing organization access.
            </Typography>
          </Alert>
        )}

        {/* Confirmation Input for Critical Roles */}
        {confirmationRequired && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              To confirm removal of this {getRoleDisplayName(member.role).toLowerCase()}, please type their email address:
            </Typography>
            <TextField
              fullWidth
              size="small"
              placeholder={expectedConfirmation}
              value={confirmationText}
              onChange={(e) => setConfirmationText(e.target.value)}
              disabled={loading}
              error={confirmationRequired && confirmationText !== '' && confirmationText !== expectedConfirmation}
              helperText={
                confirmationRequired && confirmationText !== '' && confirmationText !== expectedConfirmation
                  ? 'Email address does not match'
                  : ''
              }
            />
          </Box>
        )}

        {/* Impact Summary */}
        <Box sx={{
          mt: 3,
          p: 2,
          bgcolor: 'error.50',
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'error.200'
        }}>
          <Typography variant="subtitle2" gutterBottom color="error.main">
            What happens when you remove this member:
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2, color: 'error.main' }}>
            <li>
              <Typography variant="body2">
                Immediate loss of access to {currentOrganization?.name}
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                Cannot view or access organization resources
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                Role-specific permissions will be revoked
              </Typography>
            </li>
            {member.role === 'owner' && (
              <li>
                <Typography variant="body2">
                  Loss of billing and administrative access
                </Typography>
              </li>
            )}
          </Box>
        </Box>
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
          disabled={
            loading ||
            (confirmationRequired && confirmationText !== expectedConfirmation)
          }
          variant="contained"
          color="error"
          startIcon={
            loading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              <PersonRemoveIcon />
            )
          }
        >
          {loading ? 'Removing...' : 'Remove Member'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RemoveMemberConfirmDialog;