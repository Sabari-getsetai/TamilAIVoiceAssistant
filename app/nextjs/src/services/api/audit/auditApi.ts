/**
 * Audit API Client for Enterprise Tamil AI Voice Assistant
 *
 * Provides enterprise-grade audit trail API integration with:
 * - Type-safe API calls with Zod validation
 * - Comprehensive error handling
 * - Automatic retry logic
 * - Request correlation tracking
 */

import { ApiClient } from '../../core/apiClient';
import EnhancedTokenStorage from '../../core/tokenStorage';
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
  AuditLogSchema,
  AuditStatsSchema,
  ComplianceExportResponseSchema,
  UserAuditTrailEntrySchema,
  SecurityEventSchema,
} from './auditTypes';
import { z } from 'zod';

/**
 * Enhanced Audit API Client with enterprise features
 */
export class AuditApiClient {
  private apiClient: ApiClient;
  private readonly baseURL: string;

  constructor(baseURL: string = '/api/v1/audit') {
    this.baseURL = baseURL;
    this.apiClient = new ApiClient(
      '', // Base URL handled by proxy
      EnhancedTokenStorage,
      30000 // 30 second timeout for audit operations
    );
  }

  /**
   * Get audit logs with advanced filtering
   */
  async getAuditLogs(filters: Partial<AuditFilters> = {}): Promise<AuditLog[]> {
    const params = new URLSearchParams();

    // Add filter parameters
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.organization_id) params.append('organization_id', filters.organization_id);
    if (filters.action_types?.length) {
      params.append('action_types', filters.action_types.join(','));
    }
    if (filters.resource_types?.length) {
      params.append('resource_types', filters.resource_types.join(','));
    }
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.ip_address) params.append('ip_address', filters.ip_address);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.compliance_tags?.length) {
      params.append('compliance_tags', filters.compliance_tags.join(','));
    }
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());

    const url = `${this.baseURL}/logs${params.toString() ? `?${params.toString()}` : ''}`;

    return this.apiClient.get(
      url,
      {},
      z.array(AuditLogSchema)
    );
  }

  /**
   * Get specific audit log entry by ID
   */
  async getAuditLog(logId: string): Promise<AuditLog> {
    return this.apiClient.get(
      `${this.baseURL}/logs/${logId}`,
      {},
      AuditLogSchema
    );
  }

  /**
   * Get audit statistics and analytics
   */
  async getAuditStats(
    organizationId?: string,
    days: number = 30
  ): Promise<AuditStats> {
    const params = new URLSearchParams();
    if (organizationId) params.append('organization_id', organizationId);
    params.append('days', days.toString());

    const url = `${this.baseURL}/stats?${params.toString()}`;

    return this.apiClient.get(
      url,
      {},
      AuditStatsSchema
    );
  }

  /**
   * Get security events for monitoring
   */
  async getSecurityEvents(
    organizationId?: string,
    days: number = 7
  ): Promise<SecurityEvent[]> {
    const params = new URLSearchParams();
    if (organizationId) params.append('organization_id', organizationId);
    params.append('days', days.toString());

    const url = `${this.baseURL}/security-events?${params.toString()}`;

    return this.apiClient.get(
      url,
      {},
      z.array(SecurityEventSchema)
    );
  }

  /**
   * Get complete audit trail for a specific user
   */
  async getUserAuditTrail(
    userId: string,
    days: number = 30
  ): Promise<UserAuditTrailEntry[]> {
    const params = new URLSearchParams();
    params.append('days', days.toString());

    const url = `${this.baseURL}/user/${userId}/trail?${params.toString()}`;

    return this.apiClient.get(
      url,
      {},
      z.array(UserAuditTrailEntrySchema)
    );
  }

  /**
   * Export compliance data
   */
  async exportComplianceData(
    request: ComplianceExportRequest
  ): Promise<ComplianceExportResponse> {
    return this.apiClient.post(
      `${this.baseURL}/export/compliance`,
      request,
      {},
      ComplianceExportResponseSchema
    );
  }

  /**
   * Export compliance data as CSV file download
   */
  async exportComplianceCSV(request: ComplianceExportRequest): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/export/compliance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${EnhancedTokenStorage.getAccessToken()}`,
      },
      body: JSON.stringify({
        ...request,
        format: 'csv',
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Trigger cleanup of expired audit logs (admin only)
   */
  async cleanupExpiredLogs(): Promise<{ message: string; status: string }> {
    return this.apiClient.delete(
      `${this.baseURL}/cleanup`,
      {},
      z.object({
        message: z.string(),
        status: z.string(),
      })
    );
  }

  /**
   * Get available action types for filtering
   */
  async getActionTypes(): Promise<{ value: string; name: string }[]> {
    return this.apiClient.get(
      `${this.baseURL}/action-types`,
      {},
      z.array(z.object({
        value: z.string(),
        name: z.string(),
      }))
    );
  }

  /**
   * Get available resource types for filtering
   */
  async getResourceTypes(): Promise<{ value: string; name: string }[]> {
    return this.apiClient.get(
      `${this.baseURL}/resource-types`,
      {},
      z.array(z.object({
        value: z.string(),
        name: z.string(),
      }))
    );
  }

  /**
   * Get available compliance tags for filtering
   */
  async getComplianceTags(): Promise<{ value: string; name: string }[]> {
    return this.apiClient.get(
      `${this.baseURL}/compliance-tags`,
      {},
      z.array(z.object({
        value: z.string(),
        name: z.string(),
      }))
    );
  }

  /**
   * Stream real-time security events (Server-Sent Events)
   */
  streamSecurityEvents(
    onEvent: (event: SecurityEvent) => void,
    onError: (error: Error) => void,
    organizationId?: string
  ): () => void {
    const params = new URLSearchParams();
    if (organizationId) params.append('organization_id', organizationId);

    const url = `${this.baseURL}/security-events/stream?${params.toString()}`;
    const token = EnhancedTokenStorage.getAccessToken();

    const eventSource = new EventSource(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    } as any);

    eventSource.onmessage = (event) => {
      try {
        const securityEvent = SecurityEventSchema.parse(JSON.parse(event.data));
        onEvent(securityEvent);
      } catch (error) {
        console.error('Failed to parse security event:', error);
        onError(new Error('Failed to parse security event'));
      }
    };

    eventSource.onerror = (error) => {
      console.error('Security events stream error:', error);
      onError(new Error('Security events stream connection failed'));
    };

    // Return cleanup function
    return () => {
      eventSource.close();
    };
  }

  /**
   * Search audit logs with text query
   */
  async searchAuditLogs(
    query: string,
    filters: Partial<AuditFilters> = {}
  ): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    params.append('query', query);

    // Add other filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          params.append(key, value.join(','));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    const url = `${this.baseURL}/search?${params.toString()}`;

    return this.apiClient.get(
      url,
      {},
      z.array(AuditLogSchema)
    );
  }

  /**
   * Get audit logs count for pagination
   */
  async getAuditLogsCount(filters: Partial<AuditFilters> = {}): Promise<number> {
    const params = new URLSearchParams();

    // Add filter parameters (same as getAuditLogs)
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.organization_id) params.append('organization_id', filters.organization_id);
    if (filters.action_types?.length) {
      params.append('action_types', filters.action_types.join(','));
    }
    if (filters.resource_types?.length) {
      params.append('resource_types', filters.resource_types.join(','));
    }
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.ip_address) params.append('ip_address', filters.ip_address);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.compliance_tags?.length) {
      params.append('compliance_tags', filters.compliance_tags.join(','));
    }

    const url = `${this.baseURL}/logs/count${params.toString() ? `?${params.toString()}` : ''}`;

    const response = await this.apiClient.get(
      url,
      {},
      z.object({ count: z.number() })
    );

    return response.count;
  }

  /**
   * Download audit report as file
   */
  async downloadAuditReport(
    format: 'csv' | 'json' | 'xlsx',
    filters: Partial<AuditFilters> = {}
  ): Promise<void> {
    const params = new URLSearchParams();
    params.append('format', format);

    // Add filter parameters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          params.append(key, value.join(','));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    const url = `${this.baseURL}/export?${params.toString()}`;
    const token = EnhancedTokenStorage.getAccessToken();

    // Create download link
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-report-${new Date().toISOString().split('T')[0]}.${format}`;
    link.style.display = 'none';

    // Set authorization header (this is a bit tricky with direct downloads)
    // We'll use fetch instead for better control
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);

    link.href = downloadUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(downloadUrl), 100);
  }
}

// Create singleton instance
export const auditApi = new AuditApiClient();

export default auditApi;