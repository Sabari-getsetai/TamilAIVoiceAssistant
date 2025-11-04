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
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as DocumentsIcon,
  Analytics as StatsIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import MainLayout from '../../components/layout/MainLayout';
import { useStats } from '../../hooks/useStats';
import { formatNumber } from '../../utils/format';

export default function AdminDashboard() {
  const router = useRouter();
  const { data: stats, isLoading: statsLoading, refetch } = useStats();

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const handleRefresh = () => {
    refetch();
  };

  return (
    <MainLayout>
      <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            Admin Dashboard
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            Manage documents, monitor system performance, and configure settings
          </Typography>
        </Box>

        {/* System Status */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            System Overview
          </Typography>
          
          {statsLoading ? (
            <Card>
              <CardContent>
                <Typography variant="body1" gutterBottom>
                  Loading system status...
                </Typography>
                <LinearProgress />
              </CardContent>
            </Card>
          ) : (
            <>
              {!stats?.exists ? (
                <Alert severity="warning" sx={{ mb: 3 }}>
                  No documents have been indexed yet. Upload some documents to get started.
                </Alert>
              ) : (
                <Alert severity="success" sx={{ mb: 3 }}>
                  System is ready with {formatNumber(stats.total_documents || 0)} documents indexed.
                </Alert>
              )}

              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' },
                gap: 3 
              }}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography color="text.secondary" gutterBottom>
                      Documents
                    </Typography>
                    <Typography variant="h3" component="div" color="primary">
                      {stats?.total_documents ? formatNumber(stats.total_documents) : '0'}
                    </Typography>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography color="text.secondary" gutterBottom>
                      Text Chunks
                    </Typography>
                    <Typography variant="h3" component="div" color="secondary">
                      {stats?.total_chunks ? formatNumber(stats.total_chunks) : '0'}
                    </Typography>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography color="text.secondary" gutterBottom>
                      Index Size
                    </Typography>
                    <Typography variant="h3" component="div" color="info.main">
                      {stats?.index_size_mb ? `${stats.index_size_mb.toFixed(1)} MB` : '0 MB'}
                    </Typography>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography color="text.secondary" gutterBottom>
                      Status
                    </Typography>
                    <Typography variant="h4" component="div">
                      <Button
                        size="small"
                        startIcon={<RefreshIcon />}
                        onClick={handleRefresh}
                        variant="outlined"
                        sx={{ mt: 1 }}
                      >
                        Refresh Stats
                      </Button>
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </>
          )}
        </Box>

        {/* Quick Actions */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            Quick Actions
          </Typography>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
            gap: 3 
          }}>
            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/upload')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Upload Documents
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Add new documents to the knowledge base
                </Typography>
                <Button variant="contained" sx={{ mt: 2 }}>
                  Upload Files
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/documents')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <DocumentsIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Manage Documents
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  View and manage indexed documents
                </Typography>
                <Button variant="contained" color="secondary" sx={{ mt: 2 }}>
                  View Documents
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/statistics')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <StatsIcon sx={{ fontSize: 48, color: 'info.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  View Statistics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Monitor system performance and usage
                </Typography>
                <Button variant="contained" color="info" sx={{ mt: 2 }}>
                  View Stats
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/settings')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <SettingsIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  System Settings
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Configure system settings and reindex
                </Typography>
                <Button variant="contained" color="warning" sx={{ mt: 2 }}>
                  Settings
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Container>
    </MainLayout>
  );
}
