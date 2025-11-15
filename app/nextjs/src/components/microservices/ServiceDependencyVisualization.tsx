'use client';

/**
 * Service Dependency Visualization Component
 *
 * Features:
 * - Interactive dependency graph visualization
 * - Service relationship mapping
 * - Circular dependency detection
 * - Impact analysis
 * - Service health overlay
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  AccountTree,
  Refresh,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Warning,
  Error,
  CheckCircle,
  Api,
  Database,
  Memory,
  Storage,
  Computer,
  Cloud,
} from '@mui/icons-material';

import { MinimalErrorBoundary } from '../common/ErrorBoundary';

interface ServiceDependencyVisualizationProps {
  organizationId?: string;
}

// Service node data
interface ServiceNode {
  id: string;
  name: string;
  type: 'api' | 'database' | 'cache' | 'storage' | 'ai' | 'frontend';
  status: 'healthy' | 'warning' | 'critical';
  dependencies: string[];
  dependents: string[];
  x?: number;
  y?: number;
}

// Mock service data
const MOCK_SERVICES: ServiceNode[] = [
  {
    id: 'nextjs',
    name: 'Next.js Frontend',
    type: 'frontend',
    status: 'healthy',
    dependencies: ['fastapi'],
    dependents: [],
  },
  {
    id: 'fastapi',
    name: 'FastAPI Backend',
    type: 'api',
    status: 'healthy',
    dependencies: ['postgres', 'redis', 'minio', 'ollama'],
    dependents: ['nextjs'],
  },
  {
    id: 'postgres',
    name: 'PostgreSQL',
    type: 'database',
    status: 'healthy',
    dependencies: [],
    dependents: ['fastapi'],
  },
  {
    id: 'redis',
    name: 'Redis Cache',
    type: 'cache',
    status: 'healthy',
    dependencies: [],
    dependents: ['fastapi'],
  },
  {
    id: 'minio',
    name: 'MinIO Storage',
    type: 'storage',
    status: 'healthy',
    dependencies: [],
    dependents: ['fastapi'],
  },
  {
    id: 'ollama',
    name: 'Ollama LLM',
    type: 'ai',
    status: 'warning',
    dependencies: [],
    dependents: ['fastapi'],
  },
];

const SERVICE_ICONS = {
  api: Api,
  database: Database,
  cache: Memory,
  storage: Storage,
  ai: Computer,
  frontend: Cloud,
};

const STATUS_COLORS = {
  healthy: '#4caf50',
  warning: '#ff9800',
  critical: '#f44336',
};

export const ServiceDependencyVisualization: React.FC<ServiceDependencyVisualizationProps> = ({
  organizationId,
}) => {
  const [services, setServices] = useState<ServiceNode[]>(MOCK_SERVICES);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'dependency' | 'impact'>('dependency');

  // Calculate positions using a simple force-directed layout
  const positionedServices = useMemo(() => {
    const width = 600;
    const height = 400;
    const centerX = width / 2;
    const centerY = height / 2;

    return services.map((service, index) => {
      // Simple circular layout
      const angle = (index / services.length) * 2 * Math.PI;
      const radius = 120;

      return {
        ...service,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      };
    });
  }, [services]);

  // Detect circular dependencies
  const circularDependencies = useMemo(() => {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();
    const cycles: string[][] = [];

    const detectCycle = (serviceId: string, path: string[]) => {
      visited.add(serviceId);
      recursionStack.add(serviceId);

      const service = services.find(s => s.id === serviceId);
      if (!service) return;

      for (const depId of service.dependencies) {
        if (!visited.has(depId)) {
          detectCycle(depId, [...path, depId]);
        } else if (recursionStack.has(depId)) {
          // Found cycle
          const cycleStart = path.indexOf(depId);
          cycles.push(path.slice(cycleStart));
        }
      }

      recursionStack.delete(serviceId);
    };

    for (const service of services) {
      if (!visited.has(service.id)) {
        detectCycle(service.id, [service.id]);
      }
    }

    return cycles;
  }, [services]);

  // Get service impact
  const getServiceImpact = (serviceId: string) => {
    const visited = new Set<string>();
    const impact: string[] = [];

    const collectImpact = (id: string) => {
      if (visited.has(id)) return;
      visited.add(id);
      impact.push(id);

      const service = services.find(s => s.id === id);
      if (service) {
        service.dependents.forEach(depId => collectImpact(depId));
      }
    };

    collectImpact(serviceId);
    return impact;
  };

  const renderServiceNode = (service: ServiceNode) => {
    const IconComponent = SERVICE_ICONS[service.type];
    const isSelected = selectedService === service.id;
    const statusColor = STATUS_COLORS[service.status];

    return (
      <g
        key={service.id}
        transform={`translate(${service.x},${service.y})`}
        style={{ cursor: 'pointer' }}
        onClick={() => setSelectedService(service.id)}
      >
        <circle
          r="30"
          fill={statusColor}
          fillOpacity={isSelected ? 0.8 : 0.6}
          stroke={isSelected ? '#000' : statusColor}
          strokeWidth={isSelected ? 3 : 1}
        />
        <foreignObject x="-12" y="-8" width="24" height="16">
          <IconComponent style={{ fontSize: 16, color: 'white' }} />
        </foreignObject>
        <text
          y="45"
          textAnchor="middle"
          fontSize="12"
          fill="#333"
          fontWeight={isSelected ? 'bold' : 'normal'}
        >
          {service.name}
        </text>
      </g>
    );
  };

  const renderDependencyLines = () => {
    const lines: JSX.Element[] = [];

    positionedServices.forEach(service => {
      service.dependencies.forEach(depId => {
        const dependency = positionedServices.find(s => s.id === depId);
        if (!dependency || !service.x || !service.y || !dependency.x || !dependency.y) return;

        lines.push(
          <line
            key={`${service.id}-${depId}`}
            x1={service.x}
            y1={service.y}
            x2={dependency.x}
            y2={dependency.y}
            stroke="#666"
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
            opacity={selectedService && selectedService !== service.id && selectedService !== depId ? 0.3 : 0.8}
          />
        );
      });
    });

    return lines;
  };

  return (
    <MinimalErrorBoundary context={{ component: 'ServiceDependencyVisualization' }}>
      <Box>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" component="h2">
            <AccountTree sx={{ mr: 1, verticalAlign: 'middle' }} />
            Service Dependencies
          </Typography>

          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>View Mode</InputLabel>
              <Select
                value={viewMode}
                label="View Mode"
                onChange={(e) => setViewMode(e.target.value as any)}
              >
                <MenuItem value="dependency">Dependencies</MenuItem>
                <MenuItem value="impact">Impact Analysis</MenuItem>
              </Select>
            </FormControl>

            <Button variant="outlined" startIcon={<Refresh />}>
              Refresh
            </Button>
          </Stack>
        </Box>

        {/* Circular Dependencies Warning */}
        {circularDependencies.length > 0 && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Circular Dependencies Detected!</strong> Found {circularDependencies.length} circular dependency cycles.
            </Typography>
          </Alert>
        )}

        <Box display="flex" gap={3}>
          {/* Visualization */}
          <Card sx={{ flex: 1 }}>
            <CardContent>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6">Dependency Graph</Typography>
                <Stack direction="row" spacing={1}>
                  <IconButton size="small">
                    <ZoomIn />
                  </IconButton>
                  <IconButton size="small">
                    <ZoomOut />
                  </IconButton>
                  <IconButton size="small">
                    <CenterFocusStrong />
                  </IconButton>
                </Stack>
              </Box>

              <Box sx={{ border: '1px solid #ddd', borderRadius: 1, overflow: 'hidden' }}>
                <svg width="600" height="400" viewBox="0 0 600 400">
                  {/* Arrow marker definition */}
                  <defs>
                    <marker
                      id="arrowhead"
                      markerWidth="10"
                      markerHeight="7"
                      refX="9"
                      refY="3.5"
                      orient="auto"
                    >
                      <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                    </marker>
                  </defs>

                  {/* Dependency lines */}
                  <g>{renderDependencyLines()}</g>

                  {/* Service nodes */}
                  <g>{positionedServices.map(renderServiceNode)}</g>
                </svg>
              </Box>
            </CardContent>
          </Card>

          {/* Service Details */}
          <Card sx={{ width: 300 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Details
              </Typography>

              {selectedService ? (() => {
                const service = services.find(s => s.id === selectedService);
                if (!service) return null;

                const impact = getServiceImpact(service.id);
                const IconComponent = SERVICE_ICONS[service.type];

                return (
                  <Box>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      <Box
                        sx={{
                          p: 1,
                          borderRadius: 1,
                          backgroundColor: STATUS_COLORS[service.status] + '20',
                          color: STATUS_COLORS[service.status],
                        }}
                      >
                        <IconComponent />
                      </Box>
                      <Box>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {service.name}
                        </Typography>
                        <Chip
                          label={service.status}
                          size="small"
                          color={
                            service.status === 'healthy' ? 'success' :
                            service.status === 'warning' ? 'warning' : 'error'
                          }
                        />
                      </Box>
                    </Box>

                    <Typography variant="subtitle2" gutterBottom>
                      Dependencies ({service.dependencies.length})
                    </Typography>
                    {service.dependencies.length > 0 ? (
                      <List dense>
                        {service.dependencies.map(depId => {
                          const dep = services.find(s => s.id === depId);
                          if (!dep) return null;
                          const DepIcon = SERVICE_ICONS[dep.type];

                          return (
                            <ListItem key={depId} sx={{ py: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 32 }}>
                                <DepIcon fontSize="small" />
                              </ListItemIcon>
                              <ListItemText
                                primary={dep.name}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          );
                        })}
                      </List>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No dependencies
                      </Typography>
                    )}

                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                      Dependents ({service.dependents.length})
                    </Typography>
                    {service.dependents.length > 0 ? (
                      <List dense>
                        {service.dependents.map(depId => {
                          const dep = services.find(s => s.id === depId);
                          if (!dep) return null;
                          const DepIcon = SERVICE_ICONS[dep.type];

                          return (
                            <ListItem key={depId} sx={{ py: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 32 }}>
                                <DepIcon fontSize="small" />
                              </ListItemIcon>
                              <ListItemText
                                primary={dep.name}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          );
                        })}
                      </List>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No dependents
                      </Typography>
                    )}

                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                      Impact Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      If this service fails, it would affect {impact.length} service(s).
                    </Typography>
                  </Box>
                );
              })() : (
                <Typography variant="body2" color="text.secondary">
                  Select a service in the graph to view details.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Legend */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Legend
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={2}>
              {Object.entries(SERVICE_ICONS).map(([type, IconComponent]) => (
                <Chip
                  key={type}
                  icon={<IconComponent />}
                  label={type.charAt(0).toUpperCase() + type.slice(1)}
                  variant="outlined"
                />
              ))}
            </Box>
            <Box display="flex" gap={2} mt={2}>
              <Box display="flex" alignItems="center" gap={1}>
                <CheckCircle sx={{ color: STATUS_COLORS.healthy }} />
                <Typography variant="body2">Healthy</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Warning sx={{ color: STATUS_COLORS.warning }} />
                <Typography variant="body2">Warning</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Error sx={{ color: STATUS_COLORS.critical }} />
                <Typography variant="body2">Critical</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </MinimalErrorBoundary>
  );
};

export default ServiceDependencyVisualization;