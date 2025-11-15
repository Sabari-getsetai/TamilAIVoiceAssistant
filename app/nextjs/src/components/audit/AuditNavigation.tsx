'use client';

/**
 * Audit System Navigation Component
 *
 * Features:
 * - Sidebar navigation for audit features
 * - Active route highlighting
 * - Quick action buttons
 * - System status indicators
 */

import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Chip,
  Divider,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Timeline,
  Assessment,
  Security,
  Gavel,
  Shield,
  Dashboard,
  Settings,
  Help,
  Notifications,
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';

import { useSecurityEvents } from '../../services/api/audit/auditQueries';

interface AuditNavigationProps {
  organizationId?: string;
}

export const AuditNavigation: React.FC<AuditNavigationProps> = ({
  organizationId,
}) => {
  const router = useRouter();
  const pathname = usePathname();

  // Fetch security events for badge count
  const { data: securityEvents } = useSecurityEvents(organizationId, 7);
  const criticalEvents = securityEvents?.filter(e => e.severity === 'critical').length || 0;

  const navigationItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: Dashboard,
      path: '/admin/audit',
      description: 'Audit system dashboard',
    },
    {
      id: 'logs',
      label: 'Audit Logs',
      icon: Timeline,
      path: '/admin/audit/logs',
      description: 'Browse audit trail',
    },
    {
      id: 'dashboard',
      label: 'Analytics',
      icon: Assessment,
      path: '/admin/audit/dashboard',
      description: 'Statistics and trends',
    },
    {
      id: 'security',
      label: 'Security Monitoring',
      icon: Security,
      path: '/admin/audit/security',
      description: 'Real-time security events',
      badge: criticalEvents > 0 ? criticalEvents : undefined,
      badgeColor: 'error' as const,
    },
    {
      id: 'compliance',
      label: 'Compliance Reports',
      icon: Gavel,
      path: '/admin/audit/compliance',
      description: 'Generate compliance reports',
    },
  ];

  const quickActions = [
    {
      id: 'settings',
      label: 'Audit Settings',
      icon: Settings,
      path: '/admin/audit/settings',
    },
    {
      id: 'help',
      label: 'Help & Documentation',
      icon: Help,
      path: '/admin/audit/help',
    },
  ];

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const isActivePath = (path: string) => {
    if (path === '/admin/audit') {
      return pathname === path;
    }
    return pathname.startsWith(path);
  };

  return (
    <Box
      sx={{
        width: 280,
        height: '100vh',
        bgcolor: 'background.paper',
        borderRight: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Shield color="primary" />
          <Typography variant="h6" color="primary" fontWeight="bold">
            Audit System
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Enterprise audit trail management
        </Typography>
      </Box>

      <Divider />

      {/* Main Navigation */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List sx={{ py: 1 }}>
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = isActivePath(item.path);

            return (
              <Tooltip
                key={item.id}
                title={item.description}
                placement="right"
                arrow
              >
                <ListItem disablePadding>
                  <ListItemButton
                    onClick={() => handleNavigation(item.path)}
                    selected={isActive}
                    sx={{
                      mx: 1,
                      borderRadius: 1,
                      '&.Mui-selected': {
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                        '&:hover': {
                          bgcolor: 'primary.dark',
                        },
                        '& .MuiListItemIcon-root': {
                          color: 'inherit',
                        },
                      },
                    }}
                  >
                    <ListItemIcon>
                      {item.badge ? (
                        <Badge
                          badgeContent={item.badge}
                          color={item.badgeColor}
                          overlap="circular"
                        >
                          <IconComponent />
                        </Badge>
                      ) : (
                        <IconComponent />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        variant: 'body2',
                        fontWeight: isActive ? 'medium' : 'regular',
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              </Tooltip>
            );
          })}
        </List>

        <Divider sx={{ mx: 2 }} />

        {/* Quick Actions */}
        <Box sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary" fontWeight="medium">
            QUICK ACTIONS
          </Typography>
        </Box>

        <List dense>
          {quickActions.map((action) => {
            const IconComponent = action.icon;
            const isActive = isActivePath(action.path);

            return (
              <ListItem key={action.id} disablePadding>
                <ListItemButton
                  onClick={() => handleNavigation(action.path)}
                  selected={isActive}
                  sx={{
                    mx: 1,
                    borderRadius: 1,
                    '&.Mui-selected': {
                      bgcolor: 'action.selected',
                    },
                  }}
                >
                  <ListItemIcon>
                    <IconComponent fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={action.label}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontSize: '0.875rem',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* Status Footer */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Typography variant="caption" color="text.secondary">
            System Status
          </Typography>
          <Chip
            label={criticalEvents > 0 ? 'Alert' : 'Healthy'}
            color={criticalEvents > 0 ? 'error' : 'success'}
            size="small"
            variant="outlined"
          />
        </Box>

        {criticalEvents > 0 && (
          <Box display="flex" alignItems="center" gap={1}>
            <Notifications fontSize="small" color="error" />
            <Typography variant="caption" color="error">
              {criticalEvents} critical event{criticalEvents > 1 ? 's' : ''}
            </Typography>
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" display="block" mt={1}>
          Last updated: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>
    </Box>
  );
};

export default AuditNavigation;