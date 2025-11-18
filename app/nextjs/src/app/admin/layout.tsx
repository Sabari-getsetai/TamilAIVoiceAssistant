'use client';

/**
 * Admin Layout - System Admin Route Protection
 *
 * This layout wraps all /admin routes and ensures only users with ADMIN
 * or SUPERADMIN roles can access system administration functionality.
 *
 * This is for system-wide administration, NOT organization management.
 * Organization management is handled in /org routes.
 *
 * Security Features:
 * - Uses ProtectedRoute component with requireSystemAdmin flag
 * - Redirects unauthorized users to home page
 * - Provides loading states during authentication check
 * - Does NOT require organization membership (system-wide access)
 */

import React from 'react';
import { ProtectedRoute } from '../../contexts/AuthContext';
import MainLayout from '../../components/layout/MainLayout';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <ProtectedRoute
      requireAuth={true}           // Must be authenticated
      requireSystemAdmin={true}    // Must have ADMIN or SUPERADMIN role (system-wide access)
      loadingMessage="Verifying system administrator permissions..."
    >
      <MainLayout>
        {children}
      </MainLayout>
    </ProtectedRoute>
  );
}