'use client';

/**
 * Enterprise Audit Statistics Dashboard Component
 *
 * Features:
 * - Real-time audit statistics and trends
 * - Interactive charts and visualizations
 * - Security risk assessment metrics
 * - Compliance framework reporting
 * - Time-based analytics with drill-down
 * - Export capabilities for reports
 * - Mobile-responsive dashboard layout
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Stack,
  Alert,
  Paper,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Security,
  Warning,
  Info,
  CheckCircle,
  Error,
  Assessment,
  Download,
  Refresh,
  Timeline,
  Shield,
  Person,
  Business,
  Computer,
  Gavel,
  BarChart,
  PieChart,
  ShowChart,
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Cell,
  Pie,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { format, subDays, startOfDay } from 'date-fns';

import { useAuditStats, useSecurityEvents } from '../../services/api/audit/auditQueries';
import {
  AuditStats,
  SecurityEvent,
  AuditSeverity,
  ActionType,
  ComplianceTag,
  getSeverityColor,
  getComplianceColor,
} from '../../services/api/audit/auditTypes';
import { MinimalErrorBoundary } from '../common/ErrorBoundary';

interface AuditStatsDashboardProps {
  organizationId?: string;
  onExportReport?: () => void;
}

// Time range options
const TIME_RANGES = [
  { value: 7, label: '7 Days' },
  { value: 30, label: '30 Days' },
  { value: 90, label: '90 Days' },
  { value: 365, label: '1 Year' },
];

// Chart color schemes
const SEVERITY_COLORS = {
  critical: '#f44336',
  high: '#ff9800',
  medium: '#2196f3',
  low: '#4caf50',
} as const;

const ACTION_TYPE_COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1',
  '#d084d0', '#87d068', '#ffb347', '#ff6b6b', '#4ecdc4'
];

const COMPLIANCE_COLORS = {
  GDPR: '#4caf50',
  SOC2: '#2196f3',
  HIPAA: '#ff9800',
  ISO27001: '#9c27b0',
  PCI_DSS: '#f44336',
  CCPA: '#795548',
} as const;

export const AuditStatsDashboard: React.FC<AuditStatsDashboardProps> = ({
  organizationId,
  onExportReport,
}) => {
  const [timeRange, setTimeRange] = useState(30);

  // Fetch audit statistics
  const {
    data: auditStats,
    isLoading: isStatsLoading,
    isError: isStatsError,
    error: statsError,
    refetch: refetchStats,
  } = useAuditStats(organizationId, timeRange, {
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch security events
  const {
    data: securityEvents,
    isLoading: isEventsLoading,
    isError: isEventsError,
    error: eventsError,
    refetch: refetchEvents,
  } = useSecurityEvents(organizationId, Math.min(timeRange, 30), {
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Generate time series data for trends
  const timeSeriesData = useMemo(() => {
    if (!auditStats?.daily_counts) return [];

    return Object.entries(auditStats.daily_counts).map(([date, count]) => ({
      date: format(new Date(date), 'MMM dd'),
      fullDate: date,
      count: count,
    })).slice(-timeRange);
  }, [auditStats?.daily_counts, timeRange]);

  // Generate severity distribution data
  const severityData = useMemo(() => {
    if (!auditStats?.severity_distribution) return [];

    return Object.entries(auditStats.severity_distribution).map(([severity, count]) => ({
      name: severity.charAt(0).toUpperCase() + severity.slice(1),
      value: count,
      color: SEVERITY_COLORS[severity as AuditSeverity] || '#9e9e9e',
    }));
  }, [auditStats?.severity_distribution]);

  // Generate action type distribution data
  const actionTypeData = useMemo(() => {
    if (!auditStats?.action_type_distribution) return [];

    return Object.entries(auditStats.action_type_distribution)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10) // Top 10 action types
      .map(([actionType, count], index) => ({
        name: actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: count,
        color: ACTION_TYPE_COLORS[index % ACTION_TYPE_COLORS.length],
      }));
  }, [auditStats?.action_type_distribution]);

  // Generate compliance framework data
  const complianceData = useMemo(() => {
    if (!auditStats?.compliance_distribution) return [];

    return Object.entries(auditStats.compliance_distribution).map(([framework, count]) => ({
      name: framework,
      value: count,
      color: COMPLIANCE_COLORS[framework as ComplianceTag] || '#9e9e9e',
    }));
  }, [auditStats?.compliance_distribution]);

  // Calculate risk score trend
  const riskScoreTrend = useMemo(() => {
    if (!securityEvents) return null;

    const recentEvents = securityEvents.slice(-7); // Last 7 events
    const avgRisk = recentEvents.reduce((sum, event) => {
      const severity = event.severity;
      const riskScore = severity === 'critical' ? 100 :
                       severity === 'high' ? 75 :
                       severity === 'medium' ? 50 : 25;
      return sum + riskScore;
    }, 0) / Math.max(recentEvents.length, 1);

    return Math.round(avgRisk);
  }, [securityEvents]);

  const handleRefresh = () => {
    refetchStats();
    refetchEvents();
  };

  const handleTimeRangeChange = (newTimeRange: number) => {
    setTimeRange(newTimeRange);
  };

  const handleExport = () => {
    if (onExportReport) {
      onExportReport();
    } else {
      // Default export functionality
      const exportData = {
        organization_id: organizationId,
        time_range: timeRange,
        generated_at: new Date().toISOString(),
        stats: auditStats,
        security_events: securityEvents,
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      });

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-stats-${format(new Date(), 'yyyy-MM-dd')}.json`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  // Loading state
  if (isStatsLoading || isEventsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography variant="h6" color="text.secondary">
          Loading audit statistics...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (isStatsError || isEventsError) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={handleRefresh}>
            Retry
          </Button>
        }
      >
        Failed to load audit statistics: {statsError?.message || eventsError?.message}
      </Alert>
    );
  }

  if (!auditStats) {
    return (
      <Alert severity="info">
        No audit statistics available for the selected time range.
      </Alert>
    );
  }

  return (
    <MinimalErrorBoundary context={{ component: 'AuditStatsDashboard' }}>
      <Box>
        {/* Dashboard Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              <Assessment sx={{ mr: 2, verticalAlign: 'middle' }} />
              Audit Analytics Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Real-time audit trail statistics and security monitoring
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={2}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={timeRange}
                label="Time Range"
                onChange={(e) => handleTimeRangeChange(Number(e.target.value))}
              >
                {TIME_RANGES.map((range) => (
                  <MenuItem key={range.value} value={range.value}>
                    {range.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Tooltip title="Refresh Data">
              <IconButton onClick={handleRefresh}>
                <Refresh />
              </IconButton>
            </Tooltip>

            <Tooltip title="Export Report">
              <IconButton onClick={handleExport}>
                <Download />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Key Metrics */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Box display="flex" justifyContent="center" mb={1}>
                  <Timeline color="primary" fontSize="large" />
                </Box>
                <Typography variant="h3" color="primary">
                  {auditStats.total_entries.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Audit Entries
                </Typography>
                <Typography variant="caption" color="success.main">
                  +{auditStats.growth_rate || 0}% from last period
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Box display="flex" justifyContent="center" mb={1}>
                  <Person color="info" fontSize="large" />
                </Box>
                <Typography variant="h3" color="info.main">
                  {auditStats.unique_users.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Users
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Last {timeRange} days
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Box display="flex" justifyContent="center" mb={1}>
                  <Security color="warning" fontSize="large" />
                </Box>
                <Typography variant="h3" color="warning.main">
                  {securityEvents?.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Security Events
                </Typography>
                <Typography variant="caption" color="warning.main">
                  Requires attention
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Box display="flex" justifyContent="center" mb={1}>
                  <Shield
                    color={riskScoreTrend && riskScoreTrend > 70 ? "error" :
                           riskScoreTrend && riskScoreTrend > 40 ? "warning" : "success"}
                    fontSize="large"
                  />
                </Box>
                <Typography
                  variant="h3"
                  color={riskScoreTrend && riskScoreTrend > 70 ? "error.main" :
                         riskScoreTrend && riskScoreTrend > 40 ? "warning.main" : "success.main"}
                >
                  {riskScoreTrend || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Risk Score
                </Typography>
                <Box display="flex" justifyContent="center" alignItems="center" mt={1}>
                  {riskScoreTrend && riskScoreTrend > 40 ?
                    <TrendingUp color="error" fontSize="small" /> :
                    <TrendingDown color="success" fontSize="small" />
                  }
                  <Typography variant="caption" sx={{ ml: 0.5 }}>
                    {riskScoreTrend && riskScoreTrend > 40 ? 'Increasing' : 'Stable'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Audit Activity Trend */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <ShowChart sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Audit Activity Trend
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeSeriesData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip
                        labelFormatter={(label, payload) =>
                          payload?.[0]?.payload?.fullDate ?
                          format(new Date(payload[0].payload.fullDate), 'PPP') :
                          label
                        }
                      />
                      <Area
                        type="monotone"
                        dataKey="count"
                        stroke="#2196f3"
                        fill="#2196f3"
                        fillOpacity={0.3}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Severity Distribution */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Warning sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Severity Distribution
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={severityData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label={(entry) => `${entry.name}: ${entry.value}`}
                      >
                        {severityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Top Action Types */}
          <Grid item xs={12} lg={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <BarChart sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Top Action Types
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={actionTypeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="value" fill="#8884d8">
                        {actionTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Compliance Framework Distribution */}
          <Grid item xs={12} lg={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Gavel sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Compliance Coverage
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsBarChart data={complianceData} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="name" type="category" width={80} />
                      <RechartsTooltip />
                      <Bar dataKey="value" fill="#4caf50">
                        {complianceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </RechartsBarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Security Events */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Recent Security Events
                </Typography>

                {securityEvents && securityEvents.length > 0 ? (
                  <Box>
                    {securityEvents.slice(0, 5).map((event, index) => (
                      <Box key={event.id || index}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" py={1}>
                          <Box display="flex" alignItems="center" gap={2}>
                            {event.severity === 'critical' ? <Error color="error" /> :
                             event.severity === 'high' ? <Warning color="warning" /> :
                             event.severity === 'medium' ? <Info color="info" /> :
                             <CheckCircle color="success" />}

                            <Box>
                              <Typography variant="body1" fontWeight="medium">
                                {event.event_type || 'Security Event'}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {event.description || 'No description available'}
                              </Typography>
                            </Box>
                          </Box>

                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={event.severity?.toUpperCase() || 'UNKNOWN'}
                              size="small"
                              color={event.severity === 'critical' ? 'error' :
                                     event.severity === 'high' ? 'warning' :
                                     event.severity === 'medium' ? 'info' : 'success'}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {format(new Date(event.timestamp), 'MMM dd, HH:mm')}
                            </Typography>
                          </Box>
                        </Box>
                        {index < securityEvents.slice(0, 5).length - 1 && <Divider />}
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Alert severity="success">
                    <Typography variant="body2">
                      No recent security events detected. System is operating normally.
                    </Typography>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </MinimalErrorBoundary>
  );
};

export default AuditStatsDashboard;