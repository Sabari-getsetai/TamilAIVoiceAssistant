'use client';

/**
 * Enterprise Security Monitoring Interface Component
 *
 * Features:
 * - Real-time security event streaming
 * - Live threat detection and alerting
 * - Security incident categorization
 * - Interactive timeline visualization
 * - Automated response suggestions
 * - Risk assessment dashboard
 * - Incident management workflow
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Stack,
  Badge,
  LinearProgress,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Paper,
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Security,
  Warning,
  Error,
  CheckCircle,
  Info,
  NotificationImportant,
  Shield,
  Computer,
  Person,
  LocationOn,
  AccessTime,
  Block,
  PlayArrow,
  Pause,
  Refresh,
  FilterList,
  MoreVert,
  Visibility,
  Assignment,
  VpnKey,
  Fingerprint,
  NetworkCheck,
  WifiOff,
  DangerousOutlined,
  ExpandMore,
  Timeline,
  TrendingUp,
  NotificationsActive,
} from '@mui/icons-material';
import { format, formatDistanceToNow, isAfter, subHours } from 'date-fns';
import { enqueueSnackbar } from 'notistack';

import {
  useSecurityEvents,
  useSecurityEventsStream,
} from '../../services/api/audit/auditQueries';
import {
  SecurityEvent,
  AuditSeverity,
  getSeverityColor,
} from '../../services/api/audit/auditTypes';
import { MinimalErrorBoundary } from '../common/ErrorBoundary';

interface SecurityMonitoringInterfaceProps {
  organizationId?: string;
  onIncidentCreate?: (event: SecurityEvent) => void;
  onAlertAcknowledge?: (eventId: string) => void;
}

// Security event categories
const EVENT_CATEGORIES = [
  { value: 'all', label: 'All Events' },
  { value: 'authentication', label: 'Authentication' },
  { value: 'authorization', label: 'Authorization' },
  { value: 'data_access', label: 'Data Access' },
  { value: 'system', label: 'System Events' },
  { value: 'network', label: 'Network Events' },
] as const;

// Security threat levels
const THREAT_LEVELS = {
  critical: { color: '#f44336', icon: DangerousOutlined, label: 'Critical Threat' },
  high: { color: '#ff9800', icon: Warning, label: 'High Risk' },
  medium: { color: '#2196f3', icon: Info, label: 'Medium Risk' },
  low: { color: '#4caf50', icon: CheckCircle, label: 'Low Risk' },
} as const;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

export const SecurityMonitoringInterface: React.FC<SecurityMonitoringInterfaceProps> = ({
  organizationId,
  onIncidentCreate,
  onAlertAcknowledge,
}) => {
  const [isStreaming, setIsStreaming] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [tabValue, setTabValue] = useState(0);
  const [acknowledgedEvents, setAcknowledgedEvents] = useState<Set<string>>(new Set());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch security events
  const {
    data: securityEvents,
    isLoading,
    isError,
    error,
    refetch,
  } = useSecurityEvents(organizationId, 7, {
    refetchInterval: autoRefresh ? 30000 : false, // 30 seconds
  });

  // Setup real-time streaming
  const { startStream } = useSecurityEventsStream(organizationId, isStreaming);

  // Start/stop streaming based on state
  useEffect(() => {
    if (isStreaming) {
      const cleanup = startStream();
      return cleanup;
    }
  }, [isStreaming, startStream]);

  // Filter events by category
  const filteredEvents = useMemo(() => {
    if (!securityEvents) return [];

    let filtered = securityEvents;

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(event => {
        const eventType = event.event_type?.toLowerCase() || '';
        switch (selectedCategory) {
          case 'authentication':
            return eventType.includes('login') || eventType.includes('auth');
          case 'authorization':
            return eventType.includes('access') || eventType.includes('permission');
          case 'data_access':
            return eventType.includes('data') || eventType.includes('export');
          case 'system':
            return eventType.includes('system') || eventType.includes('config');
          case 'network':
            return eventType.includes('network') || eventType.includes('connection');
          default:
            return true;
        }
      });
    }

    return filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [securityEvents, selectedCategory]);

  // Categorize events by severity and recency
  const categorizedEvents = useMemo(() => {
    const now = new Date();
    const oneHourAgo = subHours(now, 1);
    const oneDayAgo = subHours(now, 24);

    return {
      critical: filteredEvents.filter(e => e.severity === 'critical' && !acknowledgedEvents.has(e.id)),
      recent: filteredEvents.filter(e => isAfter(new Date(e.timestamp), oneHourAgo)),
      today: filteredEvents.filter(e => isAfter(new Date(e.timestamp), oneDayAgo)),
      acknowledged: filteredEvents.filter(e => acknowledgedEvents.has(e.id)),
    };
  }, [filteredEvents, acknowledgedEvents]);

  const handleToggleStreaming = () => {
    setIsStreaming(!isStreaming);
    enqueueSnackbar(
      `Real-time monitoring ${!isStreaming ? 'enabled' : 'disabled'}`,
      { variant: !isStreaming ? 'success' : 'info' }
    );
  };

  const handleRefresh = () => {
    refetch();
    enqueueSnackbar('Security events refreshed', { variant: 'success' });
  };

  const handleAcknowledgeEvent = (eventId: string) => {
    setAcknowledgedEvents(prev => new Set([...prev, eventId]));
    onAlertAcknowledge?.(eventId);
    enqueueSnackbar('Security event acknowledged', { variant: 'success' });
  };

  const handleCreateIncident = (event: SecurityEvent) => {
    onIncidentCreate?.(event);
    enqueueSnackbar('Security incident created', { variant: 'warning' });
  };

  const getThreatIcon = (severity: AuditSeverity) => {
    const threatLevel = THREAT_LEVELS[severity] || THREAT_LEVELS.low;
    const IconComponent = threatLevel.icon;
    return <IconComponent sx={{ color: threatLevel.color }} />;
  };

  const getEventIcon = (eventType: string) => {
    const type = eventType?.toLowerCase() || '';
    if (type.includes('login') || type.includes('auth')) return <VpnKey />;
    if (type.includes('access') || type.includes('permission')) return <Shield />;
    if (type.includes('data') || type.includes('export')) return <Assignment />;
    if (type.includes('system') || type.includes('config')) return <Computer />;
    if (type.includes('network')) return <NetworkCheck />;
    return <Security />;
  };

  const renderEventList = (events: SecurityEvent[], title: string) => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Timeline />
        {title} ({events.length})
      </Typography>

      {events.length === 0 ? (
        <Alert severity="info">No {title.toLowerCase()} found.</Alert>
      ) : (
        <List>
          {events.map((event, index) => (
            <React.Fragment key={event.id}>
              <ListItem>
                <ListItemIcon>
                  <Badge
                    badgeContent={getThreatIcon(event.severity)}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  >
                    {getEventIcon(event.event_type || '')}
                  </Badge>
                </ListItemIcon>

                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body1" fontWeight="medium">
                        {event.event_type || 'Security Event'}
                      </Typography>
                      <Chip
                        label={event.severity?.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: getSeverityColor(event.severity) + '20',
                          color: getSeverityColor(event.severity),
                          fontWeight: 'bold',
                        }}
                      />
                      {isAfter(new Date(event.timestamp), subHours(new Date(), 1)) && (
                        <Chip label="NEW" size="small" color="error" variant="outlined" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {event.description || 'No description available'}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <AccessTime fontSize="small" color="action" />
                          <Typography variant="caption">
                            {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                          </Typography>
                        </Box>
                        {event.user_id && (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <Person fontSize="small" color="action" />
                            <Typography variant="caption">
                              User: {event.user_id}
                            </Typography>
                          </Box>
                        )}
                        {event.source_ip && (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <LocationOn fontSize="small" color="action" />
                            <Typography variant="caption">
                              IP: {event.source_ip}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  }
                />

                <ListItemSecondaryAction>
                  <Stack direction="row" spacing={1}>
                    {!acknowledgedEvents.has(event.id) && (
                      <>
                        <Tooltip title="Acknowledge Event">
                          <IconButton
                            size="small"
                            onClick={() => handleAcknowledgeEvent(event.id)}
                          >
                            <CheckCircle />
                          </IconButton>
                        </Tooltip>
                        {event.severity === 'critical' && (
                          <Tooltip title="Create Incident">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleCreateIncident(event)}
                            >
                              <NotificationImportant />
                            </IconButton>
                          </Tooltip>
                        )}
                      </>
                    )}
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </ListItemSecondaryAction>
              </ListItem>
              {index < events.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );

  if (isLoading) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" gap={2} py={4}>
        <LinearProgress sx={{ width: '100%' }} />
        <Typography variant="body1" color="text.secondary">
          Loading security monitoring data...
        </Typography>
      </Box>
    );
  }

  if (isError) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={handleRefresh}>
            Retry
          </Button>
        }
      >
        Failed to load security events: {error?.message}
      </Alert>
    );
  }

  return (
    <MinimalErrorBoundary context={{ component: 'SecurityMonitoringInterface' }}>
      <Box>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              <Security sx={{ mr: 2, verticalAlign: 'middle' }} />
              Security Monitoring Center
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Real-time security event monitoring and incident management
            </Typography>
          </Box>

          <Stack direction="row" spacing={2} alignItems="center">
            <FormControlLabel
              control={
                <Switch
                  checked={isStreaming}
                  onChange={handleToggleStreaming}
                  color="primary"
                />
              }
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  {isStreaming ? <PlayArrow color="success" /> : <Pause color="action" />}
                  Live Monitoring
                </Box>
              }
            />

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                label="Category"
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {EVENT_CATEGORIES.map((category) => (
                  <MenuItem key={category.value} value={category.value}>
                    {category.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  color="primary"
                />
              }
              label="Auto Refresh"
            />

            <Tooltip title="Refresh Now">
              <IconButton onClick={handleRefresh}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {/* Critical Alerts Banner */}
        {categorizedEvents.critical.length > 0 && (
          <Alert
            severity="error"
            icon={<DangerousOutlined />}
            sx={{ mb: 3 }}
            action={
              <Button color="inherit" size="small">
                View All Critical
              </Button>
            }
          >
            <Typography variant="body1" fontWeight="medium">
              {categorizedEvents.critical.length} critical security event{categorizedEvents.critical.length > 1 ? 's' : ''} require immediate attention!
            </Typography>
          </Alert>
        )}

        {/* Status Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Badge badgeContent={categorizedEvents.critical.length} color="error">
                  <DangerousOutlined color="error" sx={{ fontSize: 40 }} />
                </Badge>
                <Typography variant="h6" color="error.main" sx={{ mt: 1 }}>
                  Critical Events
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Require immediate action
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Badge badgeContent={categorizedEvents.recent.length} color="warning">
                  <AccessTime color="warning" sx={{ fontSize: 40 }} />
                </Badge>
                <Typography variant="h6" color="warning.main" sx={{ mt: 1 }}>
                  Recent Events
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last hour
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Badge badgeContent={categorizedEvents.today.length} color="info">
                  <Timeline color="info" sx={{ fontSize: 40 }} />
                </Badge>
                <Typography variant="h6" color="info.main" sx={{ mt: 1 }}>
                  Today's Events
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 24 hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Badge badgeContent={categorizedEvents.acknowledged.length} color="success">
                  <CheckCircle color="success" sx={{ fontSize: 40 }} />
                </Badge>
                <Typography variant="h6" color="success.main" sx={{ mt: 1 }}>
                  Acknowledged
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Handled events
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Event Tabs */}
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab
                label={
                  <Badge badgeContent={categorizedEvents.critical.length} color="error">
                    <Box display="flex" alignItems="center" gap={1}>
                      <DangerousOutlined />
                      Critical Events
                    </Box>
                  </Badge>
                }
              />
              <Tab
                label={
                  <Badge badgeContent={categorizedEvents.recent.length} color="warning">
                    <Box display="flex" alignItems="center" gap={1}>
                      <AccessTime />
                      Recent Events
                    </Box>
                  </Badge>
                }
              />
              <Tab
                label={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Timeline />
                    All Events
                  </Box>
                }
              />
              <Tab
                label={
                  <Box display="flex" alignItems="center" gap={1}>
                    <CheckCircle />
                    Acknowledged
                  </Box>
                }
              />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            {renderEventList(categorizedEvents.critical, 'Critical Security Events')}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {renderEventList(categorizedEvents.recent, 'Recent Security Events')}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            {renderEventList(filteredEvents.slice(0, 50), 'All Security Events')}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            {renderEventList(categorizedEvents.acknowledged, 'Acknowledged Events')}
          </TabPanel>
        </Card>

        {/* System Status */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Shield sx={{ mr: 1, verticalAlign: 'middle' }} />
              System Security Status
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">Overall Security Level</Typography>
                  <Chip
                    label={categorizedEvents.critical.length > 0 ? 'HIGH RISK' :
                           categorizedEvents.recent.length > 5 ? 'ELEVATED' : 'NORMAL'}
                    color={categorizedEvents.critical.length > 0 ? 'error' :
                           categorizedEvents.recent.length > 5 ? 'warning' : 'success'}
                  />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(100, (categorizedEvents.critical.length * 30 + categorizedEvents.recent.length * 10))}
                  color={categorizedEvents.critical.length > 0 ? 'error' :
                         categorizedEvents.recent.length > 5 ? 'warning' : 'success'}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">Monitoring Status</Typography>
                  <Chip
                    label={isStreaming ? 'ACTIVE' : 'PAUSED'}
                    color={isStreaming ? 'success' : 'warning'}
                    icon={isStreaming ? <NotificationsActive /> : <Pause />}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {isStreaming ? 'Real-time monitoring enabled' : 'Real-time monitoring paused'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    </MinimalErrorBoundary>
  );
};

export default SecurityMonitoringInterface;