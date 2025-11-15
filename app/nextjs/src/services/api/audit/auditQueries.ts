/**
 * React Query Hooks for Audit API Integration
 *
 * Provides enterprise-grade audit trail query hooks with:
 * - Automatic caching and background refetching
 * - Optimistic updates and error recovery
 * - Real-time data synchronization
 * - Infinite scrolling for large datasets
 */

import {
  useQuery,
  useMutation,
  useInfiniteQuery,
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
  UseInfiniteQueryOptions,
} from '@tanstack/react-query';
import { useCallback } from 'react';

import { auditApi } from './auditApi';
import { queryKeys } from '../../core/queryClient';
import {
  AuditLog,
  AuditFilters,
  AuditStats,
  ComplianceExportRequest,
  ComplianceExportResponse,
  UserAuditTrailEntry,
  SecurityEvent,
  ActionType,
  ResourceType,
  ComplianceTag,
} from './auditTypes';

// Hook options type helpers
type QueryOptions<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;
type MutationOptions<TData, TVariables> = UseMutationOptions<TData, Error, TVariables>;

/**
 * Hook for fetching audit logs with advanced filtering
 */
export const useAuditLogs = (
  filters: Partial<AuditFilters> = {},
  options?: QueryOptions<AuditLog[]>
) => {
  return useQuery({
    queryKey: queryKeys.audit.logs(filters),
    queryFn: () => auditApi.getAuditLogs(filters),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute
    ...options,
  });
};

/**
 * Hook for infinite scrolling audit logs
 */
export const useInfiniteAuditLogs = (
  filters: Omit<Partial<AuditFilters>, 'offset'> = {},
  options?: Omit<UseInfiniteQueryOptions<AuditLog[]>, 'queryKey' | 'queryFn' | 'getNextPageParam'>
) => {
  return useInfiniteQuery({
    queryKey: queryKeys.audit.logs(filters),
    queryFn: ({ pageParam = 0 }) =>
      auditApi.getAuditLogs({ ...filters, offset: pageParam }),
    getNextPageParam: (lastPage, allPages) => {
      const limit = filters.limit || 50;
      if (lastPage.length < limit) return undefined;
      return allPages.length * limit;
    },
    staleTime: 30000,
    ...options,
  });
};

/**
 * Hook for fetching a specific audit log entry
 */
export const useAuditLog = (
  logId: string,
  options?: QueryOptions<AuditLog>
) => {
  return useQuery({
    queryKey: [...queryKeys.audit.all, 'log', logId],
    queryFn: () => auditApi.getAuditLog(logId),
    enabled: !!logId,
    staleTime: 300000, // 5 minutes (audit logs are immutable)
    ...options,
  });
};

/**
 * Hook for fetching audit statistics
 */
export const useAuditStats = (
  organizationId?: string,
  days: number = 30,
  options?: QueryOptions<AuditStats>
) => {
  return useQuery({
    queryKey: queryKeys.audit.stats(organizationId),
    queryFn: () => auditApi.getAuditStats(organizationId, days),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
};

/**
 * Hook for fetching security events
 */
export const useSecurityEvents = (
  organizationId?: string,
  days: number = 7,
  options?: QueryOptions<SecurityEvent[]>
) => {
  return useQuery({
    queryKey: queryKeys.audit.securityEvents({ organizationId, days }),
    queryFn: () => auditApi.getSecurityEvents(organizationId, days),
    staleTime: 30000, // 30 seconds (security events are time-sensitive)
    refetchInterval: 30000, // 30 seconds
    ...options,
  });
};

/**
 * Hook for fetching user audit trail
 */
export const useUserAuditTrail = (
  userId: string,
  days: number = 30,
  options?: QueryOptions<UserAuditTrailEntry[]>
) => {
  return useQuery({
    queryKey: queryKeys.audit.userTrail(userId),
    queryFn: () => auditApi.getUserAuditTrail(userId, days),
    enabled: !!userId,
    staleTime: 60000, // 1 minute
    ...options,
  });
};

/**
 * Hook for fetching action types
 */
export const useActionTypes = (options?: QueryOptions<{ value: string; name: string }[]>) => {
  return useQuery({
    queryKey: [...queryKeys.audit.all, 'action-types'],
    queryFn: () => auditApi.getActionTypes(),
    staleTime: 3600000, // 1 hour (rarely changes)
    gcTime: 3600000, // 1 hour
    ...options,
  });
};

/**
 * Hook for fetching resource types
 */
export const useResourceTypes = (options?: QueryOptions<{ value: string; name: string }[]>) => {
  return useQuery({
    queryKey: [...queryKeys.audit.all, 'resource-types'],
    queryFn: () => auditApi.getResourceTypes(),
    staleTime: 3600000, // 1 hour
    gcTime: 3600000,
    ...options,
  });
};

/**
 * Hook for fetching compliance tags
 */
export const useComplianceTags = (options?: QueryOptions<{ value: string; name: string }[]>) => {
  return useQuery({
    queryKey: [...queryKeys.audit.all, 'compliance-tags'],
    queryFn: () => auditApi.getComplianceTags(),
    staleTime: 3600000, // 1 hour
    gcTime: 3600000,
    ...options,
  });
};

/**
 * Hook for audit logs count (for pagination)
 */
export const useAuditLogsCount = (
  filters: Partial<AuditFilters> = {},
  options?: QueryOptions<number>
) => {
  return useQuery({
    queryKey: [...queryKeys.audit.logs(filters), 'count'],
    queryFn: () => auditApi.getAuditLogsCount(filters),
    staleTime: 60000, // 1 minute
    ...options,
  });
};

/**
 * Mutation hook for exporting compliance data
 */
export const useExportComplianceData = (
  options?: MutationOptions<ComplianceExportResponse, ComplianceExportRequest>
) => {
  return useMutation({
    mutationFn: (request: ComplianceExportRequest) =>
      auditApi.exportComplianceData(request),
    ...options,
  });
};

/**
 * Mutation hook for downloading CSV exports
 */
export const useExportComplianceCSV = (
  options?: MutationOptions<Blob, ComplianceExportRequest>
) => {
  return useMutation({
    mutationFn: (request: ComplianceExportRequest) =>
      auditApi.exportComplianceCSV(request),
    onSuccess: (blob, variables) => {
      // Automatically trigger download
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-${variables.compliance_framework}-${Date.now()}.csv`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
    ...options,
  });
};

/**
 * Mutation hook for downloading audit reports
 */
export const useDownloadAuditReport = (
  options?: MutationOptions<void, { format: 'csv' | 'json' | 'xlsx'; filters: Partial<AuditFilters> }>
) => {
  return useMutation({
    mutationFn: ({ format, filters }) =>
      auditApi.downloadAuditReport(format, filters),
    ...options,
  });
};

/**
 * Mutation hook for cleaning up expired logs (admin only)
 */
export const useCleanupExpiredLogs = (
  options?: MutationOptions<{ message: string; status: string }, void>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => auditApi.cleanupExpiredLogs(),
    onSuccess: () => {
      // Invalidate all audit queries after cleanup
      queryClient.invalidateQueries({ queryKey: queryKeys.audit.all });
    },
    ...options,
  });
};

/**
 * Hook for real-time security events streaming
 */
export const useSecurityEventsStream = (
  organizationId?: string,
  enabled: boolean = true
) => {
  const queryClient = useQueryClient();

  const startStream = useCallback(() => {
    if (!enabled) return () => {};

    return auditApi.streamSecurityEvents(
      (event: SecurityEvent) => {
        // Update the security events query cache with the new event
        const queryKey = queryKeys.audit.securityEvents({ organizationId });
        queryClient.setQueryData(queryKey, (oldData: SecurityEvent[] | undefined) => {
          if (!oldData) return [event];
          return [event, ...oldData].slice(0, 100); // Keep only last 100 events
        });

        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: queryKeys.audit.stats(organizationId) });
      },
      (error: Error) => {
        console.error('Security events stream error:', error);
        // Could emit a toast notification here
      },
      organizationId
    );
  }, [queryClient, organizationId, enabled]);

  return {
    startStream,
  };
};

/**
 * Hook for searching audit logs
 */
export const useSearchAuditLogs = (
  query: string,
  filters: Partial<AuditFilters> = {},
  options?: QueryOptions<AuditLog[]>
) => {
  return useQuery({
    queryKey: [...queryKeys.audit.all, 'search', query, filters],
    queryFn: () => auditApi.searchAuditLogs(query, filters),
    enabled: query.length >= 3, // Only search with 3+ characters
    staleTime: 30000,
    ...options,
  });
};

/**
 * Custom hook for audit log management with common operations
 */
export const useAuditLogManager = (organizationId?: string) => {
  const queryClient = useQueryClient();

  const refreshAuditLogs = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: queryKeys.audit.logs() });
  }, [queryClient]);

  const refreshSecurityEvents = useCallback(() => {
    queryClient.invalidateQueries({
      queryKey: queryKeys.audit.securityEvents({ organizationId })
    });
  }, [queryClient, organizationId]);

  const refreshStats = useCallback(() => {
    queryClient.invalidateQueries({
      queryKey: queryKeys.audit.stats(organizationId)
    });
  }, [queryClient, organizationId]);

  const clearCache = useCallback(() => {
    queryClient.removeQueries({ queryKey: queryKeys.audit.all });
  }, [queryClient]);

  return {
    refreshAuditLogs,
    refreshSecurityEvents,
    refreshStats,
    clearCache,
  };
};

/**
 * Hook for prefetching audit data (for performance optimization)
 */
export const usePrefetchAuditData = () => {
  const queryClient = useQueryClient();

  const prefetchAuditLogs = useCallback(async (filters: Partial<AuditFilters> = {}) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.audit.logs(filters),
      queryFn: () => auditApi.getAuditLogs(filters),
      staleTime: 30000,
    });
  }, [queryClient]);

  const prefetchAuditStats = useCallback(async (organizationId?: string) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.audit.stats(organizationId),
      queryFn: () => auditApi.getAuditStats(organizationId),
      staleTime: 60000,
    });
  }, [queryClient]);

  return {
    prefetchAuditLogs,
    prefetchAuditStats,
  };
};

export default {
  useAuditLogs,
  useInfiniteAuditLogs,
  useAuditLog,
  useAuditStats,
  useSecurityEvents,
  useUserAuditTrail,
  useActionTypes,
  useResourceTypes,
  useComplianceTags,
  useAuditLogsCount,
  useExportComplianceData,
  useExportComplianceCSV,
  useDownloadAuditReport,
  useCleanupExpiredLogs,
  useSecurityEventsStream,
  useSearchAuditLogs,
  useAuditLogManager,
  usePrefetchAuditData,
};