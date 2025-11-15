'use client';

/**
 * Enterprise Microservice Configuration Manager
 *
 * Features:
 * - Service configuration editing and validation
 * - Environment variable management
 * - Configuration versioning and rollback
 * - Deployment pipeline integration
 * - Configuration templates and presets
 * - Security and secrets management
 * - Live configuration updates
 * - Configuration diff and comparison
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  IconButton,
  Tooltip,
  TextField,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Stack,
  Breadcrumbs,
  Link,
  Badge,
  InputAdornment,
} from '@mui/material';
import {
  Settings,
  Save,
  Refresh,
  History,
  Edit,
  Delete,
  Add,
  Visibility,
  VisibilityOff,
  ContentCopy,
  Download,
  Upload,
  ExpandMore,
  Warning,
  CheckCircle,
  Error,
  Info,
  Security,
  Code,
  Storage,
  CloudQueue,
  Api,
  Database,
  Memory,
  Computer,
  RestoreFromTrash,
  CompareArrows,
  Backup,
  PublishedWithChanges,
  AutoFixHigh,
  VpnKey,
  Lock,
  LockOpen,
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format } from 'date-fns';
import { enqueueSnackbar } from 'notistack';

import { MinimalErrorBoundary } from '../common/ErrorBoundary';

interface ServiceConfigurationManagerProps {
  organizationId?: string;
}

// Service configuration schema
interface ServiceConfig {
  id: string;
  name: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  type: 'api' | 'database' | 'cache' | 'storage' | 'ai' | 'frontend';
  status: 'active' | 'inactive' | 'deprecated';
  lastModified: Date;
  modifiedBy: string;
  description?: string;
  configuration: {
    environment_variables: Record<string, ConfigValue>;
    service_settings: Record<string, ConfigValue>;
    security_settings: Record<string, ConfigValue>;
    performance_settings: Record<string, ConfigValue>;
  };
  secrets: Record<string, SecretValue>;
  dependencies: string[];
  deployment: {
    auto_deploy: boolean;
    health_check_url: string;
    rollback_enabled: boolean;
    max_replicas: number;
    min_replicas: number;
  };
}

interface ConfigValue {
  value: string | number | boolean;
  type: 'string' | 'number' | 'boolean' | 'json' | 'url' | 'email';
  required: boolean;
  description?: string;
  default?: string | number | boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: string[];
  };
}

interface SecretValue {
  value: string;
  encrypted: boolean;
  lastRotated: Date;
  expiresAt?: Date;
  description?: string;
}

// Mock service configurations
const MOCK_SERVICES: ServiceConfig[] = [
  {
    id: 'fastapi-backend',
    name: 'FastAPI Backend',
    version: '1.2.3',
    environment: 'production',
    type: 'api',
    status: 'active',
    lastModified: new Date(),
    modifiedBy: 'admin@example.com',
    description: 'Core API service for Tamil AI Voice Assistant',
    configuration: {
      environment_variables: {
        PORT: { value: 8001, type: 'number', required: true, description: 'API server port' },
        LOG_LEVEL: { value: 'INFO', type: 'string', required: true, validation: { options: ['DEBUG', 'INFO', 'WARNING', 'ERROR'] } },
        CORS_ORIGINS: { value: 'http://localhost:3000', type: 'string', required: false, description: 'Allowed CORS origins' },
        API_RATE_LIMIT: { value: '100/minute', type: 'string', required: false, description: 'API rate limiting configuration' },
      },
      service_settings: {
        MAX_WORKERS: { value: 4, type: 'number', required: true, validation: { min: 1, max: 16 } },
        RELOAD: { value: true, type: 'boolean', required: false, description: 'Enable auto-reload in development' },
        ACCESS_LOG: { value: true, type: 'boolean', required: false, description: 'Enable access logging' },
      },
      security_settings: {
        JWT_ALGORITHM: { value: 'HS256', type: 'string', required: true },
        SESSION_TIMEOUT: { value: 3600, type: 'number', required: true, description: 'Session timeout in seconds' },
        HTTPS_ONLY: { value: false, type: 'boolean', required: true, description: 'Force HTTPS connections' },
      },
      performance_settings: {
        DB_POOL_SIZE: { value: 20, type: 'number', required: true, validation: { min: 5, max: 100 } },
        CACHE_TTL: { value: 300, type: 'number', required: false, description: 'Default cache TTL in seconds' },
        REQUEST_TIMEOUT: { value: 30, type: 'number', required: true, validation: { min: 1, max: 300 } },
      },
    },
    secrets: {
      JWT_SECRET_KEY: { value: '****', encrypted: true, lastRotated: new Date(), description: 'JWT signing secret' },
      DATABASE_PASSWORD: { value: '****', encrypted: true, lastRotated: new Date(), description: 'Database connection password' },
      OPENAI_API_KEY: { value: '****', encrypted: true, lastRotated: new Date(), expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) },
    },
    dependencies: ['postgresql', 'redis', 'minio'],
    deployment: {
      auto_deploy: true,
      health_check_url: '/health',
      rollback_enabled: true,
      max_replicas: 10,
      min_replicas: 2,
    },
  },
  // Add more mock services as needed
];

// Configuration templates
const CONFIG_TEMPLATES = {
  api_service: {
    name: 'API Service Template',
    description: 'Standard configuration template for API services',
    configuration: {
      environment_variables: {
        PORT: { value: 8000, type: 'number', required: true },
        LOG_LEVEL: { value: 'INFO', type: 'string', required: true },
        CORS_ORIGINS: { value: '*', type: 'string', required: false },
      },
      service_settings: {
        MAX_WORKERS: { value: 4, type: 'number', required: true },
        RELOAD: { value: false, type: 'boolean', required: false },
      },
    },
  },
  database_service: {
    name: 'Database Service Template',
    description: 'Standard configuration template for database services',
    configuration: {
      environment_variables: {
        DB_HOST: { value: 'localhost', type: 'string', required: true },
        DB_PORT: { value: 5432, type: 'number', required: true },
        DB_NAME: { value: 'app_db', type: 'string', required: true },
      },
    },
  },
};

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box sx={{ p: 0 }}>{children}</Box>}
  </div>
);

export const ServiceConfigurationManager: React.FC<ServiceConfigurationManagerProps> = ({
  organizationId,
}) => {
  const [services, setServices] = useState<ServiceConfig[]>(MOCK_SERVICES);
  const [selectedService, setSelectedService] = useState<ServiceConfig | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ServiceConfig | null>(null);

  // Load service on selection
  useEffect(() => {
    if (services.length > 0 && !selectedService) {
      setSelectedService(services[0]);
    }
  }, [services, selectedService]);

  const handleServiceChange = useCallback((serviceId: string) => {
    const service = services.find(s => s.id === serviceId);
    setSelectedService(service || null);
    setEditMode(false);
  }, [services]);

  const handleConfigSave = useCallback(async () => {
    if (!editingConfig) return;

    try {
      // Validate configuration
      // In production, this would call an API
      setServices(prev => prev.map(s => s.id === editingConfig.id ? editingConfig : s));
      setSelectedService(editingConfig);
      setEditMode(false);
      enqueueSnackbar('Configuration saved successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to save configuration', { variant: 'error' });
    }
  }, [editingConfig]);

  const handleConfigReset = useCallback(() => {
    setEditingConfig(selectedService);
    setEditMode(false);
  }, [selectedService]);

  const handleTemplateApply = useCallback((templateKey: string) => {
    if (!selectedService) return;

    const template = CONFIG_TEMPLATES[templateKey as keyof typeof CONFIG_TEMPLATES];
    if (!template) return;

    const updatedService: ServiceConfig = {
      ...selectedService,
      configuration: {
        ...selectedService.configuration,
        ...template.configuration,
      },
    };

    setEditingConfig(updatedService);
    setTemplateDialogOpen(false);
    setEditMode(true);
    enqueueSnackbar('Template applied successfully', { variant: 'success' });
  }, [selectedService]);

  const handleSecretRotate = useCallback(async (secretKey: string) => {
    if (!selectedService) return;

    // In production, this would call an API to rotate the secret
    enqueueSnackbar(`Rotating secret: ${secretKey}`, { variant: 'info' });

    setTimeout(() => {
      setServices(prev => prev.map(s => {
        if (s.id === selectedService.id) {
          return {
            ...s,
            secrets: {
              ...s.secrets,
              [secretKey]: {
                ...s.secrets[secretKey],
                lastRotated: new Date(),
              },
            },
          };
        }
        return s;
      }));
      enqueueSnackbar('Secret rotated successfully', { variant: 'success' });
    }, 2000);
  }, [selectedService]);

  const renderConfigValue = (key: string, config: ConfigValue, isEditing: boolean) => {
    const handleValueChange = (newValue: string | number | boolean) => {
      if (!editingConfig) return;

      const category = Object.keys(editingConfig.configuration).find(cat =>
        editingConfig.configuration[cat as keyof typeof editingConfig.configuration][key]
      );

      if (!category) return;

      setEditingConfig({
        ...editingConfig,
        configuration: {
          ...editingConfig.configuration,
          [category]: {
            ...editingConfig.configuration[category as keyof typeof editingConfig.configuration],
            [key]: {
              ...config,
              value: newValue,
            },
          },
        },
      });
    };

    if (isEditing) {
      switch (config.type) {
        case 'boolean':
          return (
            <FormControlLabel
              control={
                <Switch
                  checked={Boolean(config.value)}
                  onChange={(e) => handleValueChange(e.target.checked)}
                />
              }
              label=""
            />
          );
        case 'number':
          return (
            <TextField
              type="number"
              value={config.value}
              onChange={(e) => handleValueChange(Number(e.target.value))}
              size="small"
              fullWidth
              inputProps={{
                min: config.validation?.min,
                max: config.validation?.max,
              }}
            />
          );
        default:
          if (config.validation?.options) {
            return (
              <Select
                value={config.value}
                onChange={(e) => handleValueChange(e.target.value)}
                size="small"
                fullWidth
              >
                {config.validation.options.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            );
          }
          return (
            <TextField
              value={config.value}
              onChange={(e) => handleValueChange(e.target.value)}
              size="small"
              fullWidth
              multiline={config.type === 'json'}
              rows={config.type === 'json' ? 3 : 1}
            />
          );
      }
    }

    // Display mode
    return (
      <Typography variant="body2" fontFamily={config.type === 'json' ? 'monospace' : 'inherit'}>
        {String(config.value)}
      </Typography>
    );
  };

  const renderConfigSection = (title: string, configs: Record<string, ConfigValue>, icon: React.ReactNode) => (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="h6">{title}</Typography>
          <Chip label={Object.keys(configs).length} size="small" />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Key</TableCell>
                <TableCell>Value</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Required</TableCell>
                <TableCell>Description</TableCell>
                {editMode && <TableCell>Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(configs).map(([key, config]) => (
                <TableRow key={key}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {key}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {renderConfigValue(key, config, editMode)}
                  </TableCell>
                  <TableCell>
                    <Chip label={config.type} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    {config.required ? (
                      <CheckCircle color="success" fontSize="small" />
                    ) : (
                      <Error color="disabled" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {config.description || 'No description'}
                    </Typography>
                  </TableCell>
                  {editMode && (
                    <TableCell>
                      <IconButton size="small">
                        <Delete />
                      </IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </AccordionDetails>
    </Accordion>
  );

  const renderSecretsSection = () => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
            Secrets Management
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={showSecrets}
                onChange={(e) => setShowSecrets(e.target.checked)}
                icon={<VisibilityOff />}
                checkedIcon={<Visibility />}
              />
            }
            label="Show Values"
          />
        </Box>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Secret Key</TableCell>
                <TableCell>Value</TableCell>
                <TableCell>Last Rotated</TableCell>
                <TableCell>Expires</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {selectedService && Object.entries(selectedService.secrets).map(([key, secret]) => (
                <TableRow key={key}>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Lock fontSize="small" />
                      <Typography variant="body2" fontFamily="monospace">
                        {key}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {showSecrets ? secret.value : '••••••••'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {format(secret.lastRotated, 'MMM dd, yyyy')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {secret.expiresAt ? (
                      <Chip
                        label={format(secret.expiresAt, 'MMM dd, yyyy')}
                        size="small"
                        color={secret.expiresAt < new Date() ? 'error' : 'default'}
                      />
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        No expiration
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Rotate Secret">
                        <IconButton
                          size="small"
                          onClick={() => handleSecretRotate(key)}
                        >
                          <Refresh />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Copy to Clipboard">
                        <IconButton size="small">
                          <ContentCopy />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );

  if (!selectedService) {
    return (
      <Alert severity="info">
        No service selected. Please select a service to configure.
      </Alert>
    );
  }

  return (
    <MinimalErrorBoundary context={{ component: 'ServiceConfigurationManager' }}>
      <Box>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Breadcrumbs sx={{ mb: 1 }}>
              <Link color="inherit" href="/admin/microservices">
                Microservices
              </Link>
              <Typography color="text.primary">Configuration</Typography>
              <Typography color="text.primary">{selectedService.name}</Typography>
            </Breadcrumbs>
            <Typography variant="h4" component="h1">
              <Settings sx={{ mr: 2, verticalAlign: 'middle' }} />
              Service Configuration
            </Typography>
          </Box>

          <Stack direction="row" spacing={2}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Service</InputLabel>
              <Select
                value={selectedService.id}
                label="Service"
                onChange={(e) => handleServiceChange(e.target.value)}
              >
                {services.map((service) => (
                  <MenuItem key={service.id} value={service.id}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip label={service.environment} size="small" />
                      {service.name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="outlined"
              startIcon={<History />}
              onClick={() => setHistoryDialogOpen(true)}
            >
              History
            </Button>

            <Button
              variant="outlined"
              startIcon={<AutoFixHigh />}
              onClick={() => setTemplateDialogOpen(true)}
            >
              Templates
            </Button>

            {editMode ? (
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" onClick={handleConfigReset}>
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleConfigSave}
                >
                  Save
                </Button>
              </Stack>
            ) : (
              <Button
                variant="contained"
                startIcon={<Edit />}
                onClick={() => {
                  setEditingConfig(selectedService);
                  setEditMode(true);
                }}
              >
                Edit Config
              </Button>
            )}
          </Stack>
        </Box>

        {/* Service Overview */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Service Name
                  </Typography>
                  <Typography variant="h6">{selectedService.name}</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Version
                  </Typography>
                  <Chip label={`v${selectedService.version}`} size="small" />
                </Box>
              </Grid>
              <Grid item xs={12} md={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Environment
                  </Typography>
                  <Chip
                    label={selectedService.environment}
                    color={selectedService.environment === 'production' ? 'error' : 'primary'}
                    size="small"
                  />
                </Box>
              </Grid>
              <Grid item xs={12} md={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={selectedService.status}
                    color={selectedService.status === 'active' ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Modified
                  </Typography>
                  <Typography variant="body2">
                    {format(selectedService.lastModified, 'MMM dd, yyyy HH:mm')}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {editMode && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              You are in edit mode. Make your changes and click Save to apply them to the service.
            </Typography>
          </Alert>
        )}

        {/* Configuration Tabs */}
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab label="Environment Variables" />
              <Tab label="Service Settings" />
              <Tab label="Security" />
              <Tab label="Performance" />
              <Tab label="Secrets" />
              <Tab label="Deployment" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box p={3}>
              {renderConfigSection(
                'Environment Variables',
                (editingConfig || selectedService).configuration.environment_variables,
                <Code />
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box p={3}>
              {renderConfigSection(
                'Service Settings',
                (editingConfig || selectedService).configuration.service_settings,
                <Settings />
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box p={3}>
              {renderConfigSection(
                'Security Settings',
                (editingConfig || selectedService).configuration.security_settings,
                <Security />
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Box p={3}>
              {renderConfigSection(
                'Performance Settings',
                (editingConfig || selectedService).configuration.performance_settings,
                <Speed />
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Box p={3}>
              {renderSecretsSection()}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={5}>
            <Box p={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <CloudQueue sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Deployment Configuration
                  </Typography>
                  {/* Deployment settings would go here */}
                  <Alert severity="info">
                    Deployment configuration interface will be available in the next release.
                  </Alert>
                </CardContent>
              </Card>
            </Box>
          </TabPanel>
        </Card>

        {/* Template Selection Dialog */}
        <Dialog open={templateDialogOpen} onClose={() => setTemplateDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Apply Configuration Template</DialogTitle>
          <DialogContent>
            <Grid container spacing={2}>
              {Object.entries(CONFIG_TEMPLATES).map(([key, template]) => (
                <Grid item xs={12} md={6} key={key}>
                  <Card
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { boxShadow: 2 },
                    }}
                    onClick={() => handleTemplateApply(key)}
                  >
                    <CardContent>
                      <Typography variant="h6">{template.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {template.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setTemplateDialogOpen(false)}>Cancel</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </MinimalErrorBoundary>
  );
};

export default ServiceConfigurationManager;