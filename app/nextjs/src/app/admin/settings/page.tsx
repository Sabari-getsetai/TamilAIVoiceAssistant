'use client';

import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { useSnackbar } from 'notistack';
import ProtectedLayout from "../../../components/layout/ProtectedLayout";
import { useStats } from '../../../hooks/useStats';
import { AdminApiService } from '../../../services/api/adminApi';

export default function SettingsPage() {
  const { enqueueSnackbar } = useSnackbar();
  const { data: stats, isLoading: statsLoading, refetch } = useStats();
  const [reindexDialog, setReindexDialog] = useState(false);
  const [clearDialog, setClearDialog] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      await AdminApiService.reindexDocuments();
      enqueueSnackbar('Reindexing started successfully!', { variant: 'success' });
      setReindexDialog(false);
      refetch();
    } catch (error) {
      enqueueSnackbar('Failed to start reindexing', { variant: 'error' });
    } finally {
      setIsReindexing(false);
    }
  };

  const handleClearIndex = async () => {
    setIsClearing(true);
    try {
      await AdminApiService.clearIndex();
      enqueueSnackbar('Index cleared successfully!', { variant: 'success' });
      setClearDialog(false);
      refetch();
    } catch (error) {
      enqueueSnackbar('Failed to clear index', { variant: 'error' });
    } finally {
      setIsClearing(false);
    }
  };

  return (
    
      <ProtectedLayout title="Settings">
      <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            System Settings
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            Configure system settings and manage the document index
          </Typography>
        </Box>

        {/* System Status */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current System Status
            </Typography>
            
            {statsLoading ? (
              <LinearProgress sx={{ mb: 2 }} />
            ) : (
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                  <Chip
                    label={stats?.exists ? 'Index Active' : 'No Index'}
                    color={stats?.exists ? 'success' : 'warning'}
                    icon={<SettingsIcon />}
                  />
                  <Chip
                    label={`${stats?.total_documents || 0} Documents`}
                    color="primary"
                  />
                  <Chip
                    label={`${stats?.total_chunks || 0} Chunks`}
                    color="secondary"
                  />
                  <Chip
                    label={`${stats?.index_size_mb?.toFixed(1) || '0'} MB`}
                    color="info"
                  />
                </Box>
                
                {stats?.last_updated && (
                  <Typography variant="body2" color="text.secondary">
                    Last updated: {new Date(stats.last_updated).toLocaleString()}
                  </Typography>
                )}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Index Management */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Index Management
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Manage the document index and perform maintenance operations
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={() => setReindexDialog(true)}
                disabled={isReindexing || !stats?.exists}
              >
                Reindex Documents
              </Button>
              
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => setClearDialog(true)}
                disabled={isClearing || !stats?.exists}
              >
                Clear Index
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* System Information */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
              gap: 3 
            }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Backend Configuration
                </Typography>
                <Typography variant="body2">
                  • API Endpoint: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                </Typography>
                <Typography variant="body2">
                  • Environment: {process.env.NODE_ENV || 'development'}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Supported Formats
                </Typography>
                <Typography variant="body2">
                  • PDF Documents (.pdf)
                </Typography>
                <Typography variant="body2">
                  • Text Files (.txt)
                </Typography>
                <Typography variant="body2">
                  • Word Documents (.docx)
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Warnings */}
        <Alert severity="warning" icon={<WarningIcon />}>
          <Typography variant="body2">
            <strong>Important:</strong> Reindexing will rebuild the entire search index and may take several minutes. 
            Clearing the index will permanently remove all indexed documents and cannot be undone.
          </Typography>
        </Alert>

        {/* Reindex Confirmation Dialog */}
        <Dialog open={reindexDialog} onClose={() => setReindexDialog(false)}>
          <DialogTitle>Confirm Reindex</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to reindex all documents? This will rebuild the entire search index 
              and may take several minutes to complete. The system will remain available during this process.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setReindexDialog(false)}>Cancel</Button>
            <Button 
              onClick={handleReindex} 
              variant="contained" 
              disabled={isReindexing}
            >
              {isReindexing ? 'Reindexing...' : 'Reindex'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Clear Index Confirmation Dialog */}
        <Dialog open={clearDialog} onClose={() => setClearDialog(false)}>
          <DialogTitle>Confirm Clear Index</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to clear the entire index? This will permanently remove all 
              indexed documents and cannot be undone. You will need to re-upload and reindex 
              all documents to restore functionality.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setClearDialog(false)}>Cancel</Button>
            <Button 
              onClick={handleClearIndex} 
              variant="contained" 
              color="error"
              disabled={isClearing}
            >
              {isClearing ? 'Clearing...' : 'Clear Index'}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
      </ProtectedLayout>
    
  );
}
