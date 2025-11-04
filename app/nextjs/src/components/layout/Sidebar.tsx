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
} from '@mui/icons-material';
import { usePathname, useRouter } from 'next/navigation';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  width?: number;
}

const menuItems = [
  { label: 'Home', icon: <HomeIcon />, path: '/' },
  { label: 'Admin Dashboard', icon: <DashboardIcon />, path: '/admin' },
  { label: 'Upload Documents', icon: <UploadIcon />, path: '/admin/upload' },
  { label: 'Manage Documents', icon: <DocumentsIcon />, path: '/admin/documents' },
  { label: 'Statistics', icon: <StatsIcon />, path: '/admin/statistics' },
  { label: 'Settings', icon: <SettingsIcon />, path: '/admin/settings' },
];

const voiceItems = [
  { label: 'Voice Assistant', icon: <VoiceIcon />, path: '/voice' },
];

export default function Sidebar({ open, onClose, width = 280 }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

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
          Admin Dashboard
        </Typography>
      </Box>

      <Divider />

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
