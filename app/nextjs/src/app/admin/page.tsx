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
import { useStats } from '../../hooks/useStats';
import { formatNumber } from '../../utils/format';

export default function AdminDashboard() {
  const router = useRouter();
  const { data: stats, isLoading: statsLoading, refetch } = useStats();

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const handleRefresh = () => {
    console.log(stats);
    refetch();
  };

  return (
      <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            System Administration
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            System-wide administration for platform management, user oversight, and global configuration
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            This is the system administration panel. For organization management, please visit the
            <Button variant="text" onClick={() => router.push('/org')} sx={{ mx: 1 }}>
              Organization Dashboard
            </Button>
          </Alert>
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
              {!stats ? (
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

        {/* System Administration Actions */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            System Administration
          </Typography>
          <Box sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
            gap: 3
          }}>
            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/users')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Manage Users
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  View and manage all users across organizations
                </Typography>
                <Button variant="contained" sx={{ mt: 2 }}>
                  User Management
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/organizations')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <DocumentsIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Manage Organizations
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  View and manage all organizations in the system
                </Typography>
                <Button variant="contained" color="secondary" sx={{ mt: 2 }}>
                  Organization Management
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/system-stats')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <StatsIcon sx={{ fontSize: 48, color: 'info.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  System Analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Platform-wide statistics and performance monitoring
                </Typography>
                <Button variant="contained" color="info" sx={{ mt: 2 }}>
                  View System Stats
                </Button>
              </CardContent>
            </Card>

            <Card sx={{ cursor: 'pointer' }} onClick={() => handleNavigation('/admin/settings')}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <SettingsIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Platform Settings
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Global platform configuration and system settings
                </Typography>
                <Button variant="contained" color="warning" sx={{ mt: 2 }}>
                  Platform Settings
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Box>
        </Container>
  );
}
