'use client';

import React, { useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '@/contexts/AuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';

interface AuthGuardProps {
  children: ReactNode;
  requireOrganization?: boolean;
  fallbackTo?: string;
}

/**
 * AuthGuard Component
 *
 * Protects routes by checking:
 * 1. User authentication status
 * 2. Organization membership (if required)
 *
 * Automatically redirects unauthenticated users to login
 * and users without organizations to setup page.
 */
export default function AuthGuard({
  children,
  requireOrganization = true,
  fallbackTo
}: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    hasOrganizations,
    needsOrganizationSetup,
    isLoading: orgLoading
  } = useOrganization();

  useEffect(() => {
    // Add debounce timer to prevent rapid state changes during loading
    const timer = setTimeout(() => {
      console.debug('[AuthGuard] Navigation check triggered:', {
        pathname,
        authLoading,
        orgLoading,
        isAuthenticated,
        hasOrganizations,
        needsOrganizationSetup,
        requireOrganization
      });

      // Don't do anything while still loading
      if (authLoading || orgLoading) {
        console.debug('[AuthGuard] Still loading, skipping navigation check');
        return;
      }

      // Public routes that don't need authentication
      const publicRoutes = ['/login', '/register'];
      const isPublicRoute = publicRoutes.includes(pathname);

      // If user is not authenticated
      if (!isAuthenticated) {
        if (!isPublicRoute) {
          console.debug('[AuthGuard] Redirecting unauthenticated user to login');
          // Redirect to login with return URL
          const returnUrl = encodeURIComponent(pathname);
          router.push(`/login?returnUrl=${returnUrl}`);
        }
        return;
      }

      // If user is authenticated but on public routes, redirect to appropriate page
      if (isAuthenticated && isPublicRoute) {
        console.debug('[AuthGuard] Redirecting authenticated user away from public route');
        if (fallbackTo) {
          router.push(fallbackTo);
        } else if (requireOrganization && needsOrganizationSetup) {
          router.push('/setup/organization');
        } else {
          router.push('/admin');
        }
        return;
      }

      // If organization is required but user doesn't have one
      if (requireOrganization && needsOrganizationSetup) {
        console.debug('[AuthGuard] User needs organization setup, current path:', pathname);
        // Don't redirect if already on setup page
        if (pathname !== '/setup/organization') {
          console.debug('[AuthGuard] Redirecting to organization setup');
          router.push('/setup/organization');
        }
        return;
      }

      // If user has organization but is on setup page, redirect to dashboard
      if (requireOrganization && hasOrganizations && pathname === '/setup/organization') {
        console.debug('[AuthGuard] User has organizations but on setup page, redirecting to admin');
        router.push('/admin');
        return;
      }

      console.debug('[AuthGuard] No navigation action needed');
    }, 100); // 100ms debounce

    return () => clearTimeout(timer);

  }, [
    isAuthenticated,
    authLoading,
    orgLoading,
    hasOrganizations,
    needsOrganizationSetup,
    pathname,
    router,
    requireOrganization,
    fallbackTo
  ]);

  // Show loading spinner while determining auth status
  if (authLoading || orgLoading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Loading...
        </Typography>
      </Box>
    );
  }

  // Show message for unauthenticated users on protected routes
  const publicRoutes = ['/login', '/register'];
  const isPublicRoute = publicRoutes.includes(pathname);

  if (!isAuthenticated && !isPublicRoute) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2}
        px={2}
      >
        <Alert severity="warning">
          Please log in to access this page.
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Redirecting to login...
        </Typography>
      </Box>
    );
  }

  // Show message for users without organizations on protected routes
  if (requireOrganization && needsOrganizationSetup && pathname !== '/setup/organization') {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2}
        px={2}
      >
        <Alert severity="info">
          You need to create or join an organization to access this page.
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Redirecting to organization setup...
        </Typography>
      </Box>
    );
  }

  // If all checks pass, render the protected content
  return <>{children}</>;
}