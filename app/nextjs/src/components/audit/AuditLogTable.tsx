'use client';

/**
 * Enterprise Audit Log Table Component
 *
 * Features:
 * - Advanced filtering and search capabilities
 * - Infinite scrolling for large datasets
 * - Real-time updates and sorting
 * - Export functionality for compliance
 * - Detailed audit entry modals
 * - Mobile-responsive design
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Avatar,
  Alert,
  CircularProgress,
  Button,
  Stack,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridRowParams,
  GridToolbar,
  GridActionsCellItem,
  GridRowId,
} from '@mui/x-data-grid';
import {
  Visibility,
  Download,
  FilterList,
  Refresh,
  Security,
  Person,
  Business,
  Computer,
  AccessTime,
  MoreVert,
  GetApp,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

import { useInfiniteAuditLogs, useDownloadAuditReport } from '../../services/api/audit/auditQueries';
import {
  AuditLog,
  AuditFilters,
  AuditSeverity,
  ActionType,
  formatActionType,
  formatResourceType,
  getSeverityColor,
  getActionTypeColor,
} from '../../services/api/audit/auditTypes';
import { MinimalErrorBoundary } from '../common/ErrorBoundary';
import { AuditLogDetailModal } from './AuditLogDetailModal';

interface AuditLogTableProps {
  filters: Partial<AuditFilters>;
  onFiltersChange: (filters: Partial<AuditFilters>) => void;
  onEntryClick: (entry: AuditLog) => void;
  showFilters?: boolean;
  height?: number;
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  filters,
  onFiltersChange,
  onEntryClick,
  showFilters = true,
  height = 600,
}) => {
  const [selectedRows, setSelectedRows] = useState<GridRowId[]>([]);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedAuditLog, setSelectedAuditLog] = useState<AuditLog | null>(null);

  // Fetch audit logs with infinite scrolling
  const {
    data: auditPages,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteAuditLogs(filters, {
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Export mutation
  const downloadReport = useDownloadAuditReport({
    onSuccess: () => {
      setExportMenuAnchor(null);
    },
  });

  // Flatten infinite query results
  const auditLogs = useMemo(() => {
    if (!auditPages) return [];
    return auditPages.pages.flatMap(page => page);
  }, [auditPages]);

  // Handle row selection
  const handleRowSelection = useCallback((newSelection: GridRowId[]) => {
    setSelectedRows(newSelection);
  }, []);

  // Handle export actions
  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
  };

  const handleExport = (format: 'csv' | 'json' | 'xlsx') => {
    downloadReport.mutate({
      format,
      filters: {
        ...filters,
        // If rows are selected, filter by their IDs
        ...(selectedRows.length > 0 && {
          // This would need backend support for ID filtering
        }),
      },
    });
  };

  // Handle refresh
  const handleRefresh = () => {
    refetch();
  };

  // Handle audit log detail modal
  const handleAuditLogClick = useCallback((auditLog: AuditLog) => {
    setSelectedAuditLog(auditLog);
    setDetailModalOpen(true);
    onEntryClick(auditLog);
  }, [onEntryClick]);

  const handleDetailModalClose = useCallback(() => {
    setDetailModalOpen(false);
    setSelectedAuditLog(null);
  }, []);

  const handleRelatedEntryClick = useCallback((relatedEntry: AuditLog) => {
    setSelectedAuditLog(relatedEntry);
    // Modal remains open, just switches to the new entry
  }, []);

  // Handle infinite scroll
  const handleScrollToBottom = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  // Define table columns
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'timestamp',
      headerName: 'Time',
      width: 160,
      renderCell: (params) => (
        <Tooltip title={format(new Date(params.value), 'PPpp')}>
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {format(new Date(params.value), 'MMM dd, HH:mm')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatDistanceToNow(new Date(params.value), { addSuffix: true })}
            </Typography>
          </Box>
        </Tooltip>
      ),
    },
    {
      field: 'action_type',
      headerName: 'Action',
      width: 200,
      renderCell: (params) => {
        const color = getActionTypeColor(params.value);
        return (
          <Chip
            label={formatActionType(params.value)}
            size="small"
            sx={{
              backgroundColor: color + '20',
              color: color,
              border: `1px solid ${color}40`,
            }}
          />
        );
      },
    },
    {
      field: 'user_id',
      headerName: 'User',
      width: 150,
      renderCell: (params) => (
        <Box display="flex" alignItems="center" gap={1}>
          <Avatar sx={{ width: 24, height: 24 }}>
            <Person fontSize="small" />
          </Avatar>
          <Typography variant="body2" noWrap>
            {params.value || 'Anonymous'}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'resource_type',
      headerName: 'Resource',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" color="text.secondary">
          {formatResourceType(params.value)}
        </Typography>
      ),
    },
    {
      field: 'ip_address',
      headerName: 'IP Address',
      width: 140,
      renderCell: (params) => (
        <Box display="flex" alignItems="center" gap={1}>
          <Computer fontSize="small" color="action" />
          <Typography variant="body2" fontFamily="monospace">
            {params.value || 'N/A'}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'severity',
      headerName: 'Severity',
      width: 100,
      renderCell: (params) => {
        const color = getSeverityColor(params.value);
        return (
          <Chip
            label={params.value.toUpperCase()}
            size="small"
            sx={{
              backgroundColor: color + '20',
              color: color,
              fontWeight: 'bold',
            }}
          />
        );
      },
    },
    {
      field: 'organization_id',
      headerName: 'Organization',
      width: 150,
      renderCell: (params) => (
        <Box display="flex" alignItems="center" gap={1}>
          <Business fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary" noWrap>
            {params.value || 'N/A'}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'compliance_tags',
      headerName: 'Compliance',
      width: 160,
      renderCell: (params) => {
        const tags = params.value || [];
        return (
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
            {tags.slice(0, 2).map((tag: string) => (
              <Chip
                key={tag}
                label={tag}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            ))}
            {tags.length > 2 && (
              <Typography variant="caption" color="text.secondary">
                +{tags.length - 2} more
              </Typography>
            )}
          </Stack>
        );
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 80,
      getActions: (params: GridRowParams<AuditLog>) => [
        <GridActionsCellItem
          key="view"
          icon={<Visibility />}
          label="View Details"
          onClick={() => handleAuditLogClick(params.row)}
        />,
      ],
    },
  ], [handleAuditLogClick]);

  // Error state
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
        Failed to load audit logs: {error?.message}
      </Alert>
    );
  }

  return (
    <MinimalErrorBoundary context={{ component: 'AuditLogTable' }}>
      <Card>
        <CardContent sx={{ p: 0 }}>
          {/* Table Header with Actions */}
          <Box
            sx={{
              p: 2,
              pb: 0,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box>
              <Typography variant="h6" component="h2">
                Audit Trail
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {auditLogs.length} entries loaded
                {hasNextPage && ' • More available'}
              </Typography>
            </Box>

            <Stack direction="row" spacing={1}>
              {/* Refresh Button */}
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh} disabled={isLoading}>
                  <Refresh />
                </IconButton>
              </Tooltip>

              {/* Export Button */}
              <Tooltip title="Export">
                <IconButton onClick={handleExportClick}>
                  <Download />
                </IconButton>
              </Tooltip>

              {/* Export Menu */}
              <Menu
                anchorEl={exportMenuAnchor}
                open={Boolean(exportMenuAnchor)}
                onClose={handleExportClose}
              >
                <MenuItem onClick={() => handleExport('csv')}>
                  <ListItemIcon>
                    <GetApp />
                  </ListItemIcon>
                  <ListItemText>Export as CSV</ListItemText>
                </MenuItem>
                <MenuItem onClick={() => handleExport('json')}>
                  <ListItemIcon>
                    <GetApp />
                  </ListItemIcon>
                  <ListItemText>Export as JSON</ListItemText>
                </MenuItem>
                <MenuItem onClick={() => handleExport('xlsx')}>
                  <ListItemIcon>
                    <GetApp />
                  </ListItemIcon>
                  <ListItemText>Export as Excel</ListItemText>
                </MenuItem>
              </Menu>
            </Stack>
          </Box>

          {/* Data Grid */}
          <Box sx={{ height, width: '100%' }}>
            <DataGrid
              rows={auditLogs}
              columns={columns}
              loading={isLoading}
              checkboxSelection
              disableRowSelectionOnClick
              rowSelectionModel={selectedRows}
              onRowSelectionModelChange={handleRowSelection}
              onRowDoubleClick={(params) => handleAuditLogClick(params.row)}
              slots={{
                toolbar: showFilters ? GridToolbar : undefined,
                loadingOverlay: () => (
                  <Box
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    height="100%"
                  >
                    <CircularProgress />
                  </Box>
                ),
              }}
              slotProps={{
                toolbar: {
                  showQuickFilter: true,
                  quickFilterProps: { debounceMs: 500 },
                },
              }}
              initialState={{
                sorting: {
                  sortModel: [{ field: 'timestamp', sort: 'desc' }],
                },
              }}
              pageSizeOptions={[25, 50, 100]}
              onScrollPositionChange={(params) => {
                // Check if scrolled to bottom for infinite loading
                const { top } = params;
                if (top > 0.9 && hasNextPage && !isFetchingNextPage) {
                  handleScrollToBottom();
                }
              }}
              sx={{
                border: 0,
                '& .MuiDataGrid-cell': {
                  borderBottom: '1px solid',
                  borderBottomColor: 'divider',
                },
                '& .MuiDataGrid-columnHeaders': {
                  backgroundColor: 'grey.50',
                  borderBottom: '2px solid',
                  borderBottomColor: 'divider',
                },
                '& .MuiDataGrid-row': {
                  '&:hover': {
                    backgroundColor: 'action.hover',
                    cursor: 'pointer',
                  },
                },
              }}
            />
          </Box>

          {/* Loading indicator for infinite scroll */}
          {isFetchingNextPage && (
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ ml: 1 }}>
                Loading more entries...
              </Typography>
            </Box>
          )}

          {/* No more data indicator */}
          {!hasNextPage && auditLogs.length > 0 && (
            <Box display="flex" justifyContent="center" p={2}>
              <Typography variant="body2" color="text.secondary">
                No more audit entries to load
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Audit Log Detail Modal */}
      <AuditLogDetailModal
        auditLog={selectedAuditLog}
        open={detailModalOpen}
        onClose={handleDetailModalClose}
        onRelatedEntryClick={handleRelatedEntryClick}
      />
    </MinimalErrorBoundary>
  );
};

export default AuditLogTable;