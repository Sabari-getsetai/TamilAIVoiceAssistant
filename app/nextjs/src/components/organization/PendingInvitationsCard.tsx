'use client';

import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Snackbar,
  Box,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
  Copy as CopyIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import { OrganizationRole } from '@/types/organization';

interface PendingInvitation {
  id: string;
  invited_email: string;
  role: OrganizationRole;
  invited_by: string;
  inviter_name?: string;
  token: string;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
}

interface PendingInvitationsCardProps {
  organizationId: string;
  userRole?: string;
  onRefresh?: () => void;
}

export default function PendingInvitationsCard({ organizationId, userRole, onRefresh }: PendingInvitationsCardProps) {
  const [invitations, setInvitations] = React.useState<PendingInvitation[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [resendDialogOpen, setResendDialogOpen] = React.useState(false);
  const [selectedInvitation, setSelectedInvitation] = React.useState<PendingInvitation | null>(null);
  const [snackbar, setSnackbar] = React.useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const canManageInvitations = userRole === 'owner' || userRole === 'ORG_ADMIN' || userRole === 'admin';

  const loadInvitations = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await organizationApi.getPendingInvitations(organizationId);
      // setInvitations(response);

      // Mock data for demonstration
      const mockInvitations: PendingInvitation[] = [
        {
          id: '1',
          invited_email: 'john.doe@example.com',
          role: 'member',
          invited_by: 'user-1',
          inviter_name: 'Admin User',
          token: 'abc123',
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
          expires_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
          is_expired: false
        },
        {
          id: '2',
          invited_email: 'jane.smith@example.com',
          role: 'ORG_ADMIN',
          invited_by: 'user-1',
          inviter_name: 'Admin User',
          token: 'def456',
          created_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(), // 8 days ago
          expires_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago (expired)
          is_expired: true
        }
      ];
      setInvitations(mockInvitations);
    } catch (error: any) {
      console.error('Error loading invitations:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load pending invitations',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    if (organizationId) {
      loadInvitations();
    }
  }, [organizationId]);

  const handleDeleteInvitation = async () => {
    if (!selectedInvitation) return;

    try {
      // TODO: Replace with actual API call
      // await organizationApi.deleteInvitation(selectedInvitation.id);

      setInvitations(prev => prev.filter(inv => inv.id !== selectedInvitation.id));
      setSnackbar({
        open: true,
        message: 'Invitation cancelled successfully',
        severity: 'success'
      });
      setDeleteDialogOpen(false);
      setSelectedInvitation(null);
      onRefresh?.();
    } catch (error: any) {
      console.error('Error deleting invitation:', error);
      setSnackbar({
        open: true,
        message: 'Failed to cancel invitation',
        severity: 'error'
      });
    }
  };

  const handleResendInvitation = async () => {
    if (!selectedInvitation) return;

    try {
      // TODO: Replace with actual API call
      // await organizationApi.resendInvitation(selectedInvitation.id);

      setSnackbar({
        open: true,
        message: 'Invitation resent successfully',
        severity: 'success'
      });
      setResendDialogOpen(false);
      setSelectedInvitation(null);
    } catch (error: any) {
      console.error('Error resending invitation:', error);
      setSnackbar({
        open: true,
        message: 'Failed to resend invitation',
        severity: 'error'
      });
    }
  };

  const handleCopyInviteLink = async (token: string) => {
    const inviteLink = `${window.location.origin}/auth/accept-invitation?token=${token}`;

    try {
      await navigator.clipboard.writeText(inviteLink);
      setSnackbar({
        open: true,
        message: 'Invitation link copied to clipboard',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      setSnackbar({
        open: true,
        message: 'Failed to copy invitation link',
        severity: 'error'
      });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getDaysRemaining = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffTime = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'owner':
        return 'error';
      case 'org_admin':
        return 'warning';
      case 'member':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    if (role === 'ORG_ADMIN') return 'Org Admin';
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  if (!canManageInvitations) {
    return null;
  }

  return (
    <>
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <EmailIcon sx={{ mr: 1 }} />
                Pending Invitations
                {invitations.length > 0 && (
                  <Chip
                    label={invitations.length}
                    size="small"
                    color="primary"
                    sx={{ ml: 2 }}
                  />
                )}
              </Typography>
              <Tooltip title="Refresh invitations">
                <IconButton onClick={loadInvitations} disabled={isLoading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        <CardContent>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : invitations.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No pending invitations
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Email</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Invited By</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Expires</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invitations.map((invitation) => (
                    <TableRow key={invitation.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {invitation.invited_email}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getRoleLabel(invitation.role)}
                          color={getRoleColor(invitation.role) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {invitation.inviter_name || invitation.invited_by}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {invitation.is_expired ? (
                          <Chip label="Expired" color="error" size="small" />
                        ) : (
                          <Chip
                            label={`${getDaysRemaining(invitation.expires_at)} days left`}
                            color={getDaysRemaining(invitation.expires_at) <= 1 ? 'warning' : 'success'}
                            size="small"
                            icon={<ScheduleIcon />}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(invitation.expires_at)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Copy invitation link">
                            <IconButton
                              size="small"
                              onClick={() => handleCopyInviteLink(invitation.token)}
                              disabled={invitation.is_expired}
                            >
                              <CopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Resend invitation">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedInvitation(invitation);
                                setResendDialogOpen(true);
                              }}
                            >
                              <SendIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Cancel invitation">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedInvitation(invitation);
                                setDeleteDialogOpen(true);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Cancel Invitation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel the invitation for{' '}
            <strong>{selectedInvitation?.invited_email}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone. The user will no longer be able to accept this invitation.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleDeleteInvitation} color="error" variant="contained">
            Cancel Invitation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Resend Confirmation Dialog */}
      <Dialog open={resendDialogOpen} onClose={() => setResendDialogOpen(false)}>
        <DialogTitle>Resend Invitation</DialogTitle>
        <DialogContent>
          <Typography>
            Send a new invitation email to{' '}
            <strong>{selectedInvitation?.invited_email}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will generate a new invitation token and extend the expiry date.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResendDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleResendInvitation} variant="contained">
            Resend Invitation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}