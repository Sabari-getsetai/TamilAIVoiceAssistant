/**
 * Organization Members Management Page
 *
 * Complete interface for managing organization members with role-based access control
 */

'use client';

import React, { useState, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Breadcrumbs,
  Link,
  Alert,
  Snackbar
} from '@mui/material';
import { Home as HomeIcon, Business as BusinessIcon } from '@mui/icons-material';
import NextLink from 'next/link';

import ProtectedLayout from '@/components/layout/ProtectedLayout';
import MemberListTable from '@/components/organization/MemberListTable';
import InviteMemberDialog from '@/components/organization/InviteMemberDialog';
import RemoveMemberConfirmDialog from '@/components/organization/RemoveMemberConfirmDialog';
import UpdateMemberRoleDialog from '@/components/organization/UpdateMemberRoleDialog';
import PendingInvitationsCard from '@/components/organization/PendingInvitationsCard';

import { useOrganization } from '@/contexts/OrganizationContext';
import { OrganizationMember } from '@/types/organization';
import { canManageMembers } from '@/utils/permissions';

interface SnackbarState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'info' | 'warning';
}

const MembersPage: React.FC = () => {
  // Dialog states
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [updateRoleDialogOpen, setUpdateRoleDialogOpen] = useState(false);

  // Selected member for actions
  const [selectedMember, setSelectedMember] = useState<OrganizationMember | null>(null);

  // Snackbar for notifications
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Reference to the table component for refreshing
  const tableRef = useRef<{ refresh: () => void }>(null);

  const { currentOrganization, isLoading, error } = useOrganization();
  const userRole = currentOrganization?.user_role;
  const canManage = canManageMembers(userRole);

  // Debug logging for permission issues
  React.useEffect(() => {
    console.debug('[MembersPage] Permission check:', {
      currentOrganization: currentOrganization ? {
        id: currentOrganization.id,
        name: currentOrganization.name,
        user_role: currentOrganization.user_role,
        current_user_role: currentOrganization.current_user_role
      } : null,
      userRole,
      canManage,
      isLoading,
      error
    });
  }, [currentOrganization, userRole, canManage, isLoading, error]);

  // Handler for successful operations
  const handleSuccess = (message: string) => {
    setSnackbar({
      open: true,
      message,
      severity: 'success'
    });

    // Refresh the member list
    tableRef.current?.refresh();
  };

  // Handler for errors
  const handleError = (message: string) => {
    setSnackbar({
      open: true,
      message,
      severity: 'error'
    });
  };

  // Dialog handlers
  const handleInviteMember = () => {
    if (!canManage) {
      handleError('You do not have permission to invite members');
      return;
    }
    setInviteDialogOpen(true);
  };

  const handleUpdateMemberRole = (member: OrganizationMember) => {
    setSelectedMember(member);
    setUpdateRoleDialogOpen(true);
  };

  const handleRemoveMember = (member: OrganizationMember) => {
    setSelectedMember(member);
    setRemoveDialogOpen(true);
  };

  // Success handlers for dialogs
  const handleInviteSuccess = () => {
    handleSuccess('Member invitation sent successfully');
    setInviteDialogOpen(false);
  };

  const handleUpdateRoleSuccess = () => {
    handleSuccess('Member role updated successfully');
    setUpdateRoleDialogOpen(false);
    setSelectedMember(null);
  };

  const handleRemoveSuccess = () => {
    handleSuccess('Member removed successfully');
    setRemoveDialogOpen(false);
    setSelectedMember(null);
  };

  // Close handlers for dialogs
  const handleInviteClose = () => {
    setInviteDialogOpen(false);
  };

  const handleUpdateRoleClose = () => {
    setUpdateRoleDialogOpen(false);
    setSelectedMember(null);
  };

  const handleRemoveClose = () => {
    setRemoveDialogOpen(false);
    setSelectedMember(null);
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Loading state
  if (isLoading) {
    return (
      <ProtectedLayout requireOrganization>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Typography variant="h4">Loading...</Typography>
        </Container>
      </ProtectedLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <ProtectedLayout requireOrganization>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Alert severity="error">
            Error loading organization: {error}
          </Alert>
        </Container>
      </ProtectedLayout>
    );
  }

  // No organization state
  if (!currentOrganization) {
    return (
      <ProtectedLayout requireOrganization>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Alert severity="warning">
            No organization selected. Please create or select an organization first.
          </Alert>
        </Container>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout requireOrganization>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Breadcrumbs */}
        <Box sx={{ mb: 3 }}>
          <Breadcrumbs>
            <Link
              component={NextLink}
              href="/admin"
              color="inherit"
              sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
            >
              <HomeIcon fontSize="small" />
              Dashboard
            </Link>
            <Link
              component={NextLink}
              href="/admin/organizations"
              color="inherit"
              sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
            >
              <BusinessIcon fontSize="small" />
              Organizations
            </Link>
            <Typography color="text.primary">Members</Typography>
          </Breadcrumbs>
        </Box>

        {/* Page Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Team Members
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your organization's team members and their roles in <strong>{currentOrganization.name}</strong>
          </Typography>
        </Box>

        {/* Access Control Notice */}
        {!canManage && (
          <Alert severity="info" sx={{ mb: 3 }}>
            You have read-only access to the member list. Contact an organization admin or owner to manage members.
          </Alert>
        )}

        {/* Pending Invitations */}
        {canManage && (
          <Box sx={{ mb: 4 }}>
            <PendingInvitationsCard
              organizationId={currentOrganization.id}
              userRole={userRole}
              onRefresh={() => tableRef.current?.refresh()}
            />
          </Box>
        )}

        {/* Member List Table */}
        <MemberListTable
          ref={tableRef}
          onInviteMember={handleInviteMember}
          onUpdateMemberRole={handleUpdateMemberRole}
          onRemoveMember={handleRemoveMember}
        />

        {/* Dialogs */}
        <InviteMemberDialog
          open={inviteDialogOpen}
          onClose={handleInviteClose}
          onSuccess={handleInviteSuccess}
        />

        <UpdateMemberRoleDialog
          open={updateRoleDialogOpen}
          member={selectedMember}
          onClose={handleUpdateRoleClose}
          onSuccess={handleUpdateRoleSuccess}
        />

        <RemoveMemberConfirmDialog
          open={removeDialogOpen}
          member={selectedMember}
          onClose={handleRemoveClose}
          onSuccess={handleRemoveSuccess}
        />

        {/* Success/Error Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleSnackbarClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
        >
          <Alert
            onClose={handleSnackbarClose}
            severity={snackbar.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </ProtectedLayout>
  );
};

export default MembersPage;