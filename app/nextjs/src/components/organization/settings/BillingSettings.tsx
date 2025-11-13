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
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  CreditCard as CreditCardIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Download as DownloadIcon,
  Upgrade as UpgradeIcon,
  Info as InfoIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material';

import { Organization, OrganizationRole } from '@/types/organization';

interface BillingSettingsProps {
  organization: Organization;
  userRole?: string;
}

// Mock billing data (replace with real API calls later)
const SUBSCRIPTION_PLANS = [
  {
    name: 'Starter',
    price: 0,
    period: 'month',
    features: [
      'Up to 5 team members',
      '100 documents',
      '10 hours voice processing/month',
      'Email support',
      'Basic analytics'
    ],
    current: true
  },
  {
    name: 'Professional',
    price: 29,
    period: 'month',
    features: [
      'Up to 25 team members',
      '1,000 documents',
      '100 hours voice processing/month',
      'Priority support',
      'Advanced analytics',
      'Custom integrations'
    ],
    current: false,
    popular: true
  },
  {
    name: 'Enterprise',
    price: 99,
    period: 'month',
    features: [
      'Unlimited team members',
      'Unlimited documents',
      'Unlimited voice processing',
      '24/7 phone support',
      'Advanced analytics',
      'Custom integrations',
      'Dedicated account manager',
      'SLA guarantee'
    ],
    current: false
  }
];

const BILLING_HISTORY = [
  {
    id: '1',
    date: '2024-11-01',
    amount: 29.00,
    status: 'paid',
    description: 'Professional Plan - November 2024',
    invoiceUrl: '#'
  },
  {
    id: '2',
    date: '2024-10-01',
    amount: 29.00,
    status: 'paid',
    description: 'Professional Plan - October 2024',
    invoiceUrl: '#'
  },
  {
    id: '3',
    date: '2024-09-01',
    amount: 29.00,
    status: 'paid',
    description: 'Professional Plan - September 2024',
    invoiceUrl: '#'
  }
];

const USAGE_STATS = {
  members: { used: 8, limit: 25 },
  documents: { used: 234, limit: 1000 },
  voiceHours: { used: 45.2, limit: 100 }
};

export default function BillingSettings({ organization, userRole }: BillingSettingsProps) {
  const [upgradeDialogOpen, setUpgradeDialogOpen] = React.useState(false);
  const [selectedPlan, setSelectedPlan] = React.useState<string>('');

  const isOwnerOrAdmin = userRole === 'owner' || userRole === 'ORG_ADMIN';

  const handleUpgrade = (planName: string) => {
    setSelectedPlan(planName);
    setUpgradeDialogOpen(true);
  };

  const handleUpgradeConfirm = () => {
    // TODO: Implement actual upgrade logic
    console.log(`Upgrading to ${selectedPlan} plan`);
    setUpgradeDialogOpen(false);
    setSelectedPlan('');
  };

  const getUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 75) return 'warning';
    return 'primary';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Billing & Subscription
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage your subscription plan, billing information, and usage statistics.
      </Typography>

      {!isOwnerOrAdmin && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Only organization owners and admins can manage billing settings.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Current Plan & Usage */}
        <Grid item xs={12} lg={8}>
          {/* Current Plan */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Current Plan</Typography>
                <Chip
                  label={organization.subscription_plan || 'Starter'}
                  color="primary"
                  variant="outlined"
                />
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status: {organization.subscription_status || 'Active'}
              </Typography>
              {organization.trial_ends_at && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Trial ends on {new Date(organization.trial_ends_at).toLocaleDateString()}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Usage Statistics */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Usage Statistics
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Team Members</Typography>
                  <Typography variant="body2">
                    {USAGE_STATS.members.used} / {USAGE_STATS.members.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(USAGE_STATS.members.used, USAGE_STATS.members.limit)}
                  color={getUsageColor(getUsagePercentage(USAGE_STATS.members.used, USAGE_STATS.members.limit))}
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Documents</Typography>
                  <Typography variant="body2">
                    {USAGE_STATS.documents.used} / {USAGE_STATS.documents.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(USAGE_STATS.documents.used, USAGE_STATS.documents.limit)}
                  color={getUsageColor(getUsagePercentage(USAGE_STATS.documents.used, USAGE_STATS.documents.limit))}
                />
              </Box>

              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Voice Processing Hours</Typography>
                  <Typography variant="body2">
                    {USAGE_STATS.voiceHours.used} / {USAGE_STATS.voiceHours.limit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getUsagePercentage(USAGE_STATS.voiceHours.used, USAGE_STATS.voiceHours.limit)}
                  color={getUsageColor(getUsagePercentage(USAGE_STATS.voiceHours.used, USAGE_STATS.voiceHours.limit))}
                />
              </Box>
            </CardContent>
          </Card>

          {/* Billing History */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Billing History
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Invoice</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {BILLING_HISTORY.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell>
                          {new Date(invoice.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{invoice.description}</TableCell>
                        <TableCell align="right">${invoice.amount.toFixed(2)}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={invoice.status}
                            color={invoice.status === 'paid' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton size="small" disabled={!isOwnerOrAdmin}>
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Available Plans */}
        <Grid item xs={12} lg={4}>
          <Typography variant="h6" gutterBottom>
            Available Plans
          </Typography>

          {SUBSCRIPTION_PLANS.map((plan) => (
            <Card
              key={plan.name}
              sx={{
                mb: 2,
                border: plan.popular ? 2 : 1,
                borderColor: plan.popular ? 'primary.main' : 'divider',
                position: 'relative'
              }}
            >
              {plan.popular && (
                <Chip
                  label="Most Popular"
                  color="primary"
                  size="small"
                  sx={{
                    position: 'absolute',
                    top: -8,
                    right: 16,
                    zIndex: 1
                  }}
                />
              )}

              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {plan.name}
                  {plan.current && (
                    <Chip label="Current" color="success" size="small" sx={{ ml: 1 }} />
                  )}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="h4" component="span">
                    ${plan.price}
                  </Typography>
                  <Typography variant="body2" component="span" color="text.secondary">
                    /{plan.period}
                  </Typography>
                </Box>

                <List dense>
                  {plan.features.map((feature, index) => (
                    <ListItem key={index} sx={{ py: 0.5, pl: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckIcon color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={feature}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>

              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                {plan.current ? (
                  <Button variant="outlined" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    variant={plan.popular ? "contained" : "outlined"}
                    startIcon={<UpgradeIcon />}
                    onClick={() => handleUpgrade(plan.name)}
                    disabled={!isOwnerOrAdmin}
                    fullWidth
                  >
                    Upgrade
                  </Button>
                )}
              </CardActions>
            </Card>
          ))}
        </Grid>
      </Grid>

      {/* Upgrade Confirmation Dialog */}
      <Dialog open={upgradeDialogOpen} onClose={() => setUpgradeDialogOpen(false)}>
        <DialogTitle>Upgrade to {selectedPlan} Plan</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            <InfoIcon sx={{ mr: 1 }} />
            Payment integration coming soon! This is a preview of the upgrade flow.
          </Alert>
          <Typography>
            You are about to upgrade to the <strong>{selectedPlan}</strong> plan.
            This change will take effect immediately and you will be charged pro-rated for the current billing period.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleUpgradeConfirm} variant="contained">
            Confirm Upgrade
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}