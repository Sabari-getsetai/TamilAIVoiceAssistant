'use client';

/**
 * Admin Compliance Reporting Page
 *
 * Features:
 * - Compliance report generation
 * - Multi-framework support
 * - Export and scheduling capabilities
 */

import React, { useCallback } from 'react';
import {
  Box,
  Typography,
  Breadcrumbs,
  Link,
} from '@mui/material';
import { enqueueSnackbar } from 'notistack';

import { ComplianceReportingInterface } from '../../../../components/audit/ComplianceReportingInterface';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function AdminAuditCompliancePage() {
  const handleReportGenerated = useCallback((reportId: string) => {
    console.log('Report generated with ID:', reportId);
    enqueueSnackbar('Compliance report generated successfully', { variant: 'success' });
  }, []);

  return (
    <MinimalErrorBoundary context={{ component: 'AdminAuditCompliancePage' }}>
      <Box sx={{ p: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">
            Admin
          </Link>
          <Link color="inherit" href="/admin/audit" underline="hover">
            Audit System
          </Link>
          <Typography color="text.primary">Compliance Reporting</Typography>
        </Breadcrumbs>

        {/* Compliance Reporting Interface */}
        <ComplianceReportingInterface
          organizationId={undefined} // Would come from context
          onReportGenerated={handleReportGenerated}
        />
      </Box>
    </MinimalErrorBoundary>
  );
}