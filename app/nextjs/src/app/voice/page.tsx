'use client';

import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import RealTimeVoiceAssistant from '@/components/voice/RealTimeVoiceAssistant';
import ProtectedLayout from '@/components/layout/ProtectedLayout';

const VoicePage: React.FC = () => {
  return (
    <ProtectedLayout title="Voice Assistant" showSidebar={false}>
      <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Voice Assistant
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          Have a natural conversation with your Tamil AI assistant
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Click "Start Conversation" to begin. The assistant will listen to your voice,
          understand your questions, and respond with both text and speech.
        </Typography>
      </Box>
      
      <RealTimeVoiceAssistant />
    </Container>
    </ProtectedLayout>
  );
};

export default VoicePage;
