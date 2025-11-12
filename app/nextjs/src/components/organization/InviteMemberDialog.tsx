/**
 * InviteMemberDialog Component
 *
 * Dialog for inviting new members to the organization with email validation and role selection
 */

'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  FormHelperText
} from '@mui/material';
import { Email as EmailIcon, PersonAdd as PersonAddIcon } from '@mui/icons-material';

import { OrganizationRole, InviteMemberRequest } from '@/types/organization';
import { useOrganization } from '@/contexts/OrganizationContext';
import { organizationApi } from '@/services/api/organizationApi';
import {
  canInviteToRole,
  getRoleDisplayName,
  getRoleBadgeColor
} from '@/utils/permissions';

interface InviteMemberDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const InviteMemberDialog: React.FC<InviteMemberDialogProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<OrganizationRole>('member');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  const { currentOrganization } = useOrganization();
  const userRole = currentOrganization?.user_role;

  // Get available roles based on user's permissions
  const getAvailableRoles = (): OrganizationRole[] => {
    const allRoles: OrganizationRole[] = ['member', 'ORG_ADMIN', 'admin', 'owner'];
    return allRoles.filter(targetRole => canInviteToRole(userRole, targetRole));
  };

  const availableRoles = getAvailableRoles();

  const handleEmailChange = (value: string) => {
    setEmail(value);
    setEmailError(null);
    setError(null);

    if (value && !validateEmail(value)) {
      setEmailError('Please enter a valid email address');
    }
  };

  const handleSubmit = async () => {
    // Validation
    if (!email.trim()) {
      setEmailError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    if (!canInviteToRole(userRole, role)) {
      setError('You do not have permission to invite users to this role');
      return;
    }

    if (!currentOrganization?.id) {
      setError('No organization selected');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: InviteMemberRequest = {
        email: email.trim(),
        role
      };

      await organizationApi.inviteMember(currentOrganization.id, request);

      // Success
      handleClose();
      onSuccess();
    } catch (err: any) {
      console.error('Failed to invite member:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to send invitation';

      // Handle specific errors
      if (errorMessage.includes('already a member')) {
        setError('This user is already a member of the organization');
      } else if (errorMessage.includes('not found')) {
        setError('User with this email address not found');
      } else if (errorMessage.includes('permission')) {
        setError('You do not have permission to invite users to this role');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setEmail('');
      setRole('member');
      setError(null);
      setEmailError(null);
      onClose();
    }
  };

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

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonAddIcon color="primary" />
          <Typography variant="h6">
            Invite Team Member
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Send an invitation to add a new member to {currentOrganization?.name}
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Email Input */}
          <TextField
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => handleEmailChange(e.target.value)}
            error={!!emailError}
            helperText={emailError}
            fullWidth
            required
            disabled={loading}
            placeholder="colleague@company.com"
            InputProps={{
              startAdornment: (
                <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
              ),
            }}
          />

          {/* Role Selection */}
          <FormControl fullWidth required disabled={loading}>
            <InputLabel>Role</InputLabel>
            <Select
              value={role}
              label="Role"
              onChange={(e) => setRole(e.target.value as OrganizationRole)}
            >
              {availableRoles.map((roleOption) => (
                <MenuItem key={roleOption} value={roleOption}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={getRoleDisplayName(roleOption)}
                      color={getRoleBadgeColor(roleOption)}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              {getRoleDescription(role)}
            </FormHelperText>
          </FormControl>

          {/* Permission Notice */}
          {userRole === 'ORG_ADMIN' && (
            <Alert severity="info" sx={{ mt: 1 }}>
              As an Organization Admin, you can only invite members. Contact the organization owner to invite admins.
            </Alert>
          )}

          {/* Preview */}
          <Box sx={{
            p: 2,
            bgcolor: 'grey.50',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'grey.200'
          }}>
            <Typography variant="subtitle2" gutterBottom>
              Invitation Preview
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {email || 'colleague@company.com'} will be invited to join {currentOrganization?.name} as a{' '}
              <Chip
                label={getRoleDisplayName(role)}
                color={getRoleBadgeColor(role)}
                size="small"
                variant="outlined"
              />
            </Typography>
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
          onClick={handleSubmit}
          disabled={loading || !email.trim() || !!emailError}
          variant="contained"
          startIcon={
            loading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              <PersonAddIcon />
            )
          }
        >
          {loading ? 'Sending Invitation...' : 'Send Invitation'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InviteMemberDialog;