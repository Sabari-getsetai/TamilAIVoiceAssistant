'use client';

import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  IconButton,
  Chip,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Business as BusinessIcon,
  People as PeopleIcon,
  Description as DocumentIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Upload as UploadIcon,
  ManageAccounts as ManageAccountsIcon,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useOrgDashboardData } from '@/hooks/useOrgDashboard';

/**
 * Organization Dashboard - Main landing page for /org
 *
 * Displays:
 * - Organization overview and stats
 * - Quick access to key features
 * - Member management shortcuts
 * - Document management overview
 */
export default function OrgDashboard() {
  const router = useRouter();

  // Use the new API hooks
  const { documents, stats, members, settings, isLoading, isError, refetchAll } = useOrgDashboardData();

  // Calculate dashboard stats from real data
  const orgStats = {
    totalMembers: members.data?.length || 0,
    totalDocuments: stats.data?.total_documents || 0,
    processingDocuments: stats.data?.documents_by_status?.processing || 0,
    lastActivity: stats.data?.last_updated ? new Date(stats.data.last_updated).toLocaleString() : 'No activity',
  };

  const quickActions = [
    {
      title: 'Upload Documents',
      description: 'Add new documents to knowledge base',
      icon: <UploadIcon />,
      action: () => router.push('/org/documents'),
      color: 'primary' as const,
    },
    {
      title: 'Manage Members',
      description: 'Invite and manage team members',
      icon: <ManageAccountsIcon />,
      action: () => router.push('/org/members'),
      color: 'secondary' as const,
    },
    {
      title: 'View Analytics',
      description: 'Organization usage and stats',
      icon: <AnalyticsIcon />,
      action: () => router.push('/org/analytics'),
      color: 'info' as const,
    },
    {
      title: 'Organization Settings',
      description: 'Configure organization preferences',
      icon: <SettingsIcon />,
      action: () => router.push('/org/settings'),
      color: 'warning' as const,
    },
  ];

  // Show loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Show error state
  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load organization data. Please try again.
        </Alert>
        <Button variant="contained" onClick={refetchAll}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Organization Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome to {settings.data?.organization.name || 'your organization'}. Manage documents, members, and settings.
        </Typography>
      </Box>

      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 40, mb: 1, color: 'primary.main' }} />
              <Typography variant="h4" component="div">
                {orgStats.totalMembers}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Team Members
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <DocumentIcon sx={{ fontSize: 40, mb: 1, color: 'secondary.main' }} />
              <Typography variant="h4" component="div">
                {orgStats.totalDocuments}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AnalyticsIcon sx={{ fontSize: 40, mb: 1, color: 'info.main' }} />
              <Typography variant="h4" component="div">
                {orgStats.processingDocuments}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Processing
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BusinessIcon sx={{ fontSize: 40, mb: 1, color: 'success.main' }} />
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Last Activity
              </Typography>
              <Typography variant="h6" component="div">
                {orgStats.lastActivity}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
        Quick Actions
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {quickActions.map((action, index) => (
          <Grid item xs={12} sm={6} md={6} lg={3} key={index}>
            <Card
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={action.action}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <IconButton
                    sx={{
                      color: `${action.color}.main`,
                      bgcolor: `${action.color}.light`,
                      mr: 2
                    }}
                  >
                    {action.icon}
                  </IconButton>
                  <Typography variant="h6" component="h3">
                    {action.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity & Status */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" component="h3" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mb: 2 }}>
              {documents.data && documents.data.length > 0 ? (
                documents.data.slice(0, 4).map((doc, index) => (
                  <Typography key={doc.id} variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    • {doc.uploader} uploaded "{doc.original_filename}" - {new Date(doc.upload_date).toLocaleDateString()}
                  </Typography>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent activity
                </Typography>
              )}
            </Box>
            <Button variant="outlined" size="small" onClick={() => router.push('/org/audit')}>
              View Full Audit Trail
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" component="h3" gutterBottom>
              System Status
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Document Processing</Typography>
                <Chip label="Online" color="success" size="small" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Voice Assistant</Typography>
                <Chip label="Ready" color="success" size="small" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Knowledge Base</Typography>
                <Chip label="Synced" color="info" size="small" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Storage Usage</Typography>
                <Chip label="12% Used" color="primary" size="small" />
              </Box>
            </Box>
            <Button variant="outlined" size="small" onClick={() => router.push('/org/system-status')}>
              View Detailed Status
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}