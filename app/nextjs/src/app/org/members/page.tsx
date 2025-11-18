'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import {
  useOrgMembers,
  useInviteOrgMember,
  useChangeOrgMemberRole,
  useRemoveOrgMember,
} from '@/hooks/useOrgDashboard';
import type { OrgMember } from '@/services/api/orgDashboardApi';

export default function OrgMembers() {
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedMember, setSelectedMember] = useState<OrgMember | null>(null);

  // Use the new API hooks
  const {
    data: members = [],
    isLoading,
    isError,
    error
  } = useOrgMembers();

  // Invite mutation
  const inviteMutation = useInviteOrgMember();

  // Change role mutation
  const changeRoleMutation = useChangeOrgMemberRole();

  // Remove member mutation
  const removeMutation = useRemoveOrgMember();

  const handleInvite = () => {
    if (inviteEmail) {
      inviteMutation.mutate({ email: inviteEmail, role: inviteRole }, {
        onSuccess: () => {
          setInviteDialogOpen(false);
          setInviteEmail('');
          setInviteRole('MEMBER');
        }
      });
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, member: OrgMember) => {
    setMenuAnchor(event.currentTarget);
    setSelectedMember(member);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedMember(null);
  };

  const handleChangeRole = (newRole: string) => {
    if (selectedMember) {
      changeRoleMutation.mutate({ memberId: selectedMember.id, newRole }, {
        onSuccess: () => {
          setMenuAnchor(null);
          setSelectedMember(null);
        }
      });
    }
  };

  const handleRemoveMember = () => {
    if (selectedMember && confirm('Are you sure you want to remove this member?')) {
      removeMutation.mutate(selectedMember.id, {
        onSuccess: () => {
          setMenuAnchor(null);
          setSelectedMember(null);
        }
      });
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'OWNER': return <BusinessIcon />;
      case 'ORG_ADMIN': return <AdminIcon />;
      case 'MEMBER': return <PersonIcon />;
      default: return <PersonIcon />;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'OWNER': return 'error';
      case 'ORG_ADMIN': return 'warning';
      case 'MEMBER': return 'primary';
      default: return 'default';
    }
  };

  const getRoleDescription = (role: string) => {
    switch (role) {
      case 'OWNER': return 'Full organization control';
      case 'ORG_ADMIN': return 'Can invite members and manage documents';
      case 'MEMBER': return 'Can view and upload documents';
      default: return 'Unknown role';
    }
  };

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading members: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            Organization Members
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your team members and their roles
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => setInviteDialogOpen(true)}
        >
          Invite Member
        </Button>
      </Box>

      {/* Role Information */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Role Permissions
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <BusinessIcon sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="subtitle1" fontWeight="bold">OWNER</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              • Full organization control<br />
              • Can invite members<br />
              • Can change member roles<br />
              • Can manage documents<br />
              • Can view organization audit trail
            </Typography>
          </Box>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AdminIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="subtitle1" fontWeight="bold">ORG_ADMIN</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              • Can invite members<br />
              • Cannot change member roles<br />
              • Can manage documents<br />
              • Can view organization audit trail
            </Typography>
          </Box>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="subtitle1" fontWeight="bold">MEMBER</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              • Can view documents<br />
              • Can upload documents<br />
              • Can delete own documents<br />
              • Can edit/reindex documents
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Members Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Member</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Joined Date</TableCell>
              <TableCell>Invited By</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: 'center', py: 4 }}>
                  Loading members...
                </TableCell>
              </TableRow>
            ) : (
              members.map((member: OrgMember) => (
                <TableRow key={member.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getRoleIcon(member.role)}
                      <Box sx={{ ml: 2 }}>
                        <Typography variant="body2" fontWeight="medium">
                          {member.full_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          @{member.username}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{member.email}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={member.role}
                      color={getRoleColor(member.role) as any}
                      size="small"
                      sx={{ fontWeight: 'bold' }}
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(member.joined_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {member.invited_by ? (
                      <Typography variant="body2" color="text.secondary">
                        {members.find(m => m.user_id === member.invited_by)?.full_name || 'Unknown'}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Founder
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {member.role !== 'OWNER' && (
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, member)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Member Actions Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        {selectedMember && selectedMember.role !== 'ORG_ADMIN' && (
          <MenuItem onClick={() => handleChangeRole('ORG_ADMIN')}>
            <ListItemIcon>
              <AdminIcon />
            </ListItemIcon>
            <ListItemText>Promote to Admin</ListItemText>
          </MenuItem>
        )}
        {selectedMember && selectedMember.role === 'ORG_ADMIN' && (
          <MenuItem onClick={() => handleChangeRole('MEMBER')}>
            <ListItemIcon>
              <PersonIcon />
            </ListItemIcon>
            <ListItemText>Demote to Member</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={handleRemoveMember} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon color="error" />
          </ListItemIcon>
          <ListItemText>Remove Member</ListItemText>
        </MenuItem>
      </Menu>

      {/* Invite Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite New Member</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Email Address"
              type="email"
              fullWidth
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="user@company.com"
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                label="Role"
              >
                <MenuItem value="MEMBER">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PersonIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Box>
                      <Typography variant="body2">Member</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Can view and upload documents
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
                <MenuItem value="ORG_ADMIN">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AdminIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Box>
                      <Typography variant="body2">Organization Admin</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Can invite members and manage documents
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body2" color="text.secondary">
              An invitation email will be sent to this address.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleInvite}
            variant="contained"
            disabled={!inviteEmail || inviteMutation.isPending}
            startIcon={<EmailIcon />}
          >
            {inviteMutation.isPending ? 'Sending...' : 'Send Invitation'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}