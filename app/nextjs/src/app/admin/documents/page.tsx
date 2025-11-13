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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Description as DocumentIcon,
  CloudDownload as DownloadIcon,
  Sync as ReindexIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '../../../components/layout/ProtectedLayout';
import { useDocuments, useDeleteDocument, useGetDocument, useReindexDocument } from '../../../hooks/useDocuments';
import { formatNumber } from '../../../utils/format';
import type { Document } from '../../../types';

export default function DocumentsPage() {
  const router = useRouter();
  const { data: documents, isLoading: isFetching, refetch } = useDocuments();
  const deleteDocument = useDeleteDocument();
  const reindexDocument = useReindexDocument();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reindexDialogOpen, setReindexDialogOpen] = useState(false);
  const [viewDetailsDialogOpen, setViewDetailsDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({ open: false, message: '', severity: 'info' });

  // Fetch document details when viewing
  const { data: documentDetails, isLoading: isLoadingDetails } = useGetDocument(
    selectedDocument?.id || '',
    viewDetailsDialogOpen && !!selectedDocument
  );

  // Filter documents based on search term
  const documentList = documents || [];
  const filteredDocuments = documentList.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleBack = () => {
    router.push('/admin');
  };

  const handleRefresh = () => {
    refetch();
  };

  const handleViewDocument = (document: Document) => {
    setSelectedDocument(document);
    setViewDetailsDialogOpen(true);
  };

  const handleDeleteDocument = (document: Document) => {
    setSelectedDocument(document);
    setDeleteDialogOpen(true);
  };

  const handleReindexDocument = (document: Document) => {
    setSelectedDocument(document);
    setReindexDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!selectedDocument) return;

    try {
      await deleteDocument.mutateAsync(selectedDocument.id);
      showSnackbar(
        `Document "${selectedDocument.filename}" deleted successfully`,
        'success'
      );
      setDeleteDialogOpen(false);
      setSelectedDocument(null);
    } catch (error) {
      showSnackbar(
        `Failed to delete document: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    }
  };

  const confirmReindex = async () => {
    if (!selectedDocument) return;

    try {
      await reindexDocument.mutateAsync(selectedDocument.id);
      showSnackbar(
        `Document "${selectedDocument.filename}" re-indexed successfully`,
        'success'
      );
      setReindexDialogOpen(false);
      setSelectedDocument(null);
    } catch (error) {
      showSnackbar(
        `Failed to re-index document: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <ProtectedLayout title="Documents">
        <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <BackIcon />
          </IconButton>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
              Document Management
            </Typography>
            <Typography variant="h6" color="text.secondary">
              View and manage indexed documents in the knowledge base
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isFetching}
          >
            Refresh
          </Button>
        </Box>

        {/* Search and Filters */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ maxWidth: 400 }}
          />
        </Box>

        {/* Loading State */}
        {isFetching && (
          <Card>
            <CardContent>
              <Typography variant="body1" gutterBottom>
                Loading documents...
              </Typography>
              <LinearProgress />
            </CardContent>
          </Card>
        )}

        {/* No Documents State */}
        {!isFetching && (documentList.length === 0) && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No documents have been uploaded yet. 
            <Button 
              variant="text" 
              onClick={() => router.push('/admin/upload')}
              sx={{ ml: 1 }}
            >
              Upload some documents
            </Button>
          </Alert>
        )}

        {/* Documents Table */}
        {!isFetching && documents && documentList.length > 0 && (
          <>
            {/* Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="body1" color="text.secondary">
                Showing {filteredDocuments.length} of {documentList.length} documents
              </Typography>
            </Box>

            <TableContainer component={Paper} elevation={2}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Document</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Upload Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredDocuments.map((document : Document) => (
                    <TableRow key={document.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <DocumentIcon color="primary" />
                          <Box>
                            <Typography variant="body1" fontWeight="medium">
                              {document.original_filename}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              ID: {document.id}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatFileSize(document.file_size)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(document.upload_date)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={document.status}
                          color={getStatusColor(document.status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewDocument(document)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Re-index">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleReindexDocument(document)}
                              disabled={reindexDocument.isPending}
                            >
                              <ReindexIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteDocument(document)}
                              disabled={deleteDocument.isPending}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* No Search Results */}
            {filteredDocuments.length === 0 && searchTerm && (
              <Alert severity="info" sx={{ mt: 3 }}>
                No documents found matching &ldquo;{searchTerm}&rdquo;. Try a different search term.
              </Alert>
            )}
          </>
        )}

        {/* Document Details Dialog */}
        <Dialog
          open={viewDetailsDialogOpen}
          onClose={() => {
            setViewDetailsDialogOpen(false);
            setSelectedDocument(null);
          }}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Document Details
          </DialogTitle>
          <DialogContent>
            {isLoadingDetails ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : documentDetails ? (
              <Box sx={{ pt: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {documentDetails.filename}
                </Typography>
                <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                  ID: {documentDetails.id}
                </Typography>

                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2, mb: 3 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      File Size
                    </Typography>
                    <Typography variant="body1">
                      {formatFileSize(documentDetails.file_size)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Text Chunks
                    </Typography>
                    <Typography variant="body1">
                      {formatNumber(documentDetails.chunk_count)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Upload Date
                    </Typography>
                    <Typography variant="body1">
                      {formatDate(documentDetails.upload_date)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Indexed At
                    </Typography>
                    <Typography variant="body1">
                      {documentDetails.indexed_at ? formatDate(documentDetails.indexed_at) : 'N/A'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                    <Chip
                      label={documentDetails.status}
                      color={getStatusColor(documentDetails.status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </Box>

                {documentDetails.text_preview && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Text Preview
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {documentDetails.text_preview}
                      </Typography>
                    </Paper>
                  </Box>
                )}
              </Box>
            ) : null}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setViewDetailsDialogOpen(false);
              setSelectedDocument(null);
            }}>
              Close
            </Button>
          </DialogActions>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => !deleteDocument.isPending && setDeleteDialogOpen(false)}
        >
          <DialogTitle>
            Confirm Delete
          </DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete &ldquo;{selectedDocument?.filename}&rdquo;?
              This action cannot be undone and will remove the document from the knowledge base.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleteDocument.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmDelete}
              color="error"
              variant="contained"
              disabled={deleteDocument.isPending}
              startIcon={deleteDocument.isPending ? <CircularProgress size={20} /> : null}
            >
              {deleteDocument.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Reindex Confirmation Dialog */}
        <Dialog
          open={reindexDialogOpen}
          onClose={() => !reindexDocument.isPending && setReindexDialogOpen(false)}
        >
          <DialogTitle>
            Confirm Re-index
          </DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to re-index &ldquo;{selectedDocument?.filename}&rdquo;?
              This will re-process the document and update its embeddings in the vector store.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setReindexDialogOpen(false)}
              disabled={reindexDocument.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={confirmReindex}
              color="primary"
              variant="contained"
              disabled={reindexDocument.isPending}
              startIcon={reindexDocument.isPending ? <CircularProgress size={20} /> : null}
            >
              {reindexDocument.isPending ? 'Re-indexing...' : 'Re-index'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
        </Container>
    </ProtectedLayout>
  );
}
