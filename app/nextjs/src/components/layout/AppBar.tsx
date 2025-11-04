'use client';

import {
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { usePathname } from 'next/navigation';

interface AppBarProps {
  onMenuClick: () => void;
  onRefresh?: () => void;
}

export default function AppBar({ onMenuClick, onRefresh }: AppBarProps) {
  const pathname = usePathname();

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
      </Toolbar>
    </MuiAppBar>
  );
}
