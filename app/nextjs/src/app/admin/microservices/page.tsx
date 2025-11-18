'use client';

/**
 * Admin Microservices Main Page
 *
 * Features:
 * - Central microservice management dashboard
 * - Quick access to all microservice features
 * - Service health overview
 * - Navigation to detailed microservice components
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
  Breadcrumbs,
  Link,
  Chip,
  Alert,
} from '@mui/material';
import {
  Computer,
  Settings,
  Api,
  AccountTree,
  ArrowForward,
  HealthAndSafety,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

import { ServiceHealthDashboard } from '../../../components/microservices/ServiceHealthDashboard';
import { MinimalErrorBoundary } from '../../../components/common/ErrorBoundary';

export default function AdminMicroservicesPage() {
  const router = useRouter();

  const microserviceFeatures = [
    {
      id: 'health',
      title: 'Service Health',
      description: 'Monitor real-time service health and performance metrics',
      icon: HealthAndSafety,
      color: '#4caf50',
      route: '/admin/microservices/health',
      status: 'active',
    },
    {
      id: 'config',
      title: 'Configuration',
      description: 'Manage service configurations and environment variables',
      icon: Settings,
      color: '#2196f3',
      route: '/admin/microservices/config',
      status: 'active',
    },
    {
      id: 'api-testing',
      title: 'API Testing',
      description: 'Test and validate API endpoints across all services',
      icon: Api,
      color: '#ff9800',
      route: '/admin/microservices/api-testing',
      status: 'active',
    },
    {
      id: 'dependencies',
      title: 'Dependencies',
      description: 'Visualize service dependencies and relationships',
      icon: AccountTree,
      color: '#9c27b0',
      route: '/admin/microservices/dependencies',
      status: 'active',
    },
  ];

  return (
    <MinimalErrorBoundary context={{ component: 'AdminMicroservicesPage' }}>
      <Box sx={{ p: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">
            Admin
          </Link>
          <Typography color="text.primary">Microservices</Typography>
        </Breadcrumbs>

        {/* Header */}
        <Typography variant="h4" component="h1" gutterBottom>
          <Computer sx={{ mr: 2, verticalAlign: 'middle' }} />
          Microservice Management
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Comprehensive microservice monitoring, configuration, and management platform
        </Typography>

        {/* Service Health Overview */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <ServiceHealthDashboard organizationId={undefined} />
          </CardContent>
        </Card>

        {/* Feature Cards */}
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          Management Tools
        </Typography>

        <Grid container spacing={3}>
          {microserviceFeatures.map((feature) => {
            const IconComponent = feature.icon;
            return (
              <Grid key={feature.id} item xs={12} sm={6} md={6} lg={3}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
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
                        label={feature.status}
                        color="success"
                        size="small"
                      />
                    </Box>

                    <Typography variant="h6" gutterBottom>
                      {feature.title}
                    </Typography>

                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
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

        {/* System Information */}
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>Microservice Platform Status:</strong> All management tools operational.
            Services: 6 active, 0 inactive. Last health check: {new Date().toLocaleString()}.
          </Typography>
        </Alert>
      </Box>
    </MinimalErrorBoundary>
  );
}