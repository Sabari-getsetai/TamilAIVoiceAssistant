'use client';

import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { ServiceDependencyVisualization } from '../../../../components/microservices/ServiceDependencyVisualization';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function MicroservicesDependenciesPage() {
  return (
    <MinimalErrorBoundary context={{ component: 'MicroservicesDependenciesPage' }}>
      <Box sx={{ p: 3 }}>
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">Admin</Link>
          <Link color="inherit" href="/admin/microservices" underline="hover">Microservices</Link>
          <Typography color="text.primary">Dependencies</Typography>
        </Breadcrumbs>
        <ServiceDependencyVisualization organizationId={undefined} />
      </Box>
    </MinimalErrorBoundary>
  );
}