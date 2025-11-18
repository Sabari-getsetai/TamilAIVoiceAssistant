'use client';

import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  LinearProgress,
  IconButton,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon,
  Description as DocumentIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useStats } from '../../../hooks/useStats';
import { formatNumber } from '../../../utils/format';

export default function StatisticsPage() {
  const router = useRouter();
  const { data: stats, isLoading, refetch } = useStats();

  const handleBack = () => {
    router.push('/admin');
  };

  const handleRefresh = () => {
    refetch();
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Mock performance data (in a real app, this would come from the API)
  const performanceMetrics = [
    { metric: 'Average Query Time', value: '245ms', status: 'good' },
    { metric: 'Index Load Time', value: '1.2s', status: 'good' },
    { metric: 'Memory Usage', value: '512MB', status: 'warning' },
    { metric: 'CPU Usage', value: '15%', status: 'good' },
  ];

  const systemHealth = [
    { component: 'Vector Database', status: 'healthy', uptime: '99.9%' },
    { component: 'Embedding Service', status: 'healthy', uptime: '99.8%' },
    { component: 'Document Parser', status: 'healthy', uptime: '99.7%' },
    { component: 'Search Engine', status: 'healthy', uptime: '99.9%' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
      case 'unhealthy':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <BackIcon />
          </IconButton>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
              System Statistics
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Monitor system performance, usage analytics, and health metrics
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </Box>

        {/* Loading State */}
        {isLoading && (
          <Card>
            <CardContent>
              <Typography variant="body1" gutterBottom>
                Loading statistics...
              </Typography>
              <LinearProgress />
            </CardContent>
          </Card>
        )}

        {/* No Data State */}
        {!isLoading && !stats?.exists && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No statistics available yet. Upload some documents to generate analytics data.
          </Alert>
        )}

        {/* Statistics Content */}
        {!isLoading && stats && (
          <>
            {/* Overview Cards */}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 3, mb: 4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <DocumentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography color="text.secondary" gutterBottom>
                    Total Documents
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {stats.total_documents ? formatNumber(stats.total_documents) : '0'}
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AnalyticsIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography color="text.secondary" gutterBottom>
                    Text Chunks
                  </Typography>
                  <Typography variant="h4" component="div" color="secondary">
                    {stats.total_chunks ? formatNumber(stats.total_chunks) : '0'}
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <StorageIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography color="text.secondary" gutterBottom>
                    Index Size
                  </Typography>
                  <Typography variant="h4" component="div" color="info.main">
                    {stats.index_size_mb ? formatFileSize(stats.index_size_mb * 1024 * 1024) : '0 MB'}
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <MemoryIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                  <Typography color="text.secondary" gutterBottom>
                    Embedding Dimension
                  </Typography>
                  <Typography variant="h4" component="div" color="warning.main">
                    {stats.embedding_dimension || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            {/* System Information */}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <AssessmentIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6" fontWeight="bold">
                      System Information
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'grid', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        Embedding Model
                      </Typography>
                      <Typography variant="body2" fontWeight="medium">
                        {stats.embedding_model || 'Default'}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        Last Updated
                      </Typography>
                      <Typography variant="body2" fontWeight="medium">
                        {formatDate(stats.last_updated)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        Index Status
                      </Typography>
                      <Chip
                        label={stats.exists ? 'Active' : 'Inactive'}
                        color={stats.exists ? 'success' : 'error'}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <SpeedIcon sx={{ mr: 1, color: 'success.main' }} />
                    <Typography variant="h6" fontWeight="bold">
                      Performance Metrics
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'grid', gap: 2 }}>
                    {performanceMetrics.map((metric, index) => (
                      <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          {metric.metric}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight="medium">
                            {metric.value}
                          </Typography>
                          <Chip
                            size="small"
                            variant="outlined"
                            color={getStatusColor(metric.status) as 'success' | 'warning' | 'error' | 'default'}
                            sx={{ minWidth: 60, fontSize: '0.7rem' }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Box>

            {/* System Health Table */}
            <Card sx={{ mb: 4 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <TimelineIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6" fontWeight="bold">
                    System Health
                  </Typography>
                </Box>
                <TableContainer component={Paper} elevation={0}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Component</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Uptime</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {systemHealth.map((component, index) => (
                        <TableRow key={index} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {component.component}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={component.status}
                              color={getStatusColor(component.status) as 'success' | 'warning' | 'error' | 'default'}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {component.uptime}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Button size="small" variant="outlined" disabled>
                              Monitor
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>

            {/* Usage Analytics Placeholder */}
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'secondary.main' }} />
                  <Typography variant="h6" fontWeight="bold">
                    Usage Analytics
                  </Typography>
                </Box>
                <Alert severity="info">
                  Usage analytics and charts will be available in a future update. 
                  This section will include query patterns, popular documents, and usage trends.
                </Alert>
              </CardContent>
            </Card>
          </>
        )}
      </Container>
  );
}
