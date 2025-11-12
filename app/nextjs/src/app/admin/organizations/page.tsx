'use client';

import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  LinearProgress,
  Grid,
  Chip,
  Divider,
  Avatar,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Business as BusinessIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Edit as EditIcon,
  Group as GroupIcon,
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon,
  ArrowBack as BackIcon,
} from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '../../../components/layout/ProtectedLayout';
import { useOrganization } from '@/contexts/OrganizationContext';
import { formatNumber } from '@/utils/format';

// Mock data for recent activity (will be replaced with real API calls)
interface ActivityItem {
  id: string;
  type: 'member_joined' | 'member_removed' | 'role_changed' | 'settings_updated';
  message: string;
  timestamp: Date;
  user?: string;
}

export default function OrganizationManagementPage() {
  const router = useRouter();
  const {
    currentOrganization,
    isLoading,
    error,
    refreshOrganizations,
    clearError
  } = useOrganization();

  const [refreshing, setRefreshing] = useState(false);

  // Mock recent activity data
  const [recentActivity] = useState<ActivityItem[]>([
    {
      id: '1',
      type: 'member_joined',
      message: 'John Doe joined the organization',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      user: 'John Doe'
    },
    {
      id: '2',
      type: 'role_changed',
      message: 'Sarah Admin was promoted to Admin',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
      user: 'Sarah Admin'
    },
    {
      id: '3',
      type: 'settings_updated',
      message: 'Organization settings were updated',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
    }
  ]);

  useEffect(() => {
    // Clear any existing errors when component mounts
    if (error) {
      clearError();
    }
  }, [error, clearError]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshOrganizations();
    } catch (err) {
      console.error('Failed to refresh organization data:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const handleBack = () => {
    router.push('/admin');
  };

  const formatRelativeTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      return 'Just now';
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
  };

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'member_joined':
        return <PersonIcon color="success" />;
      case 'member_removed':
        return <PersonIcon color="error" />;
      case 'role_changed':
        return <AdminIcon color="warning" />;
      case 'settings_updated':
        return <SettingsIcon color="info" />;
      default:
        return <BusinessIcon />;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'owner':
        return 'error';
      case 'admin':
        return 'warning';
      case 'member':
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <ProtectedLayout title="Organization Management">
        <Container maxWidth="lg">
          <Box sx={{ mt: 4 }}>
            <Typography variant="h4" gutterBottom>
              Loading Organization...
            </Typography>
            <LinearProgress />
          </Box>
        </Container>
      </ProtectedLayout>
    );
  }

  if (!currentOrganization) {
    return (
      <ProtectedLayout title="Organization Management">
        <Container maxWidth="lg">
          <Box sx={{ mt: 4 }}>
            <Alert severity="warning">
              No active organization found. Please create or join an organization first.
            </Alert>
          </Box>
        </Container>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout title="Organization Management">
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <BackIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
              Organization Management
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Manage members, settings, and organization details
            </Typography>
          </Box>
          <Tooltip title="Refresh data">
            <IconButton
              onClick={handleRefresh}
              disabled={refreshing}
              color="primary"
            >
              <RefreshIcon sx={{
                animation: refreshing ? 'spin 1s linear infinite' : 'none',
                '@keyframes spin': {
                  '0%': { transform: 'rotate(0deg)' },
                  '100%': { transform: 'rotate(360deg)' }
                }
              }} />
            </IconButton>
          </Tooltip>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={clearError}>
            {error}
          </Alert>
        )}

        {/* Organization Overview */}
        <Card sx={{ mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3, mb: 3 }}>
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: 'primary.main',
                  fontSize: '2rem'
                }}
              >
                <BusinessIcon fontSize="large" />
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Typography variant="h4" component="h2" fontWeight="bold">
                    {currentOrganization.name}
                  </Typography>
                  <Chip
                    label={currentOrganization.user_role || currentOrganization.current_user_role || 'Member'}
                    color={getRoleColor(currentOrganization.user_role || currentOrganization.current_user_role || 'member') as any}
                    size="small"
                  />
                </Box>
                {currentOrganization.description && (
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    {currentOrganization.description}
                  </Typography>
                )}
                <Stack direction="row" spacing={2} flexWrap="wrap">
                  {currentOrganization.industry && (
                    <Chip label={currentOrganization.industry} variant="outlined" size="small" />
                  )}
                  {currentOrganization.size && (
                    <Chip
                      label={`${currentOrganization.size.charAt(0).toUpperCase() + currentOrganization.size.slice(1)} Size`}
                      variant="outlined"
                      size="small"
                    />
                  )}
                  <Chip
                    label={`Created ${new Date(currentOrganization.created_at).toLocaleDateString()}`}
                    variant="outlined"
                    size="small"
                  />
                </Stack>
              </Box>
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={() => handleNavigation('/admin/organizations/settings')}
                sx={{ minWidth: 'auto' }}
              >
                Edit
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Organization Stats */}
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Total Members
                  </Typography>
                  <Typography variant="h3" color="primary.main" fontWeight="bold">
                    {formatNumber(currentOrganization.member_count || 0)}
                  </Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Plan
                  </Typography>
                  <Typography variant="h6" color="text.primary" fontWeight="medium">
                    {currentOrganization.subscription_plan?.charAt(0).toUpperCase() +
                     currentOrganization.subscription_plan?.slice(1) || 'Free'}
                  </Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Status
                  </Typography>
                  <Chip
                    label={currentOrganization.subscription_status || 'Active'}
                    color={currentOrganization.subscription_status === 'active' ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Timezone
                  </Typography>
                  <Typography variant="body1" color="text.primary">
                    {currentOrganization.timezone || 'UTC'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            Quick Actions
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => handleNavigation('/admin/organizations/members')}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <PeopleIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Manage Members
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Invite new members, update roles, and manage team access
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => handleNavigation('/admin/organizations/settings')}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <SettingsIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Organization Settings
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Update organization details, billing, and preferences
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => handleNavigation('/admin/statistics')}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <TimelineIcon sx={{ fontSize: 48, color: 'info.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Analytics & Usage
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    View organization usage statistics and insights
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* Recent Activity */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h5" gutterBottom>
                Recent Activity
              </Typography>
              <Button
                variant="text"
                size="small"
                onClick={() => handleNavigation('/admin/organizations/activity')}
              >
                View All
              </Button>
            </Box>

            {recentActivity.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <GroupIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  No recent activity to show
                </Typography>
                <Typography variant="body2" color="text.disabled">
                  Organization activity will appear here
                </Typography>
              </Box>
            ) : (
              <Box>
                {recentActivity.map((activity, index) => (
                  <Box
                    key={activity.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      py: 2,
                      borderBottom: index < recentActivity.length - 1 ? '1px solid' : 'none',
                      borderBottomColor: 'divider'
                    }}
                  >
                    <Avatar sx={{ width: 40, height: 40, bgcolor: 'background.paper' }}>
                      {getActivityIcon(activity.type)}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body1">
                        {activity.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatRelativeTime(activity.timestamp)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Container>
    </ProtectedLayout>
  );
}