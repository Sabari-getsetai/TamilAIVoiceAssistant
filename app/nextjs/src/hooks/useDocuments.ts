import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AdminApiService, handleApiError } from '../services/api/adminApi';
import type { DocumentsResponse, DocumentDetailResponse, ReindexResponse } from '../types';

export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: AdminApiService.getDocuments,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: AdminApiService.deleteDocument,
    onSuccess: () => {
      // Invalidate and refetch documents
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (error) => {
      console.error('Delete document error:', handleApiError(error));
    },
  });
};

export const useGetDocument = (docId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['document', docId],
    queryFn: () => AdminApiService.getDocument(docId),
    enabled: enabled && !!docId, // Only fetch if enabled and docId exists
    staleTime: 30000, // 30 seconds
  });
};

export const useReindexDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: AdminApiService.reindexDocument,
    onSuccess: () => {
      // Invalidate and refetch documents and stats
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (error) => {
      console.error('Reindex document error:', handleApiError(error));
    },
  });
};

export const useRefreshDocuments = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: ['documents'] });
  };
};
