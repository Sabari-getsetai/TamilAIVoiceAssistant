'use client';

import {
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Breadcrumbs,
  Link,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  AccountCircle as AccountIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface AppBarProps {
  onMenuClick: () => void;
  onRefresh?: () => void;
}

export default function AppBar({ onMenuClick, onRefresh }: AppBarProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const isMenuOpen = Boolean(anchorEl);

  const getBreadcrumbs = () => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs = [{ label: 'Home', href: '/' }];

    let currentPath = '';
    segments.forEach((segment) => {
      currentPath += `/${segment}`;
      const label = segment.charAt(0).toUpperCase() + segment.slice(1);
      breadcrumbs.push({ label, href: currentPath });
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
  };

  const getUserDisplayName = () => {
    if (!user) return 'Guest';
    return user.full_name || user.username || 'User';
  };

  const getUserInitials = () => {
    if (!user) return 'G';
    const name = user.full_name || user.username || 'User';
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'organization_admin':
        return 'warning';
      case 'user':
        return 'primary';
      default:
        return 'default';
    }
  };

  return (
    <MuiAppBar position="sticky" elevation={1}>
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ mb: 0.5 }}>
            Tamil AI Voice Assistant
          </Typography>
          <Breadcrumbs
            aria-label="breadcrumb"
            sx={{
              '& .MuiBreadcrumbs-separator': {
                color: 'rgba(255, 255, 255, 0.7)',
              },
            }}
          >
            {breadcrumbs.map((crumb, index) => (
              <Link
                key={crumb.href}
                color={index === breadcrumbs.length - 1 ? 'inherit' : 'rgba(255, 255, 255, 0.7)'}
                href={crumb.href}
                underline="hover"
                sx={{
                  fontSize: '0.875rem',
                  fontWeight: index === breadcrumbs.length - 1 ? 500 : 400,
                }}
              >
                {crumb.label}
              </Link>
            ))}
          </Breadcrumbs>
        </Box>

        {onRefresh && (
          <IconButton color="inherit" onClick={onRefresh} title="Refresh">
            <RefreshIcon />
          </IconButton>
        )}

        <IconButton color="inherit" title="Settings">
          <SettingsIcon />
        </IconButton>

        {/* User Profile Section */}
        {isAuthenticated && user ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
              <Chip
                label={user.role.replace('_', ' ')}
                size="small"
                color={getRoleColor(user.role) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                sx={{ mr: 1, textTransform: 'capitalize' }}
              />
              <IconButton
                size="large"
                edge="end"
                aria-label="account of current user"
                aria-controls="primary-search-account-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
                sx={{ ml: 1 }}
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  {getUserInitials()}
                </Avatar>
              </IconButton>
            </Box>
            <Menu
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              id="primary-search-account-menu"
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={isMenuOpen}
              onClose={handleMenuClose}
            >
              <MenuItem disabled>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>
                  <Typography variant="subtitle2">{getUserDisplayName()}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user.email}
                  </Typography>
                </ListItemText>
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Logout</ListItemText>
              </MenuItem>
            </Menu>
          </>
        ) : (
          <IconButton color="inherit" title="Login" href="/login">
            <AccountIcon />
          </IconButton>
        )}
      </Toolbar>
    </MuiAppBar>
  );
}
