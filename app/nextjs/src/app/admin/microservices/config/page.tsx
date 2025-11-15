'use client';

import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { ServiceConfigurationManager } from '../../../../components/microservices/ServiceConfigurationManager';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function MicroservicesConfigPage() {
  return (
    <MinimalErrorBoundary context={{ component: 'MicroservicesConfigPage' }}>
      <Box sx={{ p: 3 }}>
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">Admin</Link>
          <Link color="inherit" href="/admin/microservices" underline="hover">Microservices</Link>
          <Typography color="text.primary">Configuration</Typography>
        </Breadcrumbs>
        <ServiceConfigurationManager organizationId={undefined} />
      </Box>
    </MinimalErrorBoundary>
  );
}