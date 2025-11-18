'use client';

import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  Description as DocumentsIcon,
  Analytics as StatsIcon,
  Settings as SettingsIcon,
  Mic as VoiceIcon,
  Home as HomeIcon,
  Business as OrganizationIcon,
  People as PeopleIcon,
  SupervisorAccount as AdminIcon,
  Storage as DataIcon,
  MonitorHeart as SystemIcon,
} from '@mui/icons-material';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types/auth';
import OrganizationSwitcher from '../organization/OrganizationSwitcher';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  width?: number;
}

// Dynamic menu items based on user role
const getMenuItems = (userRole: UserRole | null) => {
  // System Admin menu for ADMIN and SUPERADMIN users
  if (userRole === UserRole.ADMIN || userRole === UserRole.SUPERADMIN) {
    return [
      { label: 'Home', icon: <HomeIcon />, path: '/' },
      { label: 'System Dashboard', icon: <DashboardIcon />, path: '/admin' },
      { label: 'Manage Users', icon: <AdminIcon />, path: '/admin/users' },
      { label: 'System Organizations', icon: <OrganizationIcon />, path: '/admin/organizations' },
      { label: 'Microservices', icon: <SystemIcon />, path: '/admin/microservices' },
      { label: 'Audit Trail', icon: <DataIcon />, path: '/admin/audit' },
      { label: 'System Settings', icon: <SettingsIcon />, path: '/admin/settings' },
    ];
  }

  // Organization menu for organization members (OWNER, ORG_ADMIN, MEMBER)
  return [
    { label: 'Home', icon: <HomeIcon />, path: '/' },
    { label: 'Organization Dashboard', icon: <DashboardIcon />, path: '/org' },
    { label: 'Documents', icon: <DocumentsIcon />, path: '/org/documents' },
    { label: 'Team Members', icon: <PeopleIcon />, path: '/org/members' },
    { label: 'Analytics', icon: <StatsIcon />, path: '/org/analytics' },
    { label: 'Organization Settings', icon: <SettingsIcon />, path: '/org/settings' },
  ];
};

const voiceItems = [
  { label: 'Voice Assistant', icon: <VoiceIcon />, path: '/voice' },
];

export default function Sidebar({ open, onClose, width = 280 }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();

  // Get dynamic menu items based on user role
  const menuItems = getMenuItems(user?.role || null);

  const handleNavigation = (path: string) => {
    router.push(path);
    onClose();
  };

  const isSelected = (path: string) => {
    if (path === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(path);
  };

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      sx={{
        width: width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: width,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div" color="primary" fontWeight="bold">
          Tamil AI Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERADMIN
            ? 'System Administration'
            : 'Organization Dashboard'}
        </Typography>
      </Box>

      <Divider />

      {/* Organization Switcher - Only show for organization members */}
      {user?.role !== UserRole.ADMIN && user?.role !== UserRole.SUPERADMIN && (
        <OrganizationSwitcher onNavigation={handleNavigation} />
      )}

      <List sx={{ flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={isSelected(item.path)}
              onClick={() => handleNavigation(item.path)}
              sx={{
                mx: 1,
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: isSelected(item.path) ? 'inherit' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isSelected(item.path) ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      <List>
        <ListItem>
          <ListItemText
            primary="Voice Interface"
            primaryTypographyProps={{
              variant: 'overline',
              color: 'text.secondary',
              fontWeight: 600,
            }}
          />
        </ListItem>
        {voiceItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={isSelected(item.path)}
              onClick={() => handleNavigation(item.path)}
              sx={{
                mx: 1,
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: isSelected(item.path) ? 'inherit' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isSelected(item.path) ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ p: 2, mt: 'auto' }}>
        <Typography variant="caption" color="text.secondary" display="block">
          Version 1.0.0
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Phase 8 Complete
        </Typography>
      </Box>
    </Drawer>
  );
}
