'use client';

import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { SnackbarProvider } from 'notistack';
import { theme } from '../theme/theme';
import { AuthProvider } from '../contexts/AuthContext';
import { OrganizationProvider } from '../contexts/OrganizationContext';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { createQueryClient } from '../services/core/queryClient';
import { useState } from 'react';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <html lang="en">
      <head>
        <title>Tamil AI Voice Assistant</title>
        <meta name="description" content="Tamil AI Voice Assistant with authentication" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <SnackbarProvider
              maxSnack={3}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              autoHideDuration={4000}
            >
              <ErrorBoundary context={{ location: 'root_layout' }}>
                <AuthProvider>
                  <OrganizationProvider>
                    {children}
                  </OrganizationProvider>
                </AuthProvider>
              </ErrorBoundary>
            </SnackbarProvider>
          </ThemeProvider>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </body>
    </html>
  );
}
