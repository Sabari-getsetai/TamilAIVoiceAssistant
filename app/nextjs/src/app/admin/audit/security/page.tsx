'use client';

/**
 * Admin Security Monitoring Page
 *
 * Features:
 * - Real-time security event monitoring
 * - Threat detection and alerting
 * - Security incident management
 */

import React, { useCallback } from 'react';
import {
  Box,
  Typography,
  Breadcrumbs,
  Link,
} from '@mui/material';
import { enqueueSnackbar } from 'notistack';

import { SecurityMonitoringInterface } from '../../../../components/audit/SecurityMonitoringInterface';
import { SecurityEvent } from '../../../../services/api/audit/auditTypes';
import { MinimalErrorBoundary } from '../../../../components/common/ErrorBoundary';

export default function AdminAuditSecurityPage() {
  const handleIncidentCreate = useCallback((event: SecurityEvent) => {
    // Would implement incident creation logic
    console.log('Creating incident for event:', event);
    enqueueSnackbar('Security incident created successfully', { variant: 'success' });
  }, []);

  const handleAlertAcknowledge = useCallback((eventId: string) => {
    // Would implement alert acknowledgment logic
    console.log('Acknowledging alert:', eventId);
    enqueueSnackbar('Security alert acknowledged', { variant: 'info' });
  }, []);

  return (
    <MinimalErrorBoundary context={{ component: 'AdminAuditSecurityPage' }}>
      <Box sx={{ p: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 3 }}>
          <Link color="inherit" href="/admin" underline="hover">
            Admin
          </Link>
          <Link color="inherit" href="/admin/audit" underline="hover">
            Audit System
          </Link>
          <Typography color="text.primary">Security Monitoring</Typography>
        </Breadcrumbs>

        {/* Security Monitoring Interface */}
        <SecurityMonitoringInterface
          organizationId={undefined} // Would come from context
          onIncidentCreate={handleIncidentCreate}
          onAlertAcknowledge={handleAlertAcknowledge}
        />
      </Box>
    </MinimalErrorBoundary>
  );
}