'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Save as SaveIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  Backup as BackupIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

// Mock organization settings data - replace with actual API integration
interface OrgSettings {
  basic: {
    name: string;
    description: string;
    website: string;
    timezone: string;
    language: string;
  };
  features: {
    aiAssistant: boolean;
    documentProcessing: boolean;
    teamCollaboration: boolean;
    apiAccess: boolean;
    advancedAnalytics: boolean;
  };
  notifications: {
    emailNotifications: boolean;
    documentUploaded: boolean;
    memberJoined: boolean;
    systemUpdates: boolean;
    securityAlerts: boolean;
  };
  security: {
    twoFactorRequired: boolean;
    sessionTimeout: number; // in minutes
    allowedDomains: string[];
    passwordPolicy: {
      minLength: number;
      requireSymbols: boolean;
      requireNumbers: boolean;
    };
  };
  storage: {
    used: number; // in MB
    limit: number; // in MB
    autoCleanup: boolean;
    retentionDays: number;
  };
}

const mockSettings: OrgSettings = {
  basic: {
    name: 'TechCorp AI Solutions',
    description: 'Advanced AI solutions for modern enterprises',
    website: 'https://techcorp.com',
    timezone: 'Asia/Kolkata',
    language: 'en',
  },
  features: {
    aiAssistant: true,
    documentProcessing: true,
    teamCollaboration: true,
    apiAccess: false,
    advancedAnalytics: true,
  },
  notifications: {
    emailNotifications: true,
    documentUploaded: true,
    memberJoined: true,
    systemUpdates: false,
    securityAlerts: true,
  },
  security: {
    twoFactorRequired: true,
    sessionTimeout: 480, // 8 hours
    allowedDomains: ['techcorp.com', 'subsidiary.com'],
    passwordPolicy: {
      minLength: 8,
      requireSymbols: true,
      requireNumbers: true,
    },
  },
  storage: {
    used: 2400, // 2.4 GB
    limit: 10000, // 10 GB
    autoCleanup: true,
    retentionDays: 365,
  },
};

export default function OrgSettingsPage() {
  const [settings, setSettings] = useState<OrgSettings>(mockSettings);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [domainDialogOpen, setDomainDialogOpen] = useState(false);
  const [newDomain, setNewDomain] = useState('');

  const handleSettingChange = (section: keyof OrgSettings, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
    setIsDirty(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement API call to save settings
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsDirty(false);
      // TODO: Show success notification
    } catch (error) {
      // TODO: Show error notification
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddDomain = () => {
    if (newDomain && !settings.security.allowedDomains.includes(newDomain)) {
      handleSettingChange('security', 'allowedDomains', [
        ...settings.security.allowedDomains,
        newDomain,
      ]);
      setNewDomain('');
      setDomainDialogOpen(false);
    }
  };

  const handleRemoveDomain = (domain: string) => {
    handleSettingChange(
      'security',
      'allowedDomains',
      settings.security.allowedDomains.filter(d => d !== domain)
    );
  };

  const formatStorage = (mb: number) => {
    if (mb < 1000) {
      return `${mb} MB`;
    }
    return `${(mb / 1000).toFixed(1)} GB`;
  };

  const getStoragePercentage = () => {
    return (settings.storage.used / settings.storage.limit) * 100;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            Organization Settings
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure your organization preferences and security settings
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={!isDirty || isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </Box>

      {/* Change indicator */}
      {isDirty && (
        <Alert severity="info" sx={{ mb: 3 }}>
          You have unsaved changes. Don't forget to save your settings.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Basic Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <BusinessIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6">Basic Information</Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Organization Name"
                    value={settings.basic.name}
                    onChange={(e) => handleSettingChange('basic', 'name', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Website URL"
                    value={settings.basic.website}
                    onChange={(e) => handleSettingChange('basic', 'website', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Description"
                    value={settings.basic.description}
                    onChange={(e) => handleSettingChange('basic', 'description', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Timezone</InputLabel>
                    <Select
                      value={settings.basic.timezone}
                      onChange={(e) => handleSettingChange('basic', 'timezone', e.target.value)}
                      label="Timezone"
                    >
                      <MenuItem value="Asia/Kolkata">Asia/Kolkata (IST)</MenuItem>
                      <MenuItem value="America/New_York">America/New_York (EST)</MenuItem>
                      <MenuItem value="Europe/London">Europe/London (GMT)</MenuItem>
                      <MenuItem value="Asia/Tokyo">Asia/Tokyo (JST)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Default Language</InputLabel>
                    <Select
                      value={settings.basic.language}
                      onChange={(e) => handleSettingChange('basic', 'language', e.target.value)}
                      label="Default Language"
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="ta">தமிழ் (Tamil)</MenuItem>
                      <MenuItem value="hi">हिंदी (Hindi)</MenuItem>
                      <MenuItem value="es">Español</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Feature Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <ApiIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6">Features & Access</Typography>
              </Box>

              <List>
                <ListItem>
                  <ListItemText
                    primary="AI Assistant"
                    secondary="Enable AI-powered conversations and assistance"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.features.aiAssistant}
                      onChange={(e) => handleSettingChange('features', 'aiAssistant', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Document Processing"
                    secondary="Automatic document indexing and search"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.features.documentProcessing}
                      onChange={(e) => handleSettingChange('features', 'documentProcessing', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Team Collaboration"
                    secondary="Shared workspaces and team features"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.features.teamCollaboration}
                      onChange={(e) => handleSettingChange('features', 'teamCollaboration', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="API Access"
                    secondary="Enable programmatic access via REST API"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.features.apiAccess}
                      onChange={(e) => handleSettingChange('features', 'apiAccess', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Advanced Analytics"
                    secondary="Detailed usage analytics and reporting"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.features.advancedAnalytics}
                      onChange={(e) => handleSettingChange('features', 'advancedAnalytics', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <SecurityIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6">Security</Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.twoFactorRequired}
                      onChange={(e) => handleSettingChange('security', 'twoFactorRequired', e.target.checked)}
                    />
                  }
                  label="Require Two-Factor Authentication"
                />
              </Box>

              <TextField
                fullWidth
                label="Session Timeout (minutes)"
                type="number"
                value={settings.security.sessionTimeout}
                onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                sx={{ mb: 3 }}
              />

              <Typography variant="subtitle2" gutterBottom>
                Allowed Email Domains
              </Typography>
              <Box sx={{ mb: 2 }}>
                {settings.security.allowedDomains.map((domain, index) => (
                  <Chip
                    key={index}
                    label={domain}
                    onDelete={() => handleRemoveDomain(domain)}
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setDomainDialogOpen(true)}
                  sx={{ mb: 1 }}
                >
                  Add Domain
                </Button>
              </Box>

              <Typography variant="subtitle2" gutterBottom>
                Password Policy
              </Typography>
              <TextField
                fullWidth
                label="Minimum Length"
                type="number"
                value={settings.security.passwordPolicy.minLength}
                onChange={(e) => handleSettingChange('security', 'passwordPolicy', {
                  ...settings.security.passwordPolicy,
                  minLength: parseInt(e.target.value),
                })}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.passwordPolicy.requireSymbols}
                    onChange={(e) => handleSettingChange('security', 'passwordPolicy', {
                      ...settings.security.passwordPolicy,
                      requireSymbols: e.target.checked,
                    })}
                  />
                }
                label="Require Symbols"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.passwordPolicy.requireNumbers}
                    onChange={(e) => handleSettingChange('security', 'passwordPolicy', {
                      ...settings.security.passwordPolicy,
                      requireNumbers: e.target.checked,
                    })}
                  />
                }
                label="Require Numbers"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <NotificationsIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6">Notifications</Typography>
              </Box>

              <List>
                <ListItem>
                  <ListItemText primary="Email Notifications" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.emailNotifications}
                      onChange={(e) => handleSettingChange('notifications', 'emailNotifications', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Document Uploaded" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.documentUploaded}
                      onChange={(e) => handleSettingChange('notifications', 'documentUploaded', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Member Joined" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.memberJoined}
                      onChange={(e) => handleSettingChange('notifications', 'memberJoined', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="System Updates" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.systemUpdates}
                      onChange={(e) => handleSettingChange('notifications', 'systemUpdates', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Security Alerts" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.notifications.securityAlerts}
                      onChange={(e) => handleSettingChange('notifications', 'securityAlerts', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Storage Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <StorageIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6">Storage & Data</Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Storage Usage: {formatStorage(settings.storage.used)} of {formatStorage(settings.storage.limit)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <Box
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'grey.200',
                        position: 'relative',
                      }}
                    >
                      <Box
                        sx={{
                          height: 8,
                          borderRadius: 1,
                          bgcolor: getStoragePercentage() > 80 ? 'error.main' : 'primary.main',
                          width: `${Math.min(getStoragePercentage(), 100)}%`,
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 40 }}>
                    {getStoragePercentage().toFixed(1)}%
                  </Typography>
                </Box>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.storage.autoCleanup}
                    onChange={(e) => handleSettingChange('storage', 'autoCleanup', e.target.checked)}
                  />
                }
                label="Auto-cleanup old data"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Data Retention (days)"
                type="number"
                value={settings.storage.retentionDays}
                onChange={(e) => handleSettingChange('storage', 'retentionDays', parseInt(e.target.value))}
                helperText="Data older than this will be automatically deleted if auto-cleanup is enabled"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Domain Dialog */}
      <Dialog open={domainDialogOpen} onClose={() => setDomainDialogOpen(false)}>
        <DialogTitle>Add Allowed Domain</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Domain"
            type="text"
            fullWidth
            variant="outlined"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="example.com"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDomainDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddDomain} variant="contained">
            Add Domain
          </Button>
        </DialogActions>
      </Dialog>

      {/* Implementation Notice */}
      <Alert severity="info" sx={{ mt: 3 }}>
        This settings page shows sample configuration options. Backend integration for saving and applying these settings is pending.
      </Alert>
    </Box>
  );
}