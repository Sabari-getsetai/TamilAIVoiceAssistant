'use client';

import React from 'react';
import {
  Box,
  Grid,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Switch,
  FormControlLabel,
  Snackbar
} from '@mui/material';
import {
  Warning as WarningIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  People as PeopleIcon,
  Storage as StorageIcon,
  Backup as BackupIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

import { Organization, OrganizationRole } from '@/types/organization';
import { organizationApi } from '@/services/api/organizationApi';

interface AdvancedSettingsProps {
  organization: Organization;
  userRole?: string;
}

export default function AdvancedSettings({ organization, userRole }: AdvancedSettingsProps) {
  const [memberLimit, setMemberLimit] = React.useState(organization.settings?.memberLimit || 25);
  const [dataRetention, setDataRetention] = React.useState(organization.settings?.dataRetentionDays || 365);
  const [apiAccess, setApiAccess] = React.useState<boolean>(Boolean(organization.settings?.apiAccess));
  const [ssoEnabled, setSsoEnabled] = React.useState<boolean>(Boolean(organization.settings?.ssoEnabled));

  // Danger zone dialogs
  const [exportDialogOpen, setExportDialogOpen] = React.useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = React.useState('');

  const [isLoading, setIsLoading] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const isOwner = userRole === 'owner';
  const isOwnerOrAdmin = userRole === 'owner' || userRole === 'ORG_ADMIN';

  const handleSaveSettings = async () => {
    setIsLoading(true);
    try {
      await organizationApi.updateOrganization(organization.id, {
        settings: {
          ...organization.settings,
          memberLimit,
          dataRetentionDays: dataRetention,
          apiAccess,
          ssoEnabled
        }
      });
      setSnackbar({
        open: true,
        message: 'Advanced settings saved successfully!',
        severity: 'success'
      });
    } catch (error: any) {
      console.error('Error saving advanced settings:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to save advanced settings',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportData = async () => {
    setIsLoading(true);
    try {
      // TODO: Implement actual data export
      setTimeout(() => {
        setSnackbar({
          open: true,
          message: 'Data export initiated! You will receive an email when ready.',
          severity: 'info'
        });
        setExportDialogOpen(false);
        setIsLoading(false);
      }, 2000);
    } catch (error: any) {
      console.error('Error exporting data:', error);
      setSnackbar({
        open: true,
        message: 'Failed to initiate data export',
        severity: 'error'
      });
      setIsLoading(false);
    }
  };

  const handleDeleteOrganization = async () => {
    if (deleteConfirmText !== organization.name) {
      setSnackbar({
        open: true,
        message: 'Organization name does not match',
        severity: 'error'
      });
      return;
    }

    setIsLoading(true);
    try {
      await organizationApi.deleteOrganization(organization.id);
      setSnackbar({
        open: true,
        message: 'Organization deletion initiated. Redirecting...',
        severity: 'info'
      });
      // TODO: Redirect to organization selection page
      setTimeout(() => {
        window.location.href = '/setup/organization';
      }, 2000);
    } catch (error: any) {
      console.error('Error deleting organization:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to delete organization',
        severity: 'error'
      });
      setIsLoading(false);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Advanced Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure advanced options and manage organization data.
      </Typography>

      {!isOwnerOrAdmin && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Only organization owners and admins can access advanced settings.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Organization Limits */}
        <Grid size={{xs: 12, md: 6}}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Member Limits</Typography>
              </Box>

              <TextField
                fullWidth
                label="Maximum Members"
                type="number"
                value={memberLimit}
                onChange={(e) => setMemberLimit(Number(e.target.value))}
                disabled={!isOwnerOrAdmin}
                helperText="Set the maximum number of members for this organization"
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth disabled={!isOwnerOrAdmin}>
                <InputLabel>Data Retention (Days)</InputLabel>
                <Select
                  value={dataRetention}
                  onChange={(e) => setDataRetention(Number(e.target.value))}
                  label="Data Retention (Days)"
                >
                  <MenuItem value={90}>90 Days</MenuItem>
                  <MenuItem value={180}>180 Days</MenuItem>
                  <MenuItem value={365}>1 Year</MenuItem>
                  <MenuItem value={730}>2 Years</MenuItem>
                  <MenuItem value={-1}>Indefinite</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
            <CardActions>
              <Button
                variant="outlined"
                onClick={handleSaveSettings}
                disabled={!isOwnerOrAdmin || isLoading}
              >
                Save Limits
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid size={{xs: 12, md: 6}}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Security Settings</Typography>
              </Box>

              <List>
                <ListItem>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={apiAccess}
                        onChange={(e) => setApiAccess(e.target.checked)}
                        disabled={!isOwnerOrAdmin}
                      />
                    }
                    label="API Access"
                  />
                </ListItem>
                <ListItem>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={ssoEnabled}
                        onChange={(e) => setSsoEnabled(e.target.checked)}
                        disabled={!isOwnerOrAdmin}
                      />
                    }
                    label="Single Sign-On (SSO)"
                  />
                </ListItem>
              </List>

              <Alert severity="info" sx={{ mt: 2 }}>
                SSO configuration requires additional setup. Contact support for assistance.
              </Alert>
            </CardContent>
            <CardActions>
              <Button
                variant="outlined"
                onClick={handleSaveSettings}
                disabled={!isOwnerOrAdmin || isLoading}
              >
                Save Security
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Data Management */}
        <Grid size={{xs: 12}}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Data Management</Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid size={{xs: 12, md: 4}}>
                  <Button
                    variant="outlined"
                    startIcon={<BackupIcon />}
                    fullWidth
                    disabled={!isOwnerOrAdmin}
                    onClick={() => setExportDialogOpen(true)}
                  >
                    Export Organization Data
                  </Button>
                </Grid>
                <Grid size={{xs: 12, md: 4}}>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    fullWidth
                    disabled={!isOwnerOrAdmin}
                  >
                    Download Audit Log
                  </Button>
                </Grid>
                <Grid size={{xs: 12, md: 4}}>
                  <Button
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    fullWidth
                    disabled={!isOwnerOrAdmin}
                  >
                    Data Processing Settings
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Danger Zone */}
        <Grid size={{xs: 12}}>
          <Card sx={{ border: '2px solid', borderColor: 'error.main' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WarningIcon sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" color="error">
                  Danger Zone
                </Typography>
              </Box>

              <Alert severity="error" sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Irreversible Actions
                </Typography>
                These actions cannot be undone. Please proceed with extreme caution.
              </Alert>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleteDialogOpen(true)}
                  disabled={!isOwner}
                >
                  Delete Organization
                </Button>
                {!isOwner && (
                  <Chip
                    label="Owner Only"
                    color="error"
                    variant="outlined"
                    size="small"
                  />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Export Data Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Organization Data</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            This will create a comprehensive export of all your organization's data including:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <PeopleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Member information and roles" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <StorageIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Documents and conversations" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Settings and configuration" />
            </ListItem>
          </List>
          <Alert severity="info" sx={{ mt: 2 }}>
            The export will be sent to your billing email address when ready.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleExportData} variant="contained" disabled={isLoading}>
            {isLoading ? 'Initiating...' : 'Start Export'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Organization Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle sx={{ color: 'error.main' }}>
          Delete Organization
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              This action cannot be undone!
            </Typography>
            This will permanently delete the organization and all associated data including
            members, documents, conversations, and settings.
          </Alert>

          <Typography variant="body2" gutterBottom>
            Type <strong>{organization.name}</strong> to confirm deletion:
          </Typography>
          <TextField
            fullWidth
            placeholder={organization.name}
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            error={deleteConfirmText !== '' && deleteConfirmText !== organization.name}
            helperText={deleteConfirmText !== '' && deleteConfirmText !== organization.name ? 'Name does not match' : ''}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteOrganization}
            color="error"
            variant="contained"
            disabled={deleteConfirmText !== organization.name || isLoading}
          >
            {isLoading ? 'Deleting...' : 'Delete Organization'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}