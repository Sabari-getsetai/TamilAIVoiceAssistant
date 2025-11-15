'use client';

/**
 * Enterprise Audit Log Detail Modal Component
 *
 * Features:
 * - Comprehensive audit entry display
 * - JSON metadata viewer with syntax highlighting
 * - Compliance framework indicators
 * - Security risk assessment
 * - Related audit entries
 * - Detailed session information
 * - Mobile-responsive design
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Chip,
  Button,
  Divider,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Stack,
  Avatar,
  Link,
} from '@mui/material';
import {
  Close,
  Security,
  Person,
  Business,
  Computer,
  AccessTime,
  Warning,
  Info,
  CheckCircle,
  Error,
  Gavel,
  Timeline,
  Code,
  Download,
  Share,
  ExpandMore,
  LocationOn,
  Fingerprint,
  Shield,
  VpnKey,
  Assessment,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import { JSONTree } from 'react-json-tree';

import {
  AuditLog,
  AuditSeverity,
  ActionType,
  ResourceType,
  ComplianceTag,
  formatActionType,
  formatResourceType,
  getSeverityColor,
  getActionTypeColor,
  getComplianceColor,
} from '../../services/api/audit/auditTypes';
import { useUserAuditTrail } from '../../services/api/audit/auditQueries';
import { MinimalErrorBoundary } from '../common/ErrorBoundary';

interface AuditLogDetailModalProps {
  auditLog: AuditLog | null;
  open: boolean;
  onClose: () => void;
  onRelatedEntryClick?: (entry: AuditLog) => void;
}

// JSON Tree theme for syntax highlighting
const jsonTreeTheme = {
  scheme: 'monokai',
  author: 'wimer hazenberg (http://www.monokai.nl)',
  base00: '#272822',
  base01: '#383830',
  base02: '#49483e',
  base03: '#75715e',
  base04: '#a59f85',
  base05: '#f8f8f2',
  base06: '#f5f4f1',
  base07: '#f9f8f5',
  base08: '#f92672',
  base09: '#fd971f',
  base0A: '#f4bf75',
  base0B: '#a6e22e',
  base0C: '#a1efe4',
  base0D: '#66d9ef',
  base0E: '#ae81ff',
  base0F: '#cc6633',
};

const getSeverityIcon = (severity: AuditSeverity) => {
  switch (severity) {
    case 'critical':
      return <Error color="error" />;
    case 'high':
      return <Warning color="warning" />;
    case 'medium':
      return <Info color="info" />;
    case 'low':
      return <CheckCircle color="success" />;
    default:
      return <Info color="action" />;
  }
};

const getComplianceIcon = (tag: ComplianceTag) => {
  switch (tag) {
    case 'GDPR':
      return <Shield />;
    case 'SOC2':
      return <Security />;
    case 'HIPAA':
      return <Gavel />;
    case 'ISO27001':
      return <Assessment />;
    case 'PCI_DSS':
      return <VpnKey />;
    case 'CCPA':
      return <Shield />;
    default:
      return <Security />;
  }
};

export const AuditLogDetailModal: React.FC<AuditLogDetailModalProps> = ({
  auditLog,
  open,
  onClose,
  onRelatedEntryClick,
}) => {
  const [expandedSection, setExpandedSection] = useState<string | false>('overview');

  // Fetch related audit entries for the same user
  const {
    data: relatedEntries,
    isLoading: isLoadingRelated,
  } = useUserAuditTrail(
    auditLog?.user_id || '',
    7, // Last 7 days
    {
      enabled: !!auditLog?.user_id && open,
    }
  );

  if (!auditLog) return null;

  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedSection(isExpanded ? panel : false);
  };

  const handleExportEntry = () => {
    const exportData = {
      ...auditLog,
      exported_at: new Date().toISOString(),
      exported_by: 'current_user', // Would come from auth context
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-entry-${auditLog.id}.json`;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleShareEntry = () => {
    const shareUrl = `${window.location.origin}/admin/audit/${auditLog.id}`;
    navigator.clipboard.writeText(shareUrl);
    // Would show a toast notification in a real app
  };

  // Filter out the current entry from related entries
  const filteredRelatedEntries = relatedEntries?.filter(
    entry => entry.id !== auditLog.id
  ).slice(0, 5); // Show max 5 related entries

  const riskScore = auditLog.severity === 'critical' ? 95 :
                   auditLog.severity === 'high' ? 75 :
                   auditLog.severity === 'medium' ? 45 : 25;

  return (
    <MinimalErrorBoundary context={{ component: 'AuditLogDetailModal' }}>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { minHeight: '70vh', maxHeight: '90vh' }
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            pb: 1,
          }}
        >
          <Box display="flex" alignItems="center" gap={2}>
            {getSeverityIcon(auditLog.severity)}
            <Box>
              <Typography variant="h6" component="div">
                {formatActionType(auditLog.action_type)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {format(new Date(auditLog.timestamp), 'PPpp')}
              </Typography>
            </Box>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title="Export Entry">
              <IconButton onClick={handleExportEntry} size="small">
                <Download />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share Entry">
              <IconButton onClick={handleShareEntry} size="small">
                <Share />
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ px: 0 }}>
          {/* Overview Section */}
          <Accordion
            expanded={expandedSection === 'overview'}
            onChange={handleAccordionChange('overview')}
            sx={{ mx: 3, mb: 1 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Info />
                Overview
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        <Person sx={{ mr: 1, verticalAlign: 'middle' }} />
                        User Information
                      </Typography>
                      <Box sx={{ ml: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          User ID: {auditLog.user_id || 'Anonymous'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Session ID: {auditLog.session_id || 'N/A'}
                        </Typography>
                        {auditLog.organization_id && (
                          <Typography variant="body2" color="text.secondary">
                            Organization: {auditLog.organization_id}
                          </Typography>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Resource Information */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Resource Details
                      </Typography>
                      <Box sx={{ ml: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          Type: {formatResourceType(auditLog.resource_type)}
                        </Typography>
                        {auditLog.resource_id && (
                          <Typography variant="body2" color="text.secondary">
                            ID: {auditLog.resource_id}
                          </Typography>
                        )}
                        {auditLog.outcome && (
                          <Typography variant="body2" color="text.secondary">
                            Outcome: {auditLog.outcome}
                          </Typography>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Technical Information */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        <Computer sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Technical Details
                      </Typography>
                      <Box sx={{ ml: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          IP Address: {auditLog.ip_address || 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          User Agent: {auditLog.user_agent ?
                            `${auditLog.user_agent.substring(0, 50)}...` : 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Request ID: {auditLog.request_id || 'N/A'}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Risk Assessment */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        <Shield sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Risk Assessment
                      </Typography>
                      <Box sx={{ ml: 4 }}>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Typography variant="body2">Risk Score:</Typography>
                          <Chip
                            label={`${riskScore}/100`}
                            size="small"
                            color={riskScore > 70 ? 'error' : riskScore > 40 ? 'warning' : 'success'}
                          />
                        </Box>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Typography variant="body2">Severity:</Typography>
                          <Chip
                            label={auditLog.severity.toUpperCase()}
                            size="small"
                            sx={{
                              backgroundColor: getSeverityColor(auditLog.severity) + '20',
                              color: getSeverityColor(auditLog.severity),
                            }}
                          />
                        </Box>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2">Action Type:</Typography>
                          <Chip
                            label={formatActionType(auditLog.action_type)}
                            size="small"
                            sx={{
                              backgroundColor: getActionTypeColor(auditLog.action_type) + '20',
                              color: getActionTypeColor(auditLog.action_type),
                            }}
                          />
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Compliance Section */}
          <Accordion
            expanded={expandedSection === 'compliance'}
            onChange={handleAccordionChange('compliance')}
            sx={{ mx: 3, mb: 1 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Gavel />
                Compliance & Frameworks
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {auditLog.compliance_tags && auditLog.compliance_tags.length > 0 ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    This audit entry is relevant to the following compliance frameworks:
                  </Typography>
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    {auditLog.compliance_tags.map((tag) => (
                      <Grid item key={tag}>
                        <Card variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
                            {getComplianceIcon(tag as ComplianceTag)}
                            <Chip
                              label={tag}
                              size="small"
                              sx={{
                                backgroundColor: getComplianceColor(tag as ComplianceTag) + '20',
                                color: getComplianceColor(tag as ComplianceTag),
                                fontWeight: 'bold',
                              }}
                            />
                          </Box>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  {/* Compliance Notes */}
                  <Alert severity="info" sx={{ mt: 3 }}>
                    <Typography variant="body2">
                      <strong>Compliance Note:</strong> This audit entry has been automatically
                      tagged for compliance frameworks based on the action type and resource involved.
                      Review your organization's compliance requirements for data retention and reporting.
                    </Typography>
                  </Alert>
                </Box>
              ) : (
                <Alert severity="warning">
                  <Typography variant="body2">
                    No specific compliance frameworks have been associated with this audit entry.
                  </Typography>
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Metadata Section */}
          <Accordion
            expanded={expandedSection === 'metadata'}
            onChange={handleAccordionChange('metadata')}
            sx={{ mx: 3, mb: 1 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Code />
                Technical Metadata
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {auditLog.metadata ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    Raw metadata associated with this audit entry:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#272822', mt: 2 }}>
                    <JSONTree
                      data={auditLog.metadata}
                      theme={jsonTreeTheme}
                      shouldExpandNode={() => true}
                      hideRoot={true}
                      invertTheme={false}
                    />
                  </Paper>
                </Box>
              ) : (
                <Alert severity="info">
                  <Typography variant="body2">
                    No additional metadata is available for this audit entry.
                  </Typography>
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Related Entries Section */}
          <Accordion
            expanded={expandedSection === 'related'}
            onChange={handleAccordionChange('related')}
            sx={{ mx: 3, mb: 1 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Timeline />
                Related Audit Entries
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {isLoadingRelated ? (
                <Typography variant="body2" color="text.secondary">
                  Loading related entries...
                </Typography>
              ) : filteredRelatedEntries && filteredRelatedEntries.length > 0 ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    Recent audit entries for the same user (last 7 days):
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                    <Table size="small">
                      <TableBody>
                        {filteredRelatedEntries.map((entry) => (
                          <TableRow
                            key={entry.id}
                            hover
                            sx={{
                              cursor: onRelatedEntryClick ? 'pointer' : 'default',
                              '&:hover': onRelatedEntryClick ? { backgroundColor: 'action.hover' } : {}
                            }}
                            onClick={onRelatedEntryClick ? () => onRelatedEntryClick(entry) : undefined}
                          >
                            <TableCell>
                              <Box display="flex" alignItems="center" gap={1}>
                                {getSeverityIcon(entry.severity)}
                                <Box>
                                  <Typography variant="body2" fontWeight="medium">
                                    {formatActionType(entry.action_type)}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                                  </Typography>
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {formatResourceType(entry.resource_type)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={entry.severity.toUpperCase()}
                                size="small"
                                sx={{
                                  backgroundColor: getSeverityColor(entry.severity) + '20',
                                  color: getSeverityColor(entry.severity),
                                }}
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              ) : (
                <Alert severity="info">
                  <Typography variant="body2">
                    No related audit entries found for this user in the last 7 days.
                  </Typography>
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={onClose} color="primary">
            Close
          </Button>
          <Button onClick={handleExportEntry} variant="outlined" startIcon={<Download />}>
            Export Entry
          </Button>
        </DialogActions>
      </Dialog>
    </MinimalErrorBoundary>
  );
};

export default AuditLogDetailModal;