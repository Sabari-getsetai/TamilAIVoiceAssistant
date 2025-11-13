'use client';

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Container,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Business as BusinessIcon,
  Payment as PaymentIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

import { useAuth } from '@/contexts/AuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { canManageMembers } from '@/utils/permissions';

// Import tab components (we'll create these next)
import GeneralSettings from '@/components/organization/settings/GeneralSettings';
import BillingSettings from '@/components/organization/settings/BillingSettings';
import AdvancedSettings from '@/components/organization/settings/AdvancedSettings';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `settings-tab-${index}`,
    'aria-controls': `settings-tabpanel-${index}`,
  };
}

export default function OrganizationSettingsPage() {
  const { user } = useAuth();
  const { currentOrganization, isLoading, error } = useOrganization();
  const [tabValue, setTabValue] = React.useState(0);

  const userRole = currentOrganization?.user_role;
  const canManageSettings = canManageMembers(userRole);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Check if user has access to organization settings
  React.useEffect(() => {
    console.debug('[OrganizationSettingsPage] Permission check:', {
      currentOrganization: currentOrganization ? {
        id: currentOrganization.id,
        name: currentOrganization.name,
        user_role: currentOrganization.user_role
      } : null,
      userRole,
      canManageSettings,
      isLoading,
      error
    });
  }, [currentOrganization, userRole, canManageSettings, isLoading, error]);

  if (isLoading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          Error loading organization: {error}
        </Alert>
      </Container>
    );
  }

  if (!currentOrganization) {
    return (
      <Container maxWidth="lg">
        <Alert severity="warning" sx={{ mt: 2 }}>
          No organization selected. Please select an organization first.
        </Alert>
      </Container>
    );
  }

  if (!canManageSettings) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          You don't have permission to access organization settings. Contact an organization admin or owner.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        {/* Page Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Organization Settings
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage settings for <strong>{currentOrganization.name}</strong>
          </Typography>
        </Box>

        {/* Settings Content */}
        <Paper sx={{ width: '100%' }}>
          {/* Tabs Navigation */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              aria-label="organization settings tabs"
            >
              <Tab
                icon={<BusinessIcon />}
                label="General"
                {...a11yProps(0)}
                sx={{ minHeight: 64 }}
              />
              <Tab
                icon={<PaymentIcon />}
                label="Billing & Plans"
                {...a11yProps(1)}
                sx={{ minHeight: 64 }}
                disabled={userRole !== 'owner' && userRole !== 'ORG_ADMIN'}
              />
              <Tab
                icon={<SecurityIcon />}
                label="Advanced"
                {...a11yProps(2)}
                sx={{ minHeight: 64 }}
                disabled={userRole !== 'owner' && userRole !== 'ORG_ADMIN'}
              />
            </Tabs>
          </Box>

          {/* Tab Content */}
          <Box sx={{ px: 3, pb: 3 }}>
            <TabPanel value={tabValue} index={0}>
              <GeneralSettings organization={currentOrganization} />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <BillingSettings organization={currentOrganization} userRole={userRole} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <AdvancedSettings organization={currentOrganization} userRole={userRole} />
            </TabPanel>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}