'use client';

import React, { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  Group as GroupIcon,
  VoiceChat as VoiceChatIcon,
  Description as DocumentIcon
} from '@mui/icons-material';

import { useAuth } from '@/contexts/AuthContext';

interface InvitationData {
  id: string;
  organization_name: string;
  organization_description?: string;
  invited_email: string;
  role: string;
  invited_by_name: string;
  expires_at: string;
  is_expired: boolean;
}

function AcceptInvitationContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();

  const [invitation, setInvitation] = React.useState<InvitationData | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isAccepting, setIsAccepting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  const token = searchParams.get('token');

  React.useEffect(() => {
    if (!token) {
      setError('Invalid invitation link. Please check the URL.');
      setIsLoading(false);
      return;
    }

    loadInvitationDetails();
  }, [token]);

  const loadInvitationDetails = async () => {
    try {
      setIsLoading(true);

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/auth/invitations/${token}`);
      // if (!response.ok) {
      //   throw new Error('Failed to load invitation details');
      // }
      // const invitationData = await response.json();

      // Mock invitation data for demonstration
      const mockInvitation: InvitationData = {
        id: '1',
        organization_name: 'Tamil Voice AI Solutions',
        organization_description: 'Leading AI company focused on Tamil language voice technology and document intelligence.',
        invited_email: 'newuser@example.com',
        role: 'member',
        invited_by_name: 'John Smith',
        expires_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days from now
        is_expired: false
      };

      setInvitation(mockInvitation);
      setError(null);
    } catch (err: any) {
      console.error('Error loading invitation:', err);
      setError(err.message || 'Failed to load invitation details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptInvitation = async () => {
    if (!invitation) return;

    try {
      setIsAccepting(true);

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/auth/invitations/${token}/accept`, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${await getAccessToken()}`
      //   }
      // });

      // if (!response.ok) {
      //   throw new Error('Failed to accept invitation');
      // }

      // Mock success
      setSuccess(true);

      // Redirect to organization dashboard after a brief delay
      setTimeout(() => {
        router.push('/admin/organizations');
      }, 2000);

    } catch (err: any) {
      console.error('Error accepting invitation:', err);
      setError(err.message || 'Failed to accept invitation');
    } finally {
      setIsAccepting(false);
    }
  };

  const handleSignIn = () => {
    // Redirect to sign-in with return URL
    const returnUrl = encodeURIComponent(`/auth/accept-invitation?token=${token}`);
    router.push(`/auth/login?returnUrl=${returnUrl}`);
  };

  const getRoleLabel = (role: string) => {
    if (role === 'ORG_ADMIN') return 'Organization Admin';
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'owner':
        return 'error';
      case 'org_admin':
        return 'warning';
      case 'member':
        return 'primary';
      default:
        return 'default';
    }
  };

  const formatExpiryDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
          <Button variant="outlined" onClick={() => router.push('/')}>
            Go to Homepage
          </Button>
        </Paper>
      </Container>
    );
  }

  if (success) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom color="success.main">
            Welcome to the Team!
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            You have successfully joined <strong>{invitation?.organization_name}</strong>.
            Redirecting you to the organization dashboard...
          </Typography>
          <CircularProgress size={30} />
        </Paper>
      </Container>
    );
  }

  if (!invitation) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Alert severity="warning">
            Invitation not found or has expired.
          </Alert>
        </Paper>
      </Container>
    );
  }

  if (invitation.is_expired) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            This invitation has expired.
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Please contact the organization administrator to request a new invitation.
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (!isAuthenticated) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main', mx: 'auto', mb: 2 }}>
              <BusinessIcon sx={{ fontSize: 40 }} />
            </Avatar>
            <Typography variant="h4" gutterBottom>
              Organization Invitation
            </Typography>
            <Typography variant="body1" color="text.secondary">
              You've been invited to join <strong>{invitation.organization_name}</strong>
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            Please sign in to your account to accept this invitation.
          </Alert>

          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSignIn}
              sx={{ minWidth: 200 }}
            >
              Sign In to Accept
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  // Check if the current user's email matches the invited email
  const isCorrectUser = user?.email === invitation.invited_email;

  if (!isCorrectUser) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Account Mismatch
            </Typography>
            This invitation was sent to <strong>{invitation.invited_email}</strong>, but you are currently signed in as <strong>{user?.email}</strong>.
          </Alert>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Please sign in with the correct account or contact the organization administrator.
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button variant="outlined" onClick={() => router.push('/auth/logout')}>
              Sign Out
            </Button>
            <Button variant="contained" onClick={() => router.push('/')}>
              Go to Dashboard
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper sx={{ overflow: 'hidden' }}>
        {/* Header */}
        <Box sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', p: 4, textAlign: 'center' }}>
          <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.dark', mx: 'auto', mb: 2 }}>
            <BusinessIcon sx={{ fontSize: 40 }} />
          </Avatar>
          <Typography variant="h4" gutterBottom>
            You're Invited!
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            Join {invitation.organization_name}
          </Typography>
        </Box>

        {/* Content */}
        <Box sx={{ p: 4 }}>
          {/* Invitation Details */}
          <Card variant="outlined" sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <GroupIcon sx={{ mr: 1 }} />
                Invitation Details
              </Typography>

              <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' } }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Organization
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {invitation.organization_name}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Your Role
                  </Typography>
                  <Chip
                    label={getRoleLabel(invitation.role)}
                    color={getRoleColor(invitation.role) as any}
                    size="small"
                  />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Invited By
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {invitation.invited_by_name}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Invitation Expires
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatExpiryDate(invitation.expires_at)}
                  </Typography>
                </Box>
              </Box>

              {invitation.organization_description && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    About the Organization
                  </Typography>
                  <Typography variant="body1">
                    {invitation.organization_description}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* What You'll Get Access To */}
          <Card variant="outlined" sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                What you'll get access to:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <VoiceChatIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Voice Conversations"
                    secondary="Real-time AI voice interactions in Tamil"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <DocumentIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Document Intelligence"
                    secondary="Upload and query documents with AI assistance"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <GroupIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Team Collaboration"
                    secondary="Work together with your organization members"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SecurityIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Secure & Private"
                    secondary="Enterprise-grade security and data privacy"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleAcceptInvitation}
              disabled={isAccepting}
              sx={{ minWidth: 200, mr: 2 }}
            >
              {isAccepting ? <CircularProgress size={20} /> : 'Accept Invitation'}
            </Button>

            <Button
              variant="outlined"
              size="large"
              onClick={() => router.push('/admin')}
              disabled={isAccepting}
            >
              Maybe Later
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    }>
      <AcceptInvitationContent />
    </Suspense>
  );
}