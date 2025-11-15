'use client';

/**
 * Admin Audit Layout Component
 *
 * Features:
 * - Consistent audit system layout
 * - Navigation sidebar integration
 * - Responsive design
 */

import React from 'react';
import { Box } from '@mui/material';

import { AuditNavigation } from '../../../components/audit/AuditNavigation';
import { MinimalErrorBoundary } from '../../../components/common/ErrorBoundary';

interface AdminAuditLayoutProps {
  children: React.ReactNode;
}

export default function AdminAuditLayout({ children }: AdminAuditLayoutProps) {
  return (
    <MinimalErrorBoundary context={{ component: 'AdminAuditLayout' }}>
      <Box sx={{ display: 'flex', height: '100vh' }}>
        {/* Navigation Sidebar */}
        <AuditNavigation organizationId={undefined} />

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: 'auto',
            bgcolor: 'background.default',
          }}
        >
          {children}
        </Box>
      </Box>
    </MinimalErrorBoundary>
  );
}