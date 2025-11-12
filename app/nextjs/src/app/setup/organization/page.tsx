'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Container,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { Business, GroupAdd } from '@mui/icons-material';
import { useAuth } from '@/contexts/AuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import type { CreateOrganizationRequest } from '@/types/organization';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`organization-tabpanel-${index}`}
      aria-labelledby={`organization-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function OrganizationSetupPage() {
  const router = useRouter();
  const { user } = useAuth();
  const {
    createOrganization,
    refreshOrganizations,
    isLoading: contextLoading,
    error: contextError,
    clearError
  } = useOrganization();

  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Create Organization Form State
  const [createForm, setCreateForm] = useState<CreateOrganizationRequest>({
    name: '',
    description: '',
    website: '',
    industry: '',
    size: 'startup',
    timezone: 'UTC',
  });

  // Join Organization Form State
  const [joinForm, setJoinForm] = useState({
    invitationCode: '',
    organizationName: '',
  });

  // Clear errors when component mounts or tab changes
  useEffect(() => {
    setError(null);
    setSuccess(null);
    clearError();
  }, [tabValue, clearError]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setError(null);
    setSuccess(null);
  };

  const handleCreateFormChange = (field: keyof CreateOrganizationRequest) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { value: string } }
  ) => {
    setCreateForm(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const handleJoinFormChange = (field: keyof typeof joinForm) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setJoinForm(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate form
      if (!createForm.name.trim()) {
        setError('Organization name is required');
        return;
      }

      // Clear any previous context errors
      clearError();

      // Create organization using context
      const organization = await createOrganization(createForm);

      if (!organization || !organization.id) {
        throw new Error('Invalid response from server');
      }

      setSuccess('Organization created successfully! Redirecting...');

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        router.push('/admin');
      }, 1500);
    } catch (err) {
      console.error('Organization creation error:', err);
      const error = err as Error;
      let errorMessage = 'Failed to create organization';
      
      // Extract more specific error message if available
      if (error.message) {
        if (error.message.includes('Failed to create organization:')) {
          errorMessage = error.message;
        } else if (error.message.includes('Network')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('401') || error.message.includes('403')) {
          errorMessage = 'Authentication error. Please log in again.';
        } else {
          errorMessage = error.message;
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // TODO: Implement join organization logic
      // This would typically involve:
      // 1. Validating invitation code
      // 2. Adding user to organization
      // 3. Setting as active organization
      
      setError('Join organization feature is coming soon!');
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Failed to join organization');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    // For now, just redirect to dashboard
    // In the future, we might want to create a default personal organization
    router.push('/');
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box textAlign="center" mb={4}>
          <Typography variant="h4" component="h1" gutterBottom>
            Welcome to Tamil AI Voice Assistant!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            To get started, you need to set up or join an organization.
            Organizations help you collaborate with your team and manage your AI assistant together.
          </Typography>
        </Box>

        {(error || contextError) && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error || contextError}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {success}
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="organization setup tabs">
            <Tab
              icon={<Business />}
              label="Create Organization"
              id="organization-tab-0"
              aria-controls="organization-tabpanel-0"
            />
            <Tab
              icon={<GroupAdd />}
              label="Join Organization"
              id="organization-tab-1"
              aria-controls="organization-tabpanel-1"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <form onSubmit={handleCreateOrganization}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <TextField
                label="Organization Name"
                value={createForm.name}
                onChange={handleCreateFormChange('name')}
                required
                fullWidth
                placeholder="e.g., Acme Corporation"
              />

              <TextField
                label="Description"
                value={createForm.description}
                onChange={handleCreateFormChange('description')}
                multiline
                rows={3}
                fullWidth
                placeholder="Brief description of your organization..."
              />

              <TextField
                label="Website"
                value={createForm.website}
                onChange={handleCreateFormChange('website')}
                fullWidth
                placeholder="https://www.example.com"
              />

              <TextField
                label="Industry"
                value={createForm.industry}
                onChange={handleCreateFormChange('industry')}
                fullWidth
                placeholder="e.g., Technology, Healthcare, Education"
              />

              <FormControl fullWidth>
                <InputLabel>Organization Size</InputLabel>
                <Select
                  value={createForm.size}
                  label="Organization Size"
                  onChange={handleCreateFormChange('size')}
                >
                  <MenuItem value="startup">Startup (1-10 employees)</MenuItem>
                  <MenuItem value="small">Small (11-50 employees)</MenuItem>
                  <MenuItem value="medium">Medium (51-200 employees)</MenuItem>
                  <MenuItem value="large">Large (201-1000 employees)</MenuItem>
                  <MenuItem value="enterprise">Enterprise (1000+ employees)</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  type="button"
                  variant="outlined"
                  onClick={handleSkip}
                  disabled={loading || contextLoading}
                >
                  Skip for Now
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading || contextLoading || !createForm.name.trim()}
                  startIcon={loading || contextLoading ? <CircularProgress size={20} /> : <Business />}
                >
                  Create Organization
                </Button>
              </Box>
            </Box>
          </form>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <form onSubmit={handleJoinOrganization}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Alert severity="info">
                Join an existing organization using an invitation code or by searching for public organizations.
              </Alert>

              <TextField
                label="Invitation Code"
                value={joinForm.invitationCode}
                onChange={handleJoinFormChange('invitationCode')}
                fullWidth
                placeholder="Enter invitation code..."
              />

              <Divider>
                <Typography variant="body2" color="text.secondary">
                  OR
                </Typography>
              </Divider>

              <TextField
                label="Organization Name"
                value={joinForm.organizationName}
                onChange={handleJoinFormChange('organizationName')}
                fullWidth
                placeholder="Search for organization..."
              />

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  type="button"
                  variant="outlined"
                  onClick={handleSkip}
                  disabled={loading || contextLoading}
                >
                  Skip for Now
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading || contextLoading || (!joinForm.invitationCode.trim() && !joinForm.organizationName.trim())}
                  startIcon={loading || contextLoading ? <CircularProgress size={20} /> : <GroupAdd />}
                >
                  Join Organization
                </Button>
              </Box>
            </Box>
          </form>
        </TabPanel>
      </Paper>
    </Container>
  );
}
