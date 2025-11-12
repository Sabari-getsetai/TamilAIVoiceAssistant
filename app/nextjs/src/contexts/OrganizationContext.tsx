'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { organizationApi } from '@/services/api/organizationApi';
import type {
  Organization,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  OrganizationContextType
} from '@/types/organization';


const OrganizationContext = createContext<OrganizationContextType | null>(null);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated, updateUser } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false); // Track initial load completion

  // Computed properties
  const hasOrganizations = organizations.length > 0;
  // Prevent premature evaluation during loading race conditions
  const needsOrganizationSetup = isAuthenticated && !hasOrganizations && !isLoading && hasLoaded;

  // Load organizations when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      refreshOrganizations();
    } else {
      // Clear state when user logs out
      console.debug('[OrganizationContext] User logged out, clearing state');
      setOrganizations([]);
      setCurrentOrganization(null);
      setError(null);
      setHasLoaded(false);
    }
  }, [isAuthenticated, user?.id]);

  // Debug logging for needsOrganizationSetup evaluation
  useEffect(() => {
    console.debug('[OrganizationContext] State evaluation:', {
      isAuthenticated,
      hasOrganizations,
      isLoading,
      hasLoaded,
      needsOrganizationSetup,
      organizationCount: organizations.length
    });
  }, [isAuthenticated, hasOrganizations, isLoading, hasLoaded, needsOrganizationSetup]);

  // Update current organization when user's active_organization_id changes
  useEffect(() => {
    if (user?.active_organization_id && organizations.length > 0) {
      const current = organizations.find(org => org.id === user.active_organization_id);
      setCurrentOrganization(current || null);
    } else {
      setCurrentOrganization(null);
    }
  }, [user?.active_organization_id, organizations]);

  const refreshOrganizations = async () => {
    if (!isAuthenticated) {
      console.debug('[OrganizationContext] Not authenticated, skipping organization load');
      return;
    }

    console.debug('[OrganizationContext] Starting organization load...');
    setIsLoading(true);
    setError(null);

    try {
      const userOrgs = await organizationApi.getUserOrganizations();
      console.debug('[OrganizationContext] Loaded organizations:', userOrgs.length);
      setOrganizations(userOrgs);

      // If user has no active organization but has organizations, set the first one
      if (!user?.active_organization_id && userOrgs.length > 0) {
        console.debug('[OrganizationContext] Auto-selecting first organization:', userOrgs[0].name);
        await switchOrganization(userOrgs[0].id);
      }

      // Mark as loaded after successful data fetch
      setHasLoaded(true);
      console.debug('[OrganizationContext] Organization load completed successfully');
    } catch (err: any) {
      console.error('[OrganizationContext] Failed to load organizations:', err);
      setError(err.response?.data?.detail || 'Failed to load organizations');
      // Still mark as loaded even on error to prevent infinite loading state
      setHasLoaded(true);
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = async (orgId: string) => {
    setError(null);

    try {
      await organizationApi.setActiveOrganization(orgId);

      // Update user's active_organization_id
      if (user) {
        const updatedUser = { ...user, active_organization_id: orgId };
        updateUser(updatedUser);
      }

      // Update current organization
      const newCurrent = organizations.find(org => org.id === orgId);
      setCurrentOrganization(newCurrent || null);
    } catch (err: any) {
      console.error('Failed to switch organization:', err);
      setError(err.response?.data?.detail || 'Failed to switch organization');
      throw err;
    }
  };

  const createOrganization = async (data: CreateOrganizationRequest): Promise<Organization> => {
    setError(null);

    try {
      const newOrg = await organizationApi.createOrganization(data);

      // Add to organizations list
      setOrganizations(prev => [...prev, newOrg]);

      // Auto-switch to new organization
      await switchOrganization(newOrg.id);

      return newOrg;
    } catch (err: any) {
      console.error('Failed to create organization:', err);
      setError(err.response?.data?.detail || 'Failed to create organization');
      throw err;
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    isLoading,
    error,
    hasOrganizations,
    needsOrganizationSetup,
    switchOrganization,
    createOrganization,
    refreshOrganizations,
    clearError,
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within OrganizationProvider');
  }
  return context;
}

export default OrganizationContext;