/**
 * React Query hooks for System Admin API
 *
 * Provides easy-to-use hooks for system administration functionality
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import {
  systemAdminApi,
  type SystemDocument,
  type SystemUser,
  type SystemOrganization,
  type SystemDocumentStats,
  type SystemInfo,
} from '@/services/api/systemAdminApi';

// System Documents Hooks
export const useSystemDocuments = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: ['systemDocuments', skip, limit],
    queryFn: () => systemAdminApi.documents.getAllDocuments(skip, limit),
    staleTime: 30000, // 30 seconds
  });
};

export const useSystemDocument = (documentId: string) => {
  return useQuery({
    queryKey: ['systemDocument', documentId],
    queryFn: () => systemAdminApi.documents.getDocument(documentId),
    enabled: !!documentId,
  });
};

export const useSystemDocumentStats = () => {
  return useQuery({
    queryKey: ['systemDocumentStats'],
    queryFn: systemAdminApi.documents.getStats,
    staleTime: 60000, // 1 minute
  });
};

export const useDeleteSystemDocument = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: systemAdminApi.documents.deleteDocument,
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['systemDocuments'] });
      queryClient.invalidateQueries({ queryKey: ['systemDocumentStats'] });
      queryClient.removeQueries({ queryKey: ['systemDocument', documentId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('System document delete error:', error);
      enqueueSnackbar('Failed to delete document', { variant: 'error' });
    },
  });
};

// System Users Hooks
export const useSystemUsers = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: ['systemUsers', skip, limit],
    queryFn: () => systemAdminApi.users.getAllUsers(skip, limit),
    staleTime: 60000, // 1 minute
  });
};

export const useSystemUser = (userId: string) => {
  return useQuery({
    queryKey: ['systemUser', userId],
    queryFn: () => systemAdminApi.users.getUser(userId),
    enabled: !!userId,
  });
};

export const useUpdateSystemUser = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: Partial<SystemUser> }) =>
      systemAdminApi.users.updateUser(userId, updates),
    onSuccess: (data, { userId }) => {
      queryClient.invalidateQueries({ queryKey: ['systemUsers'] });
      queryClient.invalidateQueries({ queryKey: ['systemUser', userId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('User update error:', error);
      enqueueSnackbar('Failed to update user', { variant: 'error' });
    },
  });
};

export const useSetUserActiveStatus = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      systemAdminApi.users.setUserActiveStatus(userId, isActive),
    onSuccess: (data, { userId }) => {
      queryClient.invalidateQueries({ queryKey: ['systemUsers'] });
      queryClient.invalidateQueries({ queryKey: ['systemUser', userId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('User status change error:', error);
      enqueueSnackbar('Failed to change user status', { variant: 'error' });
    },
  });
};

// System Organizations Hooks
export const useSystemOrganizations = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: ['systemOrganizations', skip, limit],
    queryFn: () => systemAdminApi.organizations.getAllOrganizations(skip, limit),
    staleTime: 60000, // 1 minute
  });
};

export const useSystemOrganization = (organizationId: string) => {
  return useQuery({
    queryKey: ['systemOrganization', organizationId],
    queryFn: () => systemAdminApi.organizations.getOrganization(organizationId),
    enabled: !!organizationId,
  });
};

export const useUpdateSystemOrganization = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({ organizationId, updates }: { organizationId: string; updates: Partial<SystemOrganization> }) =>
      systemAdminApi.organizations.updateOrganization(organizationId, updates),
    onSuccess: (data, { organizationId }) => {
      queryClient.invalidateQueries({ queryKey: ['systemOrganizations'] });
      queryClient.invalidateQueries({ queryKey: ['systemOrganization', organizationId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Organization update error:', error);
      enqueueSnackbar('Failed to update organization', { variant: 'error' });
    },
  });
};

export const useSetOrganizationActiveStatus = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: ({ organizationId, isActive }: { organizationId: string; isActive: boolean }) =>
      systemAdminApi.organizations.setOrganizationActiveStatus(organizationId, isActive),
    onSuccess: (data, { organizationId }) => {
      queryClient.invalidateQueries({ queryKey: ['systemOrganizations'] });
      queryClient.invalidateQueries({ queryKey: ['systemOrganization', organizationId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Organization status change error:', error);
      enqueueSnackbar('Failed to change organization status', { variant: 'error' });
    },
  });
};

// System Info Hooks
export const useSystemInfo = () => {
  return useQuery({
    queryKey: ['systemInfo'],
    queryFn: systemAdminApi.info.getSystemInfo,
    staleTime: 300000, // 5 minutes
    refetchInterval: 300000, // Refetch every 5 minutes
  });
};

export const useSystemAnalytics = (timeRange = '30d') => {
  return useQuery({
    queryKey: ['systemAnalytics', timeRange],
    queryFn: () => systemAdminApi.info.getAnalytics(timeRange),
    staleTime: 600000, // 10 minutes
  });
};

export const useSystemHealthMetrics = () => {
  return useQuery({
    queryKey: ['systemHealthMetrics'],
    queryFn: systemAdminApi.info.getHealthMetrics,
    staleTime: 60000, // 1 minute
    refetchInterval: 60000, // Refetch every minute
  });
};

// Combined hook for system admin dashboard data
export const useSystemAdminDashboard = () => {
  const systemInfo = useSystemInfo();
  const documentStats = useSystemDocumentStats();
  const healthMetrics = useSystemHealthMetrics();
  const users = useSystemUsers(0, 10); // Get first 10 users for overview
  const organizations = useSystemOrganizations(0, 10); // Get first 10 organizations for overview

  return {
    systemInfo,
    documentStats,
    healthMetrics,
    users,
    organizations,
    isLoading:
      systemInfo.isLoading ||
      documentStats.isLoading ||
      healthMetrics.isLoading ||
      users.isLoading ||
      organizations.isLoading,
    isError:
      systemInfo.isError ||
      documentStats.isError ||
      healthMetrics.isError ||
      users.isError ||
      organizations.isError,
    refetchAll: () => {
      systemInfo.refetch();
      documentStats.refetch();
      healthMetrics.refetch();
      users.refetch();
      organizations.refetch();
    },
  };
};

// Utility hook for system admin permissions check
export const useIsSystemAdmin = () => {
  // This would integrate with your auth context
  // For now, returning a placeholder
  return {
    isSystemAdmin: true, // Replace with actual auth check
    isLoading: false,
  };
};