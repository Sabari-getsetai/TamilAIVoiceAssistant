'use client';

import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Chip,
  Collapse,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Business as BusinessIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Add as AddIcon,
  PersonAdd as JoinIcon,
  Check as CheckIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useOrganization } from '@/contexts/OrganizationContext';
import { useSnackbar } from 'notistack';
import { useRouter } from 'next/navigation';

interface OrganizationSwitcherProps {
  onNavigation?: (path: string) => void;
}

export default function OrganizationSwitcher({ onNavigation }: OrganizationSwitcherProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    currentOrganization,
    organizations,
    isLoading,
    error,
    switchOrganization,
    clearError,
  } = useOrganization();
  const { enqueueSnackbar } = useSnackbar();
  const router = useRouter();

  const handleExpandClick = () => {
    setIsExpanded(!isExpanded);
    if (error) {
      clearError();
    }
  };

  const handleSwitchOrganization = async (orgId: string) => {
    if (orgId === currentOrganization?.id) return;

    try {
      await switchOrganization(orgId);
      enqueueSnackbar('Organization switched successfully', { variant: 'success' });
      setIsExpanded(false);
    } catch (error: any) {
      enqueueSnackbar('Failed to switch organization', { variant: 'error' });
    }
  };

  const handleCreateOrganization = () => {
    router.push('/setup/organization');
    if (onNavigation) {
      onNavigation('/setup/organization');
    }
  };

  const handleManageOrganizations = () => {
    router.push('/admin/organizations');
    if (onNavigation) {
      onNavigation('/admin/organizations');
    }
  };

  const getRoleChip = (role?: string) => {
    if (!role) return null;

    const roleConfig = {
      owner: { label: 'Owner', color: 'error' as const },
      admin: { label: 'Admin', color: 'warning' as const },
      member: { label: 'Member', color: 'default' as const },
    };

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.member;

    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        sx={{ height: 20, fontSize: '0.7rem' }}
      />
    );
  };

  return (
    <Box>
      {/* Current Organization Header */}
      <ListItem>
        <ListItemText
          primary="Organization"
          primaryTypographyProps={{
            variant: 'overline',
            color: 'text.secondary',
            fontWeight: 600,
          }}
        />
      </ListItem>

      {/* Current Organization Display */}
      <ListItem disablePadding>
        <ListItemButton
          onClick={handleExpandClick}
          sx={{
            mx: 1,
            borderRadius: 1,
            bgcolor: 'action.hover',
            '&:hover': {
              bgcolor: 'action.selected',
            },
          }}
        >
          <ListItemIcon>
            <BusinessIcon color="primary" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Typography variant="body2" fontWeight={600} noWrap sx={{ flex: 1 }}>
                  {currentOrganization?.name || 'No Organization'}
                </Typography>
                {currentOrganization?.current_user_role &&
                  getRoleChip(currentOrganization.current_user_role)
                }
              </Box>
            }
            secondary={
              isLoading ? (
                <Typography variant="caption" color="text.secondary">
                  Loading...
                </Typography>
              ) : organizations.length > 1 ? (
                <Typography variant="caption" color="text.secondary">
                  {organizations.length} organizations • Click to switch
                </Typography>
              ) : (
                <Typography variant="caption" color="text.secondary">
                  Personal organization
                </Typography>
              )
            }
          />
          {organizations.length > 1 && (
            <IconButton size="small">
              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          )}
        </ListItemButton>
      </ListItem>

      {/* Error Display */}
      {error && (
        <Box sx={{ mx: 2, mb: 1 }}>
          <Alert severity="error" onClose={clearError}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Organization List (Expanded) */}
      {organizations.length > 1 && (
        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <List dense sx={{ pl: 2 }}>
            {organizations.map((org) => {
              const isActive = org.id === currentOrganization?.id;

              return (
                <ListItem key={org.id} disablePadding>
                  <ListItemButton
                    onClick={() => handleSwitchOrganization(org.id)}
                    disabled={isActive || isLoading}
                    sx={{
                      borderRadius: 1,
                      mx: 1,
                      ...(isActive && {
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                        '&:hover': {
                          bgcolor: 'primary.dark',
                        },
                        '& .MuiListItemIcon-root': {
                          color: 'primary.contrastText',
                        },
                      }),
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {isActive ? (
                        <CheckIcon fontSize="small" />
                      ) : (
                        <BusinessIcon fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            fontWeight={isActive ? 600 : 400}
                            noWrap
                            sx={{ flex: 1 }}
                          >
                            {org.name}
                          </Typography>
                          {org.current_user_role && getRoleChip(org.current_user_role)}
                        </Box>
                      }
                      secondary={
                        org.description && (
                          <Typography
                            variant="caption"
                            color={isActive ? 'inherit' : 'text.secondary'}
                            sx={{ opacity: isActive ? 0.8 : 1 }}
                          >
                            {org.description}
                          </Typography>
                        )
                      }
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </Collapse>
      )}

      {/* Organization Actions */}
      <List dense>
        <ListItem disablePadding>
          <ListItemButton
            onClick={handleCreateOrganization}
            sx={{
              mx: 1,
              borderRadius: 1,
              color: 'success.main',
              '&:hover': {
                bgcolor: 'success.light',
                color: 'success.contrastText',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: 'inherit' }}>
              <AddIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2" fontWeight={500}>
                  Create Organization
                </Typography>
              }
            />
          </ListItemButton>
        </ListItem>

        {organizations.length > 0 && (
          <ListItem disablePadding>
            <ListItemButton
              onClick={handleManageOrganizations}
              sx={{
                mx: 1,
                borderRadius: 1,
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: 'inherit' }}>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body2">
                    Manage Organizations
                  </Typography>
                }
              />
            </ListItemButton>
          </ListItem>
        )}
      </List>

      <Divider sx={{ my: 1 }} />
    </Box>
  );
}