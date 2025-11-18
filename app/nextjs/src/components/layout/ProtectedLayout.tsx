'use client';

import React, { ReactNode } from 'react';
import AuthGuard from '@/components/auth/AuthGuard';
import MainLayout from '@/components/layout/MainLayout';
import { UserRole } from '@/types/auth';

interface ProtectedLayoutProps {
  children: ReactNode;
  requireOrganization?: boolean;
  requireAdmin?: boolean;
  requireSystemAdmin?: boolean;
  allowedRoles?: UserRole[];
  showSidebar?: boolean;
  title?: string;
  loadingMessage?: string;
  fallbackTo?: string;
}

/**
 * ProtectedLayout Component
 *
 * Combines authentication protection with the main layout.
 * Use this for pages that require:
 * - User authentication
 * - Organization membership (optional)
 * - Specific user roles or admin privileges (optional)
 */
export default function ProtectedLayout({
  children,
  requireOrganization = true,
  requireAdmin = false,
  requireSystemAdmin = false,
  allowedRoles,
  showSidebar = true,
  title,
  loadingMessage,
  fallbackTo
}: ProtectedLayoutProps) {
  // Note: MainLayout currently doesn't support showSidebar or title props
  // For now, we'll use the basic MainLayout and ignore those props
  // TODO: Extend MainLayout to support these props if needed

  return (
    <AuthGuard
      requireOrganization={requireOrganization}
      requireAdmin={requireAdmin}
      requireSystemAdmin={requireSystemAdmin}
      allowedRoles={allowedRoles}
      loadingMessage={loadingMessage}
      fallbackTo={fallbackTo}
    >
      <MainLayout>
        {children}
      </MainLayout>
    </AuthGuard>
  );
}