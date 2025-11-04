'use client';

import { useState } from 'react';
import { Box } from '@mui/material';
import AppBar from './AppBar';
import Sidebar from './Sidebar';
import { useQueryClient } from '@tanstack/react-query';

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const queryClient = useQueryClient();

  const handleMenuClick = () => {
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  const handleRefresh = () => {
    // Invalidate all queries to refresh data
    queryClient.invalidateQueries();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar onMenuClick={handleMenuClick} onRefresh={handleRefresh} />
      
      <Sidebar open={sidebarOpen} onClose={handleSidebarClose} />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: 'background.default',
          minHeight: 'calc(100vh - 64px)', // Subtract AppBar height
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
