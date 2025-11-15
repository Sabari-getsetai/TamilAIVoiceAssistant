/**
 * Type definitions for Audit API Integration
 *
 * Matches the backend audit trail system types and provides
 * comprehensive TypeScript interfaces for the frontend
 */

import { z } from 'zod';

// Action types enum (matches backend)
export enum ActionType {
  // Authentication
  LOGIN = 'login',
  LOGOUT = 'logout',
  LOGIN_FAILED = 'login_failed',
  PASSWORD_RESET = 'password_reset',
  SUSPICIOUS_LOGIN = 'suspicious_login',

  // User management
  USER_CREATED = 'user_created',
  USER_UPDATED = 'user_updated',
  USER_DELETED = 'user_deleted',
  USER_INVITED = 'user_invited',
  USER_ACTIVATED = 'user_activated',
  USER_DEACTIVATED = 'user_deactivated',

  // Organization management
  ORGANIZATION_CREATED = 'organization_created',
  ORGANIZATION_UPDATED = 'organization_updated',
  ORGANIZATION_DELETED = 'organization_deleted',
  MEMBER_ADDED = 'member_added',
  MEMBER_REMOVED = 'member_removed',
  MEMBER_ROLE_CHANGED = 'member_role_changed',

  // Document management
  DOCUMENT_UPLOADED = 'document_uploaded',
  DOCUMENT_DOWNLOADED = 'document_downloaded',
  DOCUMENT_VIEWED = 'document_viewed',
  DOCUMENT_DELETED = 'document_deleted',
  DOCUMENT_SHARED = 'document_shared',

  // Session management
  SESSION_STARTED = 'session_started',
  SESSION_ENDED = 'session_ended',
  CONVERSATION_TURN = 'conversation_turn',

  // API access
  API_REQUEST = 'api_request',
  API_KEY_CREATED = 'api_key_created',
  API_KEY_DELETED = 'api_key_deleted',

  // System administration
  SYSTEM_CONFIG_CHANGED = 'system_config_changed',
  BACKUP_CREATED = 'backup_created',
  BACKUP_RESTORED = 'backup_restored',

  // Billing and subscriptions
  SUBSCRIPTION_CREATED = 'subscription_created',
  SUBSCRIPTION_CHANGED = 'subscription_changed',
  SUBSCRIPTION_CANCELLED = 'subscription_cancelled',
  PAYMENT_PROCESSED = 'payment_processed',
  PAYMENT_FAILED = 'payment_failed',

  // Security events
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
  UNAUTHORIZED_ACCESS = 'unauthorized_access',

  // Data compliance
  DATA_EXPORT_REQUESTED = 'data_export_requested',
  DATA_DELETION_REQUESTED = 'data_deletion_requested',
}

// Resource types enum
export enum ResourceType {
  USER = 'user',
  ORGANIZATION = 'organization',
  DOCUMENT = 'document',
  SESSION = 'session',
  API_KEY = 'api_key',
  SYSTEM = 'system',
  SUBSCRIPTION = 'subscription',
  PAYMENT = 'payment',
}

// Compliance framework tags
export enum ComplianceTag {
  GDPR = 'GDPR',
  SOC2 = 'SOC2',
  HIPAA = 'HIPAA',
  ISO27001 = 'ISO27001',
  PCI_DSS = 'PCI_DSS',
  CCPA = 'CCPA',
}

// Severity levels
export enum AuditSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// Base audit log entry schema
export const AuditLogSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid().nullable(),
  organization_id: z.string().uuid().nullable(),
  session_id: z.string().nullable(),
  action_type: z.nativeEnum(ActionType),
  resource_type: z.nativeEnum(ResourceType).nullable(),
  resource_id: z.string().uuid().nullable(),
  ip_address: z.string().ip().nullable(),
  user_agent: z.string().nullable(),
  endpoint: z.string().nullable(),
  http_method: z.string().nullable(),
  timestamp: z.string().datetime(),
  description: z.string().nullable(),
  severity: z.nativeEnum(AuditSeverity),
  compliance_tags: z.array(z.nativeEnum(ComplianceTag)),
  request_metadata: z.record(z.any()),
  response_status: z.string().nullable(),
  request_id: z.string().nullable(),
  is_security_event: z.boolean(),
});

export type AuditLog = z.infer<typeof AuditLogSchema>;

// Audit log filters
export const AuditFiltersSchema = z.object({
  user_id: z.string().uuid().optional(),
  organization_id: z.string().uuid().optional(),
  action_types: z.array(z.nativeEnum(ActionType)).optional(),
  resource_types: z.array(z.nativeEnum(ResourceType)).optional(),
  start_date: z.string().datetime().optional(),
  end_date: z.string().datetime().optional(),
  ip_address: z.string().optional(),
  severity: z.nativeEnum(AuditSeverity).optional(),
  compliance_tags: z.array(z.nativeEnum(ComplianceTag)).optional(),
  limit: z.number().min(1).max(1000).default(50),
  offset: z.number().min(0).default(0),
});

export type AuditFilters = z.infer<typeof AuditFiltersSchema>;

// Audit statistics response
export const AuditStatsSchema = z.object({
  total_events: z.number(),
  events_by_action: z.record(z.number()),
  events_by_severity: z.record(z.number()),
  security_events_count: z.number(),
  top_users: z.array(z.object({
    user_id: z.string(),
    event_count: z.number(),
  })),
  top_ip_addresses: z.array(z.object({
    ip_address: z.string(),
    event_count: z.number(),
  })),
  date_range: z.object({
    start_date: z.string().datetime(),
    end_date: z.string().datetime(),
  }),
});

export type AuditStats = z.infer<typeof AuditStatsSchema>;

// Compliance export request
export const ComplianceExportRequestSchema = z.object({
  compliance_framework: z.nativeEnum(ComplianceTag),
  organization_id: z.string().uuid().optional(),
  start_date: z.string().datetime().optional(),
  end_date: z.string().datetime().optional(),
  format: z.enum(['json', 'csv', 'xlsx']).default('json'),
  include_sensitive_data: z.boolean().default(false),
});

export type ComplianceExportRequest = z.infer<typeof ComplianceExportRequestSchema>;

// Compliance export response
export const ComplianceExportResponseSchema = z.object({
  compliance_framework: z.nativeEnum(ComplianceTag),
  export_date: z.string().datetime(),
  record_count: z.number(),
  data: z.array(z.record(z.any())),
});

export type ComplianceExportResponse = z.infer<typeof ComplianceExportResponseSchema>;

// User audit trail entry
export const UserAuditTrailEntrySchema = z.object({
  id: z.string().uuid(),
  action_type: z.nativeEnum(ActionType),
  resource_type: z.nativeEnum(ResourceType).nullable(),
  resource_id: z.string().uuid().nullable(),
  ip_address: z.string().ip().nullable(),
  timestamp: z.string().datetime(),
  description: z.string().nullable(),
  endpoint: z.string().nullable(),
  http_method: z.string().nullable(),
});

export type UserAuditTrailEntry = z.infer<typeof UserAuditTrailEntrySchema>;

// Security event entry
export const SecurityEventSchema = z.object({
  id: z.string().uuid(),
  action_type: z.nativeEnum(ActionType),
  user_id: z.string().uuid().nullable(),
  ip_address: z.string().ip().nullable(),
  user_agent: z.string().nullable(),
  timestamp: z.string().datetime(),
  description: z.string().nullable(),
  severity: z.nativeEnum(AuditSeverity),
  request_metadata: z.record(z.any()),
});

export type SecurityEvent = z.infer<typeof SecurityEventSchema>;

// Action type options for dropdowns
export const ActionTypeOptions = Object.values(ActionType).map(value => ({
  value,
  label: value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
}));

// Resource type options for dropdowns
export const ResourceTypeOptions = Object.values(ResourceType).map(value => ({
  value,
  label: value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
}));

// Compliance tag options for dropdowns
export const ComplianceTagOptions = Object.values(ComplianceTag).map(value => ({
  value,
  label: value,
}));

// Severity options for dropdowns
export const SeverityOptions = Object.values(AuditSeverity).map(value => ({
  value,
  label: value.replace(/\b\w/g, l => l.toUpperCase()),
}));

// Export format options
export const ExportFormatOptions = [
  { value: 'json', label: 'JSON' },
  { value: 'csv', label: 'CSV' },
  { value: 'xlsx', label: 'Excel' },
] as const;

// Default filter values
export const defaultAuditFilters: Partial<AuditFilters> = {
  limit: 50,
  offset: 0,
};

// Color mappings for UI
export const severityColors = {
  [AuditSeverity.LOW]: '#4caf50',      // Green
  [AuditSeverity.MEDIUM]: '#ff9800',   // Orange
  [AuditSeverity.HIGH]: '#f44336',     // Red
  [AuditSeverity.CRITICAL]: '#9c27b0', // Purple
} as const;

export const actionTypeColors = {
  [ActionType.LOGIN]: '#4caf50',
  [ActionType.LOGOUT]: '#2196f3',
  [ActionType.LOGIN_FAILED]: '#f44336',
  [ActionType.SUSPICIOUS_LOGIN]: '#9c27b0',
  [ActionType.USER_CREATED]: '#4caf50',
  [ActionType.USER_DELETED]: '#f44336',
  [ActionType.DOCUMENT_UPLOADED]: '#2196f3',
  [ActionType.DOCUMENT_DELETED]: '#f44336',
  [ActionType.UNAUTHORIZED_ACCESS]: '#9c27b0',
  [ActionType.RATE_LIMIT_EXCEEDED]: '#ff5722',
  // Add more as needed
} as const;

// Utility functions
export const formatActionType = (actionType: ActionType): string => {
  return actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export const formatResourceType = (resourceType: ResourceType | null): string => {
  if (!resourceType) return 'N/A';
  return resourceType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export const getSeverityColor = (severity: AuditSeverity): string => {
  return severityColors[severity] || severityColors[AuditSeverity.MEDIUM];
};

export const getActionTypeColor = (actionType: ActionType): string => {
  return actionTypeColors[actionType] || '#757575'; // Default gray
};