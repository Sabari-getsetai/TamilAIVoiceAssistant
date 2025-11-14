/**
 * MemberListTable Component
 *
 * Displays organization members in a table with role-based actions
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Skeleton,
  Alert,
  Tooltip,
  TextField,
  InputAdornment,
  Button,
  CircularProgress
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  PersonAdd as PersonAddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon
} from '@mui/icons-material';

import { OrganizationMember } from '@/types/organization';
import { useOrganization } from '@/contexts/OrganizationContext';
import { useAuth } from '@/contexts/AuthContext';
import { organizationApi } from '@/services/api/organizationApi';
import {
  canAccessMemberActions,
  canRemoveMember,
  canChangeRole,
  canInviteMembers,
  getRoleBadgeColor,
  getRoleDisplayName
} from '@/utils/permissions';

interface MemberListTableProps {
  onInviteMember: () => void;
  onUpdateMemberRole: (member: OrganizationMember) => void;
  onRemoveMember: (member: OrganizationMember) => void;
}

interface MemberListTableRef {
  refresh: () => void;
}

interface ActionMenuProps {
  member: OrganizationMember;
  onUpdateRole: () => void;
  onRemove: () => void;
  userRole?: string;
  currentUserId?: string;
}

const ActionMenu: React.FC<ActionMenuProps> = ({
  member,
  onUpdateRole,
  onRemove,
  userRole,
  currentUserId
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleUpdateRole = () => {
    onUpdateRole();
    handleClose();
  };

  const handleRemove = () => {
    onRemove();
    handleClose();
  };

  const canRemove = canRemoveMember(userRole, member.role, member.user_id, currentUserId || '');
  const canUpdate = canChangeRole(userRole, member.role, 'member', member.user_id, currentUserId || '');

  // If no actions available, don't show menu
  if (!canRemove && !canUpdate) {
    return null;
  }

  return (
    <>
      <IconButton
        size="small"
        onClick={handleClick}
        aria-label={`Actions for ${member.full_name || member.username}`}
      >
        <MoreVertIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        {canUpdate && (
          <MenuItem onClick={handleUpdateRole}>
            <EditIcon sx={{ mr: 1, fontSize: 18 }} />
            Change Role
          </MenuItem>
        )}
        {canRemove && (
          <MenuItem onClick={handleRemove} sx={{ color: 'error.main' }}>
            <DeleteIcon sx={{ mr: 1, fontSize: 18 }} />
            Remove Member
          </MenuItem>
        )}
      </Menu>
    </>
  );
};

const MemberSkeleton: React.FC = () => (
  <>
    {[1, 2, 3].map((index) => (
      <TableRow key={index}>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Skeleton variant="circular" width={40} height={40} />
            <Box>
              <Skeleton variant="text" width={120} height={20} />
              <Skeleton variant="text" width={80} height={16} />
            </Box>
          </Box>
        </TableCell>
        <TableCell>
          <Skeleton variant="text" width={150} />
        </TableCell>
        <TableCell>
          <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 12 }} />
        </TableCell>
        <TableCell>
          <Skeleton variant="text" width={100} />
        </TableCell>
        <TableCell>
          <Skeleton variant="circular" width={24} height={24} />
        </TableCell>
      </TableRow>
    ))}
  </>
);

const getInitials = (name?: string, username?: string): string => {
  const displayName = name || username || '';
  const parts = displayName.split(' ');
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return displayName.substring(0, 2).toUpperCase();
};

const MemberListTable = React.forwardRef<MemberListTableRef, MemberListTableProps>(({
  onInviteMember,
  onUpdateMemberRole,
  onRemoveMember
}, ref) => {
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const { currentOrganization } = useOrganization();
  const { user } = useAuth();

  const userRole = currentOrganization?.user_role;
  const canManage = canInviteMembers(userRole);

  // Filter members based on search query
  const filteredMembers = members.filter(member => {
    const searchLower = searchQuery.toLowerCase();
    return (
      (member.full_name?.toLowerCase().includes(searchLower)) ||
      member.username.toLowerCase().includes(searchLower) ||
      member.email.toLowerCase().includes(searchLower) ||
      getRoleDisplayName(member.role).toLowerCase().includes(searchLower)
    );
  });

  const fetchMembers = async () => {
    if (!currentOrganization?.id) return;

    try {
      setError(null);
      const memberList = await organizationApi.getOrganizationMembers(currentOrganization.id);
      setMembers(memberList);
    } catch (err: any) {
      console.error('Failed to fetch members:', err);
      setError(err.response?.data?.detail || 'Failed to load members');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchMembers();
  };

  useEffect(() => {
    fetchMembers();
  }, [currentOrganization?.id]);

  // Expose refresh function to parent components
  React.useImperativeHandle(ref, () => ({
    refresh: fetchMembers
  }));

  if (loading) {
    return (
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Team Members
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Member</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Joined</TableCell>
                  <TableCell width={50}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <MemberSkeleton />
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ p: 3 }}>
        {/* Header Section */}
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3
        }}>
          <Typography variant="h6">
            Team Members ({members.length})
          </Typography>
          {canManage && (
            <Button
              variant="contained"
              startIcon={<PersonAddIcon />}
              onClick={onInviteMember}
            >
              Invite Member
            </Button>
          )}
        </Box>

        {/* Search and Actions */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search members..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flexGrow: 1, maxWidth: 300 }}
          />
          <Button
            variant="outlined"
            size="small"
            onClick={handleRefresh}
            disabled={refreshing}
            startIcon={refreshing ? <CircularProgress size={16} /> : undefined}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Members Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Member</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell width={60} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredMembers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                      <PersonIcon color="disabled" sx={{ fontSize: 48 }} />
                      <Typography variant="body2" color="text.secondary">
                        {searchQuery ? 'No members found matching your search' : 'No members found'}
                      </Typography>
                      {searchQuery && (
                        <Button
                          size="small"
                          onClick={() => setSearchQuery('')}
                        >
                          Clear Search
                        </Button>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                filteredMembers.map((member) => (
                  <TableRow key={member.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar
                          sx={{
                            width: 40,
                            height: 40,
                            bgcolor: 'primary.main',
                            fontSize: '0.875rem'
                          }}
                        >
                          {getInitials(member.full_name, member.username)}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {member.full_name || member.username}
                          </Typography>
                          {member.full_name && (
                            <Typography variant="caption" color="text.secondary">
                              @{member.username}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {member.email}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getRoleDisplayName(member.role)}
                        color={getRoleBadgeColor(member.role)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(member.joined_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {canAccessMemberActions(userRole, member.role, member.user_id, user?.id || '') && (
                        <ActionMenu
                          member={member}
                          onUpdateRole={() => onUpdateMemberRole(member)}
                          onRemove={() => onRemoveMember(member)}
                          userRole={userRole}
                          currentUserId={user?.id}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Paper>
  );
});

MemberListTable.displayName = 'MemberListTable';

export default MemberListTable;