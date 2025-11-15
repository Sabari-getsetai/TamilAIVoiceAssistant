'use client';

import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { ServiceHealthDashboard } from '../../../../components/microservices/ServiceHealthDashboard';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function MicroservicesHealthPage() {
  return (
    <MinimalErrorBoundary context={{ component: 'MicroservicesHealthPage' }}>
      <Box sx={{ p: 3 }}>
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">Admin</Link>
          <Link color="inherit" href="/admin/microservices" underline="hover">Microservices</Link>
          <Typography color="text.primary">Health Monitoring</Typography>
        </Breadcrumbs>
        <ServiceHealthDashboard organizationId={undefined} />
      </Box>
    </MinimalErrorBoundary>
  );
}