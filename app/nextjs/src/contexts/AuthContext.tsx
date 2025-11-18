'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useSnackbar } from 'notistack';
import { Box, CircularProgress, Typography, Button, Alert } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthContextType,
  AuthError,
} from '../types/auth';
import { UserRole } from '../types/auth';
import AuthApiService from '../services/api/authApi';

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component props
interface AuthProviderProps {
  children: ReactNode;
}

// Auth provider component
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const router = useRouter();
  const { enqueueSnackbar } = useSnackbar();

  // Check if user is authenticated
  const isAuthenticated = !!user;

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('🔐 Initializing authentication...');
      setAuthError(null);
      
      try {
        // Add timeout to prevent infinite loading
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Authentication timeout')), 30000);
        });

        // Check if user has valid token
        if (AuthApiService.isAuthenticated()) {
          console.log('🔑 Token found, fetching user data...');
          
          // Race between getting user and timeout
          const currentUser = await Promise.race([
            AuthApiService.getCurrentUser(),
            timeoutPromise
          ]) as User;
          
          console.log('✅ User authenticated:', currentUser.username);
          setUser(currentUser);
        } else {
          console.log('❌ No valid token found');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
        console.error('🚨 Auth initialization failed:', errorMessage);
        
        // Token is invalid or expired, clear it
        if (errorMessage !== 'Authentication timeout') {
          await AuthApiService.logout();
        }
        
        setAuthError(errorMessage);
        
        // Show error to user if it's not just missing token
        if (AuthApiService.isAuthenticated()) {
          enqueueSnackbar(`Authentication failed: ${errorMessage}`, {
            variant: 'error',
          });
        }
      } finally {
        console.log('🏁 Auth initialization complete');
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [retryCount, enqueueSnackbar]);

  // Retry authentication
  const retryAuth = () => {
    console.log('🔄 Retrying authentication...');
    setIsLoading(true);
    setRetryCount(prev => prev + 1);
  };

  // Login function
  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const { user: loggedInUser } = await AuthApiService.login(credentials);
      setUser(loggedInUser);
      
      enqueueSnackbar(`Welcome back, ${loggedInUser.full_name || loggedInUser.username}!`, {
        variant: 'success',
      });

      // Check user role and redirect accordingly
      if ([UserRole.ADMIN, UserRole.SUPERADMIN].includes(loggedInUser.role)) {
        // System admins go to system admin dashboard regardless of organization
        router.push('/admin');
      } else if (!loggedInUser.active_organization_id) {
        // Regular users need an organization - redirect to setup
        router.push('/setup/organization');
      } else {
        // Regular users with organization go to org dashboard
        router.push('/org');
      }
    } catch (error) {
      const authError = error as AuthError;
      enqueueSnackbar(authError.message || 'Login failed', {
        variant: 'error',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const newUser = await AuthApiService.register(userData);
      
      enqueueSnackbar('Registration successful! Setting up your workspace...', {
        variant: 'success',
      });

      // Auto-login after registration (this will trigger organization auto-creation)
      await login({
        username_or_email: userData.email,
        password: userData.password,
      });
    } catch (error) {
      const authError = error as AuthError;
      enqueueSnackbar(authError.message || 'Registration failed', {
        variant: 'error',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      await AuthApiService.logout();
      setUser(null);
      
      enqueueSnackbar('Logged out successfully', {
        variant: 'info',
      });

      // Redirect to login page
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear user state even if API call fails
      setUser(null);
      router.push('/login');
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<void> => {
    try {
      await AuthApiService.refreshToken();
      // Token is refreshed automatically by the service
      // Get updated user info if needed
      if (user) {
        const updatedUser = await AuthApiService.getCurrentUser();
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, logout user
      await logout();
    }
  };

  // Refresh user function
  const refreshUser = async (): Promise<void> => {
    try {
      if (AuthApiService.isAuthenticated()) {
        const updatedUser = await AuthApiService.getCurrentUser();
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('User refresh failed:', error);
      // If refresh fails, logout user
      await logout();
    }
  };

  // Update user function (for organization context)
  const updateUser = (updatedUser: User): void => {
    setUser(updatedUser);
  };

  // Context value
  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    refreshUser,
    updateUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Extended auth context with retry capability
interface ExtendedAuthContextType extends AuthContextType {
  authError: string | null;
  retryAuth: () => void;
}

export function useAuthWithRetry(): ExtendedAuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthWithRetry must be used within an AuthProvider');
  }
  
  // Access the provider's internal state through a custom hook
  // This is a workaround since we can't modify AuthContextType interface
  const [authError] = useState<string | null>(null);
  const retryAuth = () => {
    window.location.reload();
  };
  
  return {
    ...context,
    authError,
    retryAuth,
  };
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// HOC for protected routes
interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  requireAdmin?: boolean;
  requireSystemAdmin?: boolean;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requireAuth = true,
  requireAdmin = false,
  requireSystemAdmin = false,
  fallback = null,
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const hasCheckedAuthRef = React.useRef(false);
  const [loadingTimeout, setLoadingTimeout] = React.useState(false);

  useEffect(() => {
    // Only run auth check once loading is complete and we haven't checked yet
    if (!isLoading && !hasCheckedAuthRef.current) {
      hasCheckedAuthRef.current = true;
      
      if (requireAuth && !isAuthenticated) {
        console.log('🔒 Not authenticated, redirecting to login...');
        router.push('/login');
        return;
      }

      if (requireSystemAdmin && user && ![UserRole.ADMIN, UserRole.SUPERADMIN].includes(user.role)) {
        console.log('🚫 Insufficient system admin permissions, redirecting to home...');
        router.push('/');
        return;
      }

      if (requireAdmin && user && ![UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.ORGANIZATION_ADMIN].includes(user.role)) {
        console.log('🚫 Insufficient admin permissions, redirecting to home...');
        router.push('/');
        return;
      }
    }
  }, [isAuthenticated, isLoading, requireAuth, requireAdmin, requireSystemAdmin, user, router]);

  // Set timeout for loading state
  useEffect(() => {
    if (isLoading) {
      const timer = setTimeout(() => {
        setLoadingTimeout(true);
      }, 8000); // 8 seconds

      return () => clearTimeout(timer);
    }
    // Reset timeout when not loading
    return () => setLoadingTimeout(false);
  }, [isLoading]);

  // Show enhanced loading state
  if (isLoading) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: 3,
          p: 3,
        }}
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" color="text.secondary">
          {loadingTimeout ? 'Still loading...' : 'Verifying authentication...'}
        </Typography>
        {loadingTimeout && (
          <Alert severity="warning" sx={{ maxWidth: 500 }}>
            <Typography variant="body2" gutterBottom>
              Authentication is taking longer than expected.
            </Typography>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={() => window.location.reload()}
              sx={{ mt: 1 }}
            >
              Refresh Page
            </Button>
          </Alert>
        )}
      </Box>
    );
  }

  // Check authentication requirements
  if (requireAuth && !isAuthenticated) {
    return fallback || null;
  }

  // Check admin requirements with better error message
  if (requireAdmin && user && ![UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN].includes(user.role)) {
    return (
      fallback || (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            gap: 2,
            p: 3,
          }}
        >
          <Alert severity="error" sx={{ maxWidth: 500 }}>
            <Typography variant="h6" gutterBottom>
              Access Denied
            </Typography>
            <Typography variant="body2">
              You don&apos;t have permission to access this page. Admin privileges are required.
            </Typography>
            <Button
              variant="contained"
              onClick={() => router.push('/')}
              sx={{ mt: 2 }}
            >
              Go to Home
            </Button>
          </Alert>
        </Box>
      )
    );
  }

  return <>{children}</>;
}

// Hook for checking permissions
export function usePermissions() {
  const { user, isAuthenticated } = useAuth();

  const isAdmin = user?.role === UserRole.ADMIN;
  const isOrgAdmin = user?.role === UserRole.ORGANIZATION_ADMIN;
  const hasAdminAccess = isAdmin || isOrgAdmin;

  return {
    isAuthenticated,
    isAdmin,
    isOrgAdmin,
    hasAdminAccess,
    user,
  };
}

export default AuthContext;
