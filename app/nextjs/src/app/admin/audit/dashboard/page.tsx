'use client';

/**
 * Admin Audit Dashboard Page
 *
 * Features:
 * - Interactive analytics dashboard
 * - Real-time statistics and trends
 * - Visual data representations
 */

import React from 'react';
import {
  Box,
  Typography,
  Breadcrumbs,
  Link,
} from '@mui/material';

import { AuditStatsDashboard } from '../../../../components/audit/AuditStatsDashboard';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function AdminAuditDashboardPage() {
  const handleExportReport = () => {
    // Would implement dashboard-specific export functionality
    console.log('Exporting dashboard report...');
  };

  return (
    <MinimalErrorBoundary context={{ component: 'AdminAuditDashboardPage' }}>
      <Box sx={{ p: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">
            Admin
          </Link>
          <Link color="inherit" href="/admin/audit" underline="hover">
            Audit System
          </Link>
          <Typography color="text.primary">Analytics Dashboard</Typography>
        </Breadcrumbs>

        {/* Dashboard */}
        <AuditStatsDashboard
          organizationId={undefined} // Would come from context
          onExportReport={handleExportReport}
        />
      </Box>
    </MinimalErrorBoundary>
  );
}