'use client';

/**
 * React Error Boundary for Enterprise Tamil AI Voice Assistant
 *
 * Features:
 * - Graceful error handling and recovery
 * - Error reporting and logging
 * - User-friendly error displays
 * - Development vs production error modes
 * - Error recovery actions
 */

import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import {
  Box,
  Button,
  Typography,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  Stack,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ErrorOutline,
  Refresh,
  BugReport,
  ExpandMore,
  Home,
  ContactSupport,
} from '@mui/icons-material';
import ErrorHandler, { EnhancedError, ErrorType, ErrorSeverity } from '../../services/core/errorHandler';

// Error boundary props
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  context?: Record<string, any>;
  isolate?: boolean; // If true, errors won't bubble up
}

// Error fallback component props
interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
  context?: Record<string, any>;
}

/**
 * Main Error Fallback Component
 */
const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetErrorBoundary,
  context,
}) => {
  const enhancedError = ErrorHandler.transformError(error, context);

  React.useEffect(() => {
    // Report error when component mounts
    ErrorHandler.reportError(enhancedError);
  }, [enhancedError]);

  const getSeverityColor = (severity: ErrorSeverity): 'error' | 'warning' | 'info' => {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return 'error';
      case ErrorSeverity.MEDIUM:
        return 'warning';
      default:
        return 'info';
    }
  };

  const handleContactSupport = () => {
    const subject = encodeURIComponent(`Error Report: ${enhancedError.type}`);
    const body = encodeURIComponent(
      `Error Details:\n` +
      `- Type: ${enhancedError.type}\n` +
      `- Severity: ${enhancedError.severity}\n` +
      `- Message: ${enhancedError.userMessage}\n` +
      `- Correlation ID: ${enhancedError.correlationId || 'N/A'}\n` +
      `- Timestamp: ${new Date(enhancedError.timestamp).toISOString()}\n\n` +
      `Please describe what you were doing when this error occurred:\n\n`
    );

    window.open(`mailto:support@tamil-ai-assistant.com?subject=${subject}&body=${body}`);
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        p: 3,
      }}
    >
      <Card sx={{ maxWidth: 600, width: '100%' }}>
        <CardContent>
          <Stack spacing={3}>
            {/* Error Icon and Title */}
            <Box sx={{ textAlign: 'center' }}>
              <ErrorOutline
                sx={{
                  fontSize: 64,
                  color: theme => theme.palette.error.main,
                  mb: 2,
                }}
              />
              <Typography variant="h4" component="h1" gutterBottom>
                Oops! Something went wrong
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {enhancedError.userMessage}
              </Typography>
            </Box>

            {/* Error Metadata */}
            <Box>
              <Stack direction="row" spacing={1} justifyContent="center">
                <Chip
                  label={enhancedError.type}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={enhancedError.severity}
                  size="small"
                  color={getSeverityColor(enhancedError.severity)}
                />
                {enhancedError.correlationId && (
                  <Chip
                    label={`ID: ${enhancedError.correlationId.slice(-8)}`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>

            {/* Recovery Actions */}
            {enhancedError.recoveryActions && enhancedError.recoveryActions.length > 0 && (
              <Alert severity="info">
                <AlertTitle>What you can try:</AlertTitle>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {enhancedError.recoveryActions.map((action, index) => (
                    <li key={index}>{action}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Action Buttons */}
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={resetErrorBoundary}
                size="large"
              >
                Try Again
              </Button>
              <Button
                variant="outlined"
                startIcon={<Home />}
                onClick={handleGoHome}
                size="large"
              >
                Go Home
              </Button>
              <Button
                variant="outlined"
                startIcon={<ContactSupport />}
                onClick={handleContactSupport}
                size="large"
              >
                Contact Support
              </Button>
            </Stack>

            {/* Technical Details (Development/Debug) */}
            {(process.env.NODE_ENV === 'development' || enhancedError.severity === ErrorSeverity.CRITICAL) && (
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMore />}
                  aria-controls="error-details-content"
                  id="error-details-header"
                >
                  <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BugReport fontSize="small" />
                    Technical Details
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Error Message:
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {enhancedError.message}
                      </Typography>
                    </Box>

                    {enhancedError.correlationId && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Correlation ID:
                        </Typography>
                        <Typography variant="body2" fontFamily="monospace">
                          {enhancedError.correlationId}
                        </Typography>
                      </Box>
                    )}

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Timestamp:
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {new Date(enhancedError.timestamp).toISOString()}
                      </Typography>
                    </Box>

                    {enhancedError.stack && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Stack Trace:
                        </Typography>
                        <Typography
                          variant="body2"
                          fontFamily="monospace"
                          sx={{
                            fontSize: '0.75rem',
                            backgroundColor: 'grey.100',
                            p: 1,
                            borderRadius: 1,
                            whiteSpace: 'pre-wrap',
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          {enhancedError.stack}
                        </Typography>
                      </Box>
                    )}

                    {enhancedError.context && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Context:
                        </Typography>
                        <Typography
                          variant="body2"
                          fontFamily="monospace"
                          sx={{
                            fontSize: '0.75rem',
                            backgroundColor: 'grey.100',
                            p: 1,
                            borderRadius: 1,
                          }}
                        >
                          {JSON.stringify(enhancedError.context, null, 2)}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};

/**
 * Minimal Error Fallback for smaller components
 */
const MinimalErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetErrorBoundary,
  context,
}) => {
  const enhancedError = ErrorHandler.transformError(error, context);

  React.useEffect(() => {
    ErrorHandler.reportError(enhancedError);
  }, [enhancedError]);

  return (
    <Alert
      severity="error"
      action={
        <Button color="inherit" size="small" onClick={resetErrorBoundary}>
          Retry
        </Button>
      }
    >
      <AlertTitle>Error</AlertTitle>
      {enhancedError.userMessage}
    </Alert>
  );
};

/**
 * Error handler function
 */
const handleError = (error: Error, errorInfo: React.ErrorInfo, context?: Record<string, any>) => {
  console.error('React Error Boundary caught an error:', error, errorInfo);

  const enhancedError = ErrorHandler.transformError(error, {
    ...context,
    componentStack: errorInfo.componentStack,
  });

  ErrorHandler.reportError(enhancedError);
};

/**
 * Main Error Boundary component
 */
export const ErrorBoundary: React.FC<ErrorBoundaryProps> = ({
  children,
  fallback: CustomFallback,
  onError,
  context,
  isolate = false,
}) => {
  const FallbackComponent = CustomFallback || ErrorFallback;

  const errorHandler = (error: Error, errorInfo: React.ErrorInfo) => {
    handleError(error, errorInfo, context);
    onError?.(error, errorInfo);
  };

  const resetKeys = [context]; // Reset when context changes

  return (
    <ReactErrorBoundary
      FallbackComponent={({ error, resetErrorBoundary }) => (
        <FallbackComponent
          error={error}
          resetErrorBoundary={resetErrorBoundary}
          context={context}
        />
      )}
      onError={errorHandler}
      resetKeys={resetKeys}
      isolate={isolate}
    >
      {children}
    </ReactErrorBoundary>
  );
};

/**
 * Minimal Error Boundary for small components
 */
export const MinimalErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'fallback'>> = ({
  children,
  onError,
  context,
  isolate = true, // Default to isolate for minimal boundaries
}) => {
  return (
    <ErrorBoundary
      fallback={MinimalErrorFallback}
      onError={onError}
      context={context}
      isolate={isolate}
    >
      {children}
    </ErrorBoundary>
  );
};

/**
 * HOC for wrapping components with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default ErrorBoundary;