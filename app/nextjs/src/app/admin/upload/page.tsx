'use client';

import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as FileIcon,
} from '@mui/icons-material';
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import ProtectedLayout from "../../../components/layout/ProtectedLayout";
import { useUpload } from '../../../hooks/useUpload';

export default function UploadPage() {
  const { enqueueSnackbar } = useSnackbar();
  const { files, addFiles, removeFile, uploadFiles, isUploading } = useUpload();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const { validationErrors } = addFiles(acceptedFiles);
    
    if (validationErrors.length > 0) {
      validationErrors.forEach(({ file, reason }) => {
        enqueueSnackbar(`${file}: ${reason}`, { variant: 'error' });
      });
    }
    
    if (acceptedFiles.length > validationErrors.length) {
      enqueueSnackbar(
        `Added ${acceptedFiles.length - validationErrors.length} file(s) for upload`,
        { variant: 'success' }
      );
    }
  }, [addFiles, enqueueSnackbar]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  });

  const handleUpload = async () => {
    try {
      await uploadFiles();
      enqueueSnackbar('Files uploaded and processing started!', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(
        error instanceof Error ? error.message : 'Upload failed',
        { variant: 'error' }
      );
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'uploading':
        return <LinearProgress sx={{ width: 20 }} />;
      default:
        return <FileIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'uploading':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    
      <ProtectedLayout title="Upload">
        <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            Upload Documents
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            Add new documents to the knowledge base. Supported formats: PDF, TXT, DOCX
          </Typography>
        </Box>

        {/* Upload Area */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? 'action.hover' : 'transparent',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  borderColor: 'primary.main',
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <input {...getInputProps()} />
              <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                or click to select files
              </Typography>
              <Button variant="contained" component="span">
                Select Files
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* File List */}
        {files.length > 0 && (
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Files to Upload ({files.length})
              </Typography>
              <List>
                {files.map((fileItem) => (
                  <ListItem
                    key={fileItem.id}
                    secondaryAction={
                      !isUploading && fileItem.status === 'pending' && (
                        <IconButton
                          edge="end"
                          onClick={() => removeFile(fileItem.id)}
                          disabled={isUploading}
                        >
                          <DeleteIcon />
                        </IconButton>
                      )
                    }
                  >
                    <ListItemIcon>
                      {getStatusIcon(fileItem.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={fileItem.file.name}
                      secondary={
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                          <Typography variant="body2" color="text.secondary" component="span">
                            {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                          <Chip
                            label={fileItem.status}
                            size="small"
                            color={getStatusColor(fileItem.status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                            variant="outlined"
                            component="span"
                          />
                          {fileItem.error && (
                            <Typography variant="body2" color="error" component="span">
                              {fileItem.error}
                            </Typography>
                          )}
                        </span>
                      }
                    />
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleUpload}
                  disabled={isUploading || files.length === 0}
                  startIcon={<UploadIcon />}
                >
                  {isUploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => window.location.reload()}
                  disabled={isUploading}
                >
                  Clear All
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Instructions */}
        <Alert severity="info">
          <Typography variant="body2" component="div" gutterBottom>
            <strong>Upload Instructions:</strong>
          </Typography>
          <Box component="ul" sx={{ margin: '8px 0', paddingLeft: '20px' }}>
            <Box component="li">Supported formats: PDF, TXT, DOCX</Box>
            <Box component="li">Maximum file size: 10MB per file</Box>
            <Box component="li">Files will be automatically processed and indexed</Box>
            <Box component="li">Processing may take a few minutes depending on file size</Box>
          </Box>
        </Alert>
        </Container>
      </ProtectedLayout>
    
  );
}
