'use client';

import React from 'react';
import {
  Box,
  Grid,
  TextField,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  Paper,
  Avatar,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Save as SaveIcon,
  Upload as UploadIcon,
  Business as BusinessIcon
} from '@mui/icons-material';

import { Organization, UpdateOrganizationRequest } from '@/types/organization';
import { organizationApi } from '@/services/api/organizationApi';

interface GeneralSettingsProps {
  organization: Organization;
}

// Common timezones list
const TIMEZONES = [
  'UTC',
  'Asia/Kolkata',
  'Asia/Dubai',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Australia/Sydney',
  'Asia/Tokyo',
  'Asia/Singapore'
];

// Organization size options
const ORG_SIZES = [
  { value: 'startup', label: 'Startup (1-10 employees)' },
  { value: 'small', label: 'Small (11-50 employees)' },
  { value: 'medium', label: 'Medium (51-200 employees)' },
  { value: 'large', label: 'Large (201-1000 employees)' },
  { value: 'enterprise', label: 'Enterprise (1000+ employees)' }
];

// Industry options
const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'Manufacturing',
  'Retail',
  'Consulting',
  'Government',
  'Non-profit',
  'Other'
];

export default function GeneralSettings({ organization }: GeneralSettingsProps) {
  const [formData, setFormData] = React.useState<UpdateOrganizationRequest>({
    name: organization.name || '',
    description: organization.description || '',
    website: organization.website || '',
    industry: organization.industry || '',
    size: organization.size || 'startup',
    timezone: organization.timezone || 'UTC',
    billing_email: organization.billing_email || ''
  });

  const [isLoading, setIsLoading] = React.useState(false);
  const [hasChanges, setHasChanges] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Track changes to enable auto-save indication
  React.useEffect(() => {
    const hasFormChanges = (
      formData.name !== organization.name ||
      formData.description !== (organization.description || '') ||
      formData.website !== (organization.website || '') ||
      formData.industry !== (organization.industry || '') ||
      formData.size !== organization.size ||
      formData.timezone !== organization.timezone ||
      formData.billing_email !== (organization.billing_email || '')
    );
    setHasChanges(hasFormChanges);
  }, [formData, organization]);

  const handleInputChange = (field: keyof UpdateOrganizationRequest) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSelectChange = (field: keyof UpdateOrganizationRequest) => (
    event: any
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSave = async () => {
    if (!hasChanges) return;

    setIsLoading(true);
    try {
      await organizationApi.updateOrganization(organization.id, formData);
      setSnackbar({
        open: true,
        message: 'Organization settings saved successfully!',
        severity: 'success'
      });
      setHasChanges(false);
    } catch (error: any) {
      console.error('Error saving organization settings:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to save organization settings',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleLogoUpload = () => {
    // TODO: Implement logo upload functionality
    console.log('Logo upload clicked - to be implemented');
    setSnackbar({
      open: true,
      message: 'Logo upload feature coming soon!',
      severity: 'info'
    });
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        General Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage your organization's basic information and preferences.
      </Typography>

      <Grid container spacing={3}>
        {/* Organization Logo */}
        <Grid size={{xs: 12}}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Organization Logo
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}
                variant="rounded"
              >
                <BusinessIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Upload a logo for your organization (recommended: 200x200px)
                </Typography>
                <Tooltip title="Logo upload feature coming soon">
                  <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={handleLogoUpload}
                    size="small"
                  >
                    Upload Logo
                  </Button>
                </Tooltip>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Basic Information */}
        <Grid size={{xs: 12, md: 6}}>
          <TextField
            fullWidth
            label="Organization Name"
            value={formData.name}
            onChange={handleInputChange('name')}
            required
            variant="outlined"
            helperText="The display name for your organization"
          />
        </Grid>

        <Grid size={{xs: 12, md: 6}}>
          <TextField
            fullWidth
            label="Website"
            value={formData.website}
            onChange={handleInputChange('website')}
            variant="outlined"
            placeholder="https://example.com"
            helperText="Your organization's website URL"
          />
        </Grid>

        <Grid size={{xs: 12}}>
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={handleInputChange('description')}
            multiline
            rows={3}
            variant="outlined"
            helperText="A brief description of your organization"
          />
        </Grid>

        {/* Organization Details */}
        <Grid size={{xs: 12, md: 6}}>
          <FormControl fullWidth>
            <InputLabel>Industry</InputLabel>
            <Select
              value={formData.industry}
              onChange={handleSelectChange('industry')}
              label="Industry"
            >
              <MenuItem value="">
                <em>Select Industry</em>
              </MenuItem>
              {INDUSTRIES.map((industry) => (
                <MenuItem key={industry} value={industry.toLowerCase()}>
                  {industry}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid size={{xs: 12, md: 6}}>
          <FormControl fullWidth>
            <InputLabel>Organization Size</InputLabel>
            <Select
              value={formData.size}
              onChange={handleSelectChange('size')}
              label="Organization Size"
            >
              {ORG_SIZES.map((size) => (
                <MenuItem key={size.value} value={size.value}>
                  {size.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Contact & Settings */}
        <Grid size={{xs: 12, md: 6}}>
          <TextField
            fullWidth
            label="Billing Email"
            value={formData.billing_email}
            onChange={handleInputChange('billing_email')}
            type="email"
            variant="outlined"
            helperText="Email address for billing and invoices"
          />
        </Grid>

        <Grid size={{xs: 12, md: 6}}>
          <FormControl fullWidth>
            <InputLabel>Timezone</InputLabel>
            <Select
              value={formData.timezone}
              onChange={handleSelectChange('timezone')}
              label="Timezone"
            >
              {TIMEZONES.map((timezone) => (
                <MenuItem key={timezone} value={timezone}>
                  {timezone}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Save Button */}
        <Grid size={{xs: 12}}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
            <Box>
              {hasChanges && (
                <Alert severity="info" sx={{ display: 'inline-flex' }}>
                  You have unsaved changes
                </Alert>
              )}
            </Box>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={!hasChanges || isLoading}
              size="large"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Grid>
      </Grid>

      {/* Success/Error Snackbar */}
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