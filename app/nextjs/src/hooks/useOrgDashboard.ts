/**
 * React Query hooks for Organization Dashboard API
 *
 * Provides easy-to-use hooks for organization dashboard functionality
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import {
  orgDashboardApi,
  type OrgDocument,
  type OrgMember,
  type ProcessingRequest,
  type InviteMemberRequest,
  type ChangeRoleRequest,
  type UpdateSettingsRequest,
  type DocumentStats,
  type OrganizationSettings,
} from '@/services/api/orgDashboardApi';

// Organization Documents Hooks
export const useOrgDocuments = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: ['orgDocuments', skip, limit],
    queryFn: () => orgDashboardApi.documents.getDocuments(skip, limit),
    staleTime: 30000, // 30 seconds
    refetchInterval: 10000, // Refetch every 10 seconds to check processing status
  });
};

export const useOrgDocument = (documentId: string) => {
  return useQuery({
    queryKey: ['orgDocument', documentId],
    queryFn: () => orgDashboardApi.documents.getDocument(documentId),
    enabled: !!documentId,
  });
};

export const useOrgDocumentStats = () => {
  return useQuery({
    queryKey: ['orgDocumentStats'],
    queryFn: orgDashboardApi.documents.getStats,
    staleTime: 60000, // 1 minute
  });
};

export const useUploadOrgDocuments = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.documents.uploadDocuments,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgDocuments'] });
      queryClient.invalidateQueries({ queryKey: ['orgDocumentStats'] });
      enqueueSnackbar(`Successfully uploaded ${data.documents.length} documents`, {
        variant: 'success',
      });

      if (data.errors.length > 0) {
        enqueueSnackbar(`${data.errors.length} files failed to upload`, {
          variant: 'warning',
        });
      }
    },
    onError: (error) => {
      console.error('Upload error:', error);
      enqueueSnackbar('Failed to upload documents', { variant: 'error' });
    },
  });
};

export const useProcessOrgDocuments = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.documents.processDocuments,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgDocuments'] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Processing error:', error);
      enqueueSnackbar('Failed to start document processing', { variant: 'error' });
    },
  });
};

export const useDeleteOrgDocument = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.documents.deleteDocument,
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['orgDocuments'] });
      queryClient.invalidateQueries({ queryKey: ['orgDocumentStats'] });
      queryClient.removeQueries({ queryKey: ['orgDocument', documentId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Delete error:', error);
      enqueueSnackbar('Failed to delete document', { variant: 'error' });
    },
  });
};

export const useReprocessOrgDocument = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.documents.reprocessDocument,
    onSuccess: (data, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['orgDocuments'] });
      queryClient.invalidateQueries({ queryKey: ['orgDocument', documentId] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Reprocess error:', error);
      enqueueSnackbar('Failed to reprocess document', { variant: 'error' });
    },
  });
};

// Organization Members Hooks
export const useOrgMembers = () => {
  return useQuery({
    queryKey: ['orgMembers'],
    queryFn: orgDashboardApi.members.getMembers,
    staleTime: 60000, // 1 minute
  });
};

export const useInviteOrgMember = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.members.inviteMember,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgMembers'] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Invite error:', error);
      enqueueSnackbar('Failed to send invitation', { variant: 'error' });
    },
  });
};

export const useChangeOrgMemberRole = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.members.changeMemberRole,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgMembers'] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Role change error:', error);
      enqueueSnackbar('Failed to change member role', { variant: 'error' });
    },
  });
};

export const useRemoveOrgMember = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.members.removeMember,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgMembers'] });
      enqueueSnackbar(data.message, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Remove member error:', error);
      enqueueSnackbar('Failed to remove member', { variant: 'error' });
    },
  });
};

// Organization Settings Hooks
export const useOrgSettings = () => {
  return useQuery({
    queryKey: ['orgSettings'],
    queryFn: orgDashboardApi.settings.getSettings,
    staleTime: 300000, // 5 minutes
  });
};

export const useUpdateOrgSettings = () => {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  return useMutation({
    mutationFn: orgDashboardApi.settings.updateSettings,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orgSettings'] });
      enqueueSnackbar(`Updated ${data.updated_fields.join(', ')}`, { variant: 'success' });
    },
    onError: (error) => {
      console.error('Settings update error:', error);
      enqueueSnackbar('Failed to update organization settings', { variant: 'error' });
    },
  });
};

// Combined hook for organization dashboard data
export const useOrgDashboardData = () => {
  const documents = useOrgDocuments();
  const stats = useOrgDocumentStats();
  const members = useOrgMembers();
  const settings = useOrgSettings();

  return {
    documents,
    stats,
    members,
    settings,
    isLoading: documents.isLoading || stats.isLoading || members.isLoading || settings.isLoading,
    isError: documents.isError || stats.isError || members.isError || settings.isError,
    refetchAll: () => {
      documents.refetch();
      stats.refetch();
      members.refetch();
      settings.refetch();
    },
  };
};