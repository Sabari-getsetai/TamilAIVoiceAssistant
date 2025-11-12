'use client';

import React, { ReactNode } from 'react';
import AuthGuard from '@/components/auth/AuthGuard';
import MainLayout from '@/components/layout/MainLayout';

interface ProtectedLayoutProps {
  children: ReactNode;
  requireOrganization?: boolean;
  showSidebar?: boolean;
  title?: string;
}

/**
 * ProtectedLayout Component
 *
 * Combines authentication protection with the main layout.
 * Use this for pages that require user authentication and/or organization membership.
 */
export default function ProtectedLayout({
  children,
  requireOrganization = true,
  showSidebar = true,
  title
}: ProtectedLayoutProps) {
  // Note: MainLayout currently doesn't support showSidebar or title props
  // For now, we'll use the basic MainLayout and ignore those props
  // TODO: Extend MainLayout to support these props if needed

  return (
    <AuthGuard requireOrganization={requireOrganization}>
      <MainLayout>
        {children}
      </MainLayout>
    </AuthGuard>
  );
}