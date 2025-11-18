import React from 'react';
import AuthGuard from '@/components/auth/AuthGuard';
import MainLayout from '@/components/layout/MainLayout';

interface OrgLayoutProps {
  children: React.ReactNode;
}

/**
 * Organization Dashboard Layout
 *
 * Protects all /org routes with organization membership requirements.
 * Users need to be members of an organization to access these pages.
 */
export default function OrgLayout({ children }: OrgLayoutProps) {
  return (
    <AuthGuard
      requireOrganization={true}
      loadingMessage="Verifying organization membership..."
    >
      <MainLayout>
        {children}
      </MainLayout>
    </AuthGuard>
  );
}