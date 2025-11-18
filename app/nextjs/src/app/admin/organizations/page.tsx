'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  Menu,
  ListItemIcon,
  ListItemText,
  MenuItem,
  TextField,
  InputAdornment,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Visibility as ViewIcon,
  Settings as SettingsIcon,
  Block as SuspendIcon,
  CheckCircle as ActivateIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Description as DocumentIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

// Mock organization data - replace with actual API integration
interface OrganizationSummary {
  id: string;
  name: string;
  description: string;
  ownerName: string;
  ownerEmail: string;
  memberCount: number;
  documentCount: number;
  status: 'active' | 'suspended' | 'pending';
  createdAt: string;
  lastActivity: string;
  storageUsed: number; // in MB
}

const mockOrganizations: OrganizationSummary[] = [
  {
    id: '1',
    name: 'TechCorp Inc',
    description: 'Technology company focused on AI solutions',
    ownerName: 'John Doe',
    ownerEmail: 'john@techcorp.com',
    memberCount: 15,
    documentCount: 245,
    status: 'active',
    createdAt: '2024-01-15T10:30:00Z',
    lastActivity: '2024-11-16T09:15:00Z',
    storageUsed: 1200,
  },
  {
    id: '2',
    name: 'StartupHub',
    description: 'Innovation hub for startups',
    ownerName: 'Jane Smith',
    ownerEmail: 'jane@startuphub.com',
    memberCount: 8,
    documentCount: 120,
    status: 'active',
    createdAt: '2024-03-22T14:20:00Z',
    lastActivity: '2024-11-15T16:45:00Z',
    storageUsed: 580,
  },
  {
    id: '3',
    name: 'Research Labs',
    description: 'Academic research organization',
    ownerName: 'Dr. Mike Johnson',
    ownerEmail: 'mike@researchlabs.edu',
    memberCount: 25,
    documentCount: 890,
    status: 'active',
    createdAt: '2024-02-10T09:00:00Z',
    lastActivity: '2024-11-14T11:30:00Z',
    storageUsed: 3400,
  },
];

export default function AdminOrganizationsPage() {
  const [organizations] = useState<OrganizationSummary[]>(mockOrganizations);
  const [searchTerm, setSearchTerm] = useState('');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedOrg, setSelectedOrg] = useState<OrganizationSummary | null>(null);

  const filteredOrganizations = organizations.filter(org =>
    org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    org.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    org.ownerName.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate summary stats
  const totalOrgs = organizations.length;
  const totalMembers = organizations.reduce((sum, org) => sum + org.memberCount, 0);
  const totalDocuments = organizations.reduce((sum, org) => sum + org.documentCount, 0);
  const totalStorage = organizations.reduce((sum, org) => sum + org.storageUsed, 0);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, org: OrganizationSummary) => {
    setMenuAnchor(event.currentTarget);
    setSelectedOrg(org);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedOrg(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'suspended':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatStorage = (mb: number) => {
    if (mb < 1000) {
      return `${mb} MB`;
    }
    return `${(mb / 1000).toFixed(1)} GB`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            Organization Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            System-wide view and management of all organizations
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: Implement organization creation */}}
        >
          Create Organization
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BusinessIcon sx={{ fontSize: 40, mb: 1, color: 'primary.main' }} />
              <Typography variant="h4" component="div">
                {totalOrgs}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Organizations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 40, mb: 1, color: 'secondary.main' }} />
              <Typography variant="h4" component="div">
                {totalMembers}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Members
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <DocumentIcon sx={{ fontSize: 40, mb: 1, color: 'info.main' }} />
              <Typography variant="h4" component="div">
                {totalDocuments}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AnalyticsIcon sx={{ fontSize: 40, mb: 1, color: 'success.main' }} />
              <Typography variant="h4" component="div">
                {formatStorage(totalStorage)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Storage Used
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search organizations by name, description, or owner..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 500 }}
        />
      </Box>

      {/* Organizations Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Organization</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Members</TableCell>
              <TableCell>Documents</TableCell>
              <TableCell>Storage</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredOrganizations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} sx={{ textAlign: 'center', py: 4 }}>
                  {searchTerm ? (
                    <Typography variant="body2" color="text.secondary">
                      No organizations found matching "{searchTerm}"
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No organizations available
                    </Typography>
                  )}
                </TableCell>
              </TableRow>
            ) : (
              filteredOrganizations.map((org) => (
                <TableRow key={org.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {org.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {org.description}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">
                        {org.ownerName}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {org.ownerEmail}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {org.memberCount} members
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {org.documentCount} docs
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatStorage(org.storageUsed)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={org.status.toUpperCase()}
                      color={getStatusColor(org.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(org.createdAt)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, org)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Organization Actions Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <ViewIcon />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>

        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText>Organization Settings</ListItemText>
        </MenuItem>

        {selectedOrg?.status === 'active' ? (
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <SuspendIcon />
            </ListItemIcon>
            <ListItemText>Suspend Organization</ListItemText>
          </MenuItem>
        ) : (
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <ActivateIcon />
            </ListItemIcon>
            <ListItemText>Activate Organization</ListItemText>
          </MenuItem>
        )}

        <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon color="error" />
          </ListItemIcon>
          <ListItemText>Delete Organization</ListItemText>
        </MenuItem>
      </Menu>

      {/* Implementation Notice */}
      <Alert severity="info" sx={{ mt: 3 }}>
        This is a placeholder page for organization management. Integration with the backend organization management API is pending.
      </Alert>
    </Box>
  );
}