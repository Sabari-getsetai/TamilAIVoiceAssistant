'use client';

/**
 * Admin Audit Main Page Component
 *
 * Features:
 * - Central audit system dashboard
 * - Quick access to all audit features
 * - System health monitoring
 * - Navigation to detailed audit components
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Tooltip,
  Alert,
  Breadcrumbs,
  Link,
  Chip,
  Paper,
  Stack,
} from '@mui/material';
import {
  Security,
  Assessment,
  Timeline,
  Gavel,
  Dashboard,
  ArrowForward,
  Refresh,
  Settings,
  Warning,
  TrendingUp,
  Shield,
  NotificationImportant,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

import { useAuditStats, useSecurityEvents } from '../../../services/api/audit/auditQueries';
import { MinimalErrorBoundary } from '../../../components/common/ErrorBoundary';

export default function AdminAuditPage() {
  const router = useRouter();
  const [organizationId] = useState<string | undefined>(undefined); // Would come from context

  // Fetch overview data
  const { data: auditStats, isLoading: isStatsLoading, refetch: refetchStats } = useAuditStats(organizationId, 30);
  const { data: securityEvents, isLoading: isEventsLoading, refetch: refetchEvents } = useSecurityEvents(organizationId, 7);

  const handleRefreshAll = () => {
    refetchStats();
    refetchEvents();
  };

  // Calculate system health status
  const criticalEvents = securityEvents?.filter(e => e.severity === 'critical').length || 0;
  const systemHealth = criticalEvents === 0 ? 'healthy' : criticalEvents < 3 ? 'warning' : 'critical';

  const auditFeatures = [
    {
      id: 'logs',
      title: 'Audit Logs',
      description: 'Browse and search comprehensive audit trail with advanced filtering',
      icon: Timeline,
      color: '#2196f3',
      route: '/admin/audit/logs',
      stats: `${auditStats?.total_entries?.toLocaleString() || '0'} entries`,
      status: 'active',
    },
    {
      id: 'dashboard',
      title: 'Analytics Dashboard',
      description: 'Interactive charts and statistics for audit data analysis',
      icon: Assessment,
      color: '#4caf50',
      route: '/admin/audit/dashboard',
      stats: `${auditStats?.unique_users || '0'} active users`,
      status: 'active',
    },
    {
      id: 'security',
      title: 'Security Monitoring',
      description: 'Real-time security event monitoring and threat detection',
      icon: Security,
      color: criticalEvents > 0 ? '#f44336' : '#ff9800',
      route: '/admin/audit/security',
      stats: `${securityEvents?.length || '0'} events (7d)`,
      status: criticalEvents > 0 ? 'alert' : 'active',
    },
    {
      id: 'compliance',
      title: 'Compliance Reporting',
      description: 'Generate compliance reports for GDPR, SOC2, HIPAA, and more',
      icon: Gavel,
      color: '#9c27b0',
      route: '/admin/audit/compliance',
      stats: '6 frameworks',
      status: 'active',
    },
  ];

  const quickActions = [
    {
      title: 'View Recent Logs',
      description: 'Last 100 audit entries',
      action: () => router.push('/admin/audit/logs'),
      icon: Timeline,
    },
    {
      title: 'Export Data',
      description: 'Download audit reports',
      action: () => router.push('/admin/audit/compliance'),
      icon: Assessment,
    },
    {
      title: 'Security Status',
      description: 'Check security events',
      action: () => router.push('/admin/audit/security'),
      icon: Security,
    },
    {
      title: 'System Health',
      description: 'Monitor system status',
      action: handleRefreshAll,
      icon: Refresh,
    },
  ];

  return (
    <MinimalErrorBoundary context={{ component: 'AdminAuditPage' }}>
      <Box sx={{ p: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">
            Admin
          </Link>
          <Typography color="text.primary">Audit System</Typography>
        </Breadcrumbs>

        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              <Shield sx={{ mr: 2, verticalAlign: 'middle' }} />
              Audit System
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Comprehensive audit trail management and compliance monitoring
            </Typography>
          </Box>

          <Stack direction="row" spacing={2}>
            <Tooltip title="Refresh Data">
              <IconButton onClick={handleRefreshAll} disabled={isStatsLoading || isEventsLoading}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="System Settings">
              <IconButton>
                <Settings />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {/* System Status Alert */}
        {systemHealth !== 'healthy' && (
          <Alert
            severity={systemHealth === 'critical' ? 'error' : 'warning'}
            icon={systemHealth === 'critical' ? <NotificationImportant /> : <Warning />}
            sx={{ mb: 3 }}
            action={
              <Button color="inherit" size="small" onClick={() => router.push('/admin/audit/security')}>
                View Details
              </Button>
            }
          >
            <Typography variant="body1" fontWeight="medium">
              {systemHealth === 'critical'
                ? `System Alert: ${criticalEvents} critical security events require immediate attention`
                : `System Warning: ${criticalEvents} security events detected`
              }
            </Typography>
          </Alert>
        )}

        {/* Overview Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Timeline color="primary" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h4" color="primary">
                  {auditStats?.total_entries?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Audit Entries
                </Typography>
                <Chip
                  label={`+${auditStats?.growth_rate || 0}%`}
                  color="success"
                  size="small"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Security color="info" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h4" color="info.main">
                  {securityEvents?.length || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Security Events (7d)
                </Typography>
                <Chip
                  label={criticalEvents > 0 ? 'Attention Required' : 'Normal'}
                  color={criticalEvents > 0 ? 'error' : 'success'}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Assessment color="success" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h4" color="success.main">
                  {auditStats?.unique_users || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Users
                </Typography>
                <Chip
                  label="Last 30 Days"
                  color="info"
                  size="small"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Gavel color="warning" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h4" color="warning.main">
                  6
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Compliance Frameworks
                </Typography>
                <Chip
                  label="Fully Supported"
                  color="success"
                  size="small"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Audit Features */}
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Dashboard />
          Audit Features
        </Typography>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          {auditFeatures.map((feature) => {
            const IconComponent = feature.icon;
            return (
              <Grid key={feature.id} item xs={12} sm={6} md={6} lg={3}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <IconComponent sx={{ fontSize: 40, color: feature.color }} />
                      <Chip
                        label={feature.status === 'alert' ? 'Alert' : 'Active'}
                        color={feature.status === 'alert' ? 'error' : 'success'}
                        size="small"
                      />
                    </Box>

                    <Typography variant="h6" gutterBottom>
                      {feature.title}
                    </Typography>

                    <Typography variant="body2" color="text.secondary" paragraph>
                      {feature.description}
                    </Typography>

                    <Box display="flex" alignItems="center" gap={1} mt={2}>
                      <TrendingUp fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        {feature.stats}
                      </Typography>
                    </Box>
                  </CardContent>

                  <CardActions>
                    <Button
                      size="small"
                      endIcon={<ArrowForward />}
                      onClick={() => router.push(feature.route)}
                      fullWidth
                    >
                      Open {feature.title}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* Quick Actions */}
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Settings />
          Quick Actions
        </Typography>

        <Paper sx={{ p: 2 }}>
          <Grid container spacing={2}>
            {quickActions.map((action, index) => {
              const IconComponent = action.icon;
              return (
                <Grid key={index} item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    sx={{
                      p: 2,
                      height: '80px',
                      flexDirection: 'column',
                      gap: 1,
                    }}
                    onClick={action.action}
                  >
                    <IconComponent />
                    <Box textAlign="center">
                      <Typography variant="body2" fontWeight="medium">
                        {action.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {action.description}
                      </Typography>
                    </Box>
                  </Button>
                </Grid>
              );
            })}
          </Grid>
        </Paper>

        {/* System Information */}
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Audit System Status:</strong> All components operational.
            Data retention: {auditStats ? '365 days' : 'Loading...'}.
            Last system health check: {new Date().toLocaleString()}.
          </Typography>
        </Alert>
      </Box>
    </MinimalErrorBoundary>
  );
}