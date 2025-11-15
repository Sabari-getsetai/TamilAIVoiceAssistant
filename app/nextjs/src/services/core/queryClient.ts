/**
 * Enhanced React Query Configuration for Enterprise Tamil AI Voice Assistant
 *
 * Features:
 * - Optimized cache settings for enterprise performance
 * - Error retry logic with exponential backoff
 * - Background refetching for real-time data synchronization
 * - Mutation error handling and recovery
 */

import { QueryClient, QueryClientConfig, MutationCache } from '@tanstack/react-query';

/**
 * Enhanced Query Client configuration for enterprise applications
 */
export const queryClientConfig: QueryClientConfig = {
  defaultOptions: {
    queries: {
      // Cache configuration
      staleTime: 5 * 60 * 1000, // 5 minutes - data is fresh for 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes - garbage collect after 10 minutes

      // Retry configuration with exponential backoff
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        // Retry up to 3 times for server errors and network issues
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Max 30s delay

      // Background refetching for real-time sync
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      refetchIntervalInBackground: false,

      // Network mode configuration
      networkMode: 'online',
    },
    mutations: {
      retry: 1, // Retry mutations once on failure
      networkMode: 'online',
    },
  },

  // Global mutation error handling
  mutationCache: new MutationCache({
    onError: (error, variables, context, mutation) => {
      console.error('Mutation error:', {
        error,
        variables,
        mutationKey: mutation.options.mutationKey,
      });

      // TODO: Integrate with global error handling system
      // TODO: Send error to audit service for enterprise monitoring
    },
  }),
};

/**
 * Create and configure the query client for enterprise use
 */
export function createQueryClient(): QueryClient {
  return new QueryClient(queryClientConfig);
}

/**
 * Singleton query client instance for use across the application
 */
export const queryClient = createQueryClient();

/**
 * Query key factory for consistent cache key generation
 */
export const queryKeys = {
  // Authentication queries
  auth: {
    all: ['auth'] as const,
    currentUser: () => [...queryKeys.auth.all, 'currentUser'] as const,
    profile: (userId: string) => [...queryKeys.auth.all, 'profile', userId] as const,
  },

  // Audit trail queries
  audit: {
    all: ['audit'] as const,
    logs: (filters?: Record<string, any>) => [...queryKeys.audit.all, 'logs', filters] as const,
    stats: (organizationId?: string) => [...queryKeys.audit.all, 'stats', organizationId] as const,
    securityEvents: (filters?: Record<string, any>) => [...queryKeys.audit.all, 'security-events', filters] as const,
    userTrail: (userId: string) => [...queryKeys.audit.all, 'user-trail', userId] as const,
  },

  // Organization queries
  organizations: {
    all: ['organizations'] as const,
    list: (filters?: Record<string, any>) => [...queryKeys.organizations.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.organizations.all, 'detail', id] as const,
    members: (id: string) => [...queryKeys.organizations.all, 'members', id] as const,
    invitations: (id: string) => [...queryKeys.organizations.all, 'invitations', id] as const,
  },

  // Session queries
  sessions: {
    all: ['sessions'] as const,
    list: (filters?: Record<string, any>) => [...queryKeys.sessions.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.sessions.all, 'detail', id] as const,
    analytics: (filters?: Record<string, any>) => [...queryKeys.sessions.all, 'analytics', filters] as const,
  },

  // Microservice queries
  microservices: {
    all: ['microservices'] as const,
    services: () => [...queryKeys.microservices.all, 'services'] as const,
    health: (serviceId?: string) => [...queryKeys.microservices.all, 'health', serviceId] as const,
    registry: () => [...queryKeys.microservices.all, 'registry'] as const,
    circuitBreakers: () => [...queryKeys.microservices.all, 'circuit-breakers'] as const,
  },

  // Document queries
  documents: {
    all: ['documents'] as const,
    list: (filters?: Record<string, any>) => [...queryKeys.documents.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.documents.all, 'detail', id] as const,
    content: (id: string) => [...queryKeys.documents.all, 'content', id] as const,
  },
} as const;

/**
 * Utility functions for query invalidation
 */
export const invalidateQueries = {
  // Invalidate all auth-related queries
  auth: () => queryClient.invalidateQueries({ queryKey: queryKeys.auth.all }),

  // Invalidate all audit-related queries
  audit: () => queryClient.invalidateQueries({ queryKey: queryKeys.audit.all }),

  // Invalidate organization queries
  organizations: () => queryClient.invalidateQueries({ queryKey: queryKeys.organizations.all }),

  // Invalidate session queries
  sessions: () => queryClient.invalidateQueries({ queryKey: queryKeys.sessions.all }),

  // Invalidate microservice queries
  microservices: () => queryClient.invalidateQueries({ queryKey: queryKeys.microservices.all }),

  // Invalidate document queries
  documents: () => queryClient.invalidateQueries({ queryKey: queryKeys.documents.all }),

  // Invalidate everything (nuclear option)
  all: () => queryClient.invalidateQueries(),
};

/**
 * Cache utilities for manual cache management
 */
export const cacheUtils = {
  // Set data in cache manually
  setQueryData: <T>(queryKey: any[], data: T) => {
    queryClient.setQueryData(queryKey, data);
  },

  // Get data from cache
  getQueryData: <T>(queryKey: any[]): T | undefined => {
    return queryClient.getQueryData(queryKey);
  },

  // Remove specific query from cache
  removeQueries: (queryKey: any[]) => {
    queryClient.removeQueries({ queryKey });
  },

  // Clear all cache
  clear: () => {
    queryClient.clear();
  },
};

export default queryClient;