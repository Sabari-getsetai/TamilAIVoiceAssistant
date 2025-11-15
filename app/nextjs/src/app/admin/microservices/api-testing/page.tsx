'use client';

import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { ApiEndpointTester } from '../../../../components/microservices/ApiEndpointTester';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function MicroservicesApiTestingPage() {
  return (
    <MinimalErrorBoundary context={{ component: 'MicroservicesApiTestingPage' }}>
      <Box sx={{ p: 3 }}>
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">Admin</Link>
          <Link color="inherit" href="/admin/microservices" underline="hover">Microservices</Link>
          <Typography color="text.primary">API Testing</Typography>
        </Breadcrumbs>
        <ApiEndpointTester organizationId={undefined} />
      </Box>
    </MinimalErrorBoundary>
  );
}