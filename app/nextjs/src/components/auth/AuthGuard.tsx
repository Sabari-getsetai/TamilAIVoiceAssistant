'use client';

import React, { useEffect, ReactNode, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '@/contexts/AuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { UserRole } from '@/types/auth';

interface AuthGuardProps {
  children: ReactNode;
  requireOrganization?: boolean;
  requireAdmin?: boolean;
  requireSystemAdmin?: boolean;
  allowedRoles?: UserRole[];
  fallbackTo?: string;
  loadingMessage?: string;
}

/**
 * AuthGuard Component
 *
 * Protects routes by checking:
 * 1. User authentication status
 * 2. Organization membership (if required)
 * 3. User role/permissions (if specified)
 *
 * Automatically redirects:
 * - Unauthenticated users to login
 * - Users without organizations to setup page
 * - Users without required roles to home page
 */
export default function AuthGuard({
  children,
  requireOrganization = true,
  requireAdmin = false,
  requireSystemAdmin = false,
  allowedRoles,
  fallbackTo,
  loadingMessage = "Loading..."
}: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const {
    hasOrganizations,
    needsOrganizationSetup,
    isLoading: orgLoading
  } = useOrganization();

  // Helper function to check if user has required role
  const hasRequiredRole = useCallback((userRole: UserRole | undefined): boolean => {
    if (!userRole) return false;

    // If specific roles are specified, check against those
    if (allowedRoles && allowedRoles.length > 0) {
      return allowedRoles.includes(userRole);
    }

    // If requireSystemAdmin is true, check for system admin roles only
    if (requireSystemAdmin) {
      return userRole === UserRole.ADMIN || userRole === UserRole.SUPERADMIN;
    }

    // If requireAdmin is true, check for admin roles (backward compatibility)
    if (requireAdmin) {
      return userRole === UserRole.ADMIN || userRole === UserRole.SUPERADMIN || userRole === UserRole.ORGANIZATION_ADMIN;
    }

    // If no specific role requirements, any authenticated user is allowed
    return true;
  },[allowedRoles, requireAdmin, requireSystemAdmin]);

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
        requireOrganization,
        requireAdmin,
        requireSystemAdmin,
        userRole: user?.role,
        allowedRoles
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
          // Role-based redirect
          const isSystemAdmin = user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERADMIN;
          router.push(isSystemAdmin ? '/admin' : '/org');
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
        console.debug('[AuthGuard] User has organizations but on setup page, redirecting to appropriate dashboard');
        // Role-based redirect
        const isSystemAdmin = user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERADMIN;
        router.push(isSystemAdmin ? '/admin' : '/org');
        return;
      }

      // Check user role permissions if required
      if ((requireAdmin || requireSystemAdmin || allowedRoles) && isAuthenticated && user) {
        const userHasRequiredRole = hasRequiredRole(user.role);

        if (!userHasRequiredRole) {
          console.debug('[AuthGuard] User lacks required role, redirecting to home', {
            userRole: user.role,
            requireAdmin,
            requireSystemAdmin,
            allowedRoles
          });

          // Redirect to fallback or appropriate dashboard
          if (fallbackTo) {
            router.push(fallbackTo);
          } else {
            // Role-based redirect based on what the user can access
            const isSystemAdmin = user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERADMIN;
            router.push(isSystemAdmin ? '/admin' : '/org');
          }
          return;
        }
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
    requireAdmin,
    requireSystemAdmin,
    allowedRoles,
    fallbackTo,
    user,
    hasRequiredRole
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
          {loadingMessage}
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

  // Show message for users without required role permissions
  if ((requireAdmin || requireSystemAdmin || allowedRoles) && isAuthenticated && user) {
    const userHasRequiredRole = hasRequiredRole(user.role);

    if (!userHasRequiredRole) {
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
          <Alert severity="error">
            You don&apos;t have permission to access this page.
            {requireSystemAdmin && ' System administrator privileges are required.'}
            {requireAdmin && !requireSystemAdmin && ' Administrator privileges are required.'}
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Current role: {user.role}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Redirecting to home page...
          </Typography>
        </Box>
      );
    }
  }

  // If all checks pass, render the protected content
  return <>{children}</>;
}