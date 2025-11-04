'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  Slider,
  FormControlLabel,
  Switch,
  Divider,
} from '@mui/material';
import {
  Mic,
  MicOff,
  VolumeUp,
  VolumeOff,
  Settings,
  CallEnd,
  Phone,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  audioUrl?: string;
}

interface VoiceSettings {
  vadSensitivity: number;
  autoInterrupt: boolean;
  continuousListening: boolean;
}

interface WebSocketMessage {
  type: string;
  session_id?: string;
  confidence?: number;
  is_speech?: boolean;
  text?: string;
  audio_data?: string;
  message?: string;
  [key: string]: unknown;
}

const RealTimeVoiceAssistant: React.FC = () => {
  const theme = useTheme();
  
  // State management
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [vadConfidence, setVadConfidence] = useState(0);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [showSettings, setShowSettings] = useState(false);
  const [isUserInitiatedListening, setIsUserInitiatedListening] = useState(false);
  const [settings, setSettings] = useState<VoiceSettings>({
    vadSensitivity: 0.5,
    autoInterrupt: true,
    continuousListening: false,
  });

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const isRecordingRef = useRef<boolean>(false);

  // Add message to conversation
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  // Ref to store startListening function to avoid circular dependency
  const startListeningRef = useRef<(() => Promise<void>) | null>(null);

  // Play audio response
  const playAudioResponse = useCallback(async (audioData: string, text: string) => {
    try {
      setIsSpeaking(true);
      
      // Convert base64 to blob
      const audioBlob = new Blob([
        Uint8Array.from(atob(audioData), c => c.charCodeAt(0))
      ], { type: 'audio/wav' });
      
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);

        // 🔄 SEAMLESS CONVERSATION: Don't auto-resume here
        // Backend will send 'resume_listening' signal to control the flow
        console.log('🎵 Audio playback ended, waiting for backend resume signal');
      };
      
      audio.onerror = () => {
        setIsSpeaking(false);
        setError('Failed to play audio response');
      };
      
      await audio.play();
      
    } catch (err) {
      setIsSpeaking(false);
      setError('Failed to play audio response');
      console.error('Audio playback error:', err);
    }
  }, [settings.continuousListening, isUserInitiatedListening]);

  // Convert Float32 audio to Int16 PCM
  const float32ToInt16 = (float32Array: Float32Array): Int16Array => {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
  };

  // Send audio chunk to WebSocket
  const sendAudioChunk = useCallback((audioData: Int16Array) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    try {
      // Convert Int16Array to base64
      const uint8Array = new Uint8Array(audioData.buffer);
      const base64Audio = btoa(String.fromCharCode(...uint8Array));
      
      wsRef.current.send(JSON.stringify({
        type: 'audio_chunk',
        audio_data: base64Audio,
        timestamp: new Date().toISOString(),
      }));
    } catch (err) {
      console.error('Error sending audio chunk:', err);
    }
  }, []);

  // Initialize audio recording with Web Audio API
  const initializeAudio = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      
      streamRef.current = stream;
      
      // Set up audio context
      const audioContext = new AudioContext({ sampleRate: 16000 });
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Set up ScriptProcessorNode for real-time audio processing
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      processor.onaudioprocess = (event) => {
        console.log('🎵 Audio process event fired, recording state:', isRecordingRef.current);
        
        if (!isRecordingRef.current) {
          console.log('⏸️ Not recording, skipping audio processing');
          return;
        }
        
        console.log('🎙️ Processing audio data for transmission');
        const inputBuffer = event.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        // Convert Float32 to Int16 PCM
        const pcmData = float32ToInt16(inputData);
        
        // Send audio chunk
        sendAudioChunk(pcmData);
      };
      
      processorRef.current = processor;
      
      return true;
    } catch (err) {
      setError('Microphone access denied. Please allow microphone permissions.');
      console.error('Audio initialization error:', err);
      return false;
    }
  }, [sendAudioChunk]);

  // Monitor audio levels for visualization
  const startAudioLevelMonitoring = useCallback(() => {
    if (!analyserRef.current) return;
    
    const analyser = analyserRef.current;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(average / 255);
      
      if (isListening || settings.continuousListening) {
        requestAnimationFrame(updateLevel);
      }
    };
    
    updateLevel();
  }, [isListening, settings.continuousListening]);

  // Start listening function
  const startListening = useCallback(async () => {
    console.log('🎙️ Starting listening process...');
    
    if (!isConnected) {
      setError('Not connected to voice service');
      return;
    }
    
    // Set recording state BEFORE initializing audio
    console.log('✅ Setting recording state to true');
    setIsListening(true);
    setError(null);
    isRecordingRef.current = true;
    
    if (!streamRef.current) {
      console.log('🎵 Initializing audio for the first time...');
      const success = await initializeAudio();
      if (!success) {
        console.log('❌ Audio initialization failed, resetting recording state');
        setIsListening(false);
        isRecordingRef.current = false;
        return;
      }
      console.log('✅ Audio initialized successfully');
    }
    
    // Notify WebSocket
    wsRef.current?.send(JSON.stringify({
      type: 'start_speaking',
      timestamp: new Date().toISOString(),
    }));
    
    startAudioLevelMonitoring();
    console.log('🎙️ Listening started successfully');
  }, [isConnected, initializeAudio, startAudioLevelMonitoring]);

  // Update ref when startListening changes
  useEffect(() => {
    startListeningRef.current = startListening;
  }, [startListening]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('Voice session connected:', message.session_id);
        break;
        
      case 'vad_result':
        setVadConfidence(message.confidence || 0);
        if (message.is_speech && !isListening && settings.continuousListening && startListeningRef.current) {
          startListeningRef.current();
        }
        break;
        
      case 'transcription':
        addMessage({
          id: `user_${crypto.randomUUID()}`,
          type: 'user',
          text: message.text || '',
          timestamp: new Date(),
        });
        break;
        
      case 'chat_response':
        addMessage({
          id: `assistant_${crypto.randomUUID()}`,
          type: 'assistant',
          text: message.text || '',
          timestamp: new Date(),
        });
        break;
        
      case 'audio_response':
        if (message.audio_data && message.text) {
          playAudioResponse(message.audio_data, message.text);
        }
        break;
        
      case 'speaking_started':
        setIsListening(true);
        break;
        
      case 'speaking_stopped':
        setIsListening(false);
        break;
        
      case 'interrupted':
        setIsSpeaking(false);
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
        }
        break;
        
      case 'error':
        setError(message.message || 'Unknown error occurred');
        break;

      case 'resume_listening':
        // 🔄 SEAMLESS CONVERSATION: Backend signals to resume listening
        console.log('🔄 Resume listening signal received from backend');
        setTimeout(() => {
          if (isConnected && !isSpeaking) {
            setIsListening(true);
            isRecordingRef.current = true;
            setError(null);

            // Notify backend that we're starting to listen
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({
                type: 'start_speaking',
                timestamp: new Date().toISOString(),
              }));
            }

            // Restart audio level monitoring
            if (startListeningRef.current) {
              startListeningRef.current();
            }

            console.log('✅ Seamless listening resumed via backend signal');
          }
        }, 100);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [addMessage, isListening, settings.continuousListening, startListening, playAudioResponse]);

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      const wsUrl = `ws://localhost:8000/ws/voice/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data) as WebSocketMessage;
        handleWebSocketMessage(message);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsListening(false);
        setIsSpeaking(false);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please try again.');
        setIsConnected(false);
      };
      
      wsRef.current = ws;
    } catch (err) {
      setError('Failed to connect to voice service');
      console.error('WebSocket connection error:', err);
    }
  }, [sessionId, handleWebSocketMessage]);

  // Stop listening
  const stopListening = useCallback(() => {
    console.log('🛑 Stopping listening process...');
    setIsListening(false);
    setIsUserInitiatedListening(false); // Clear user-initiated flag
    isRecordingRef.current = false;
    console.log('✅ Recording state set to false');
    
    // Notify WebSocket
    wsRef.current?.send(JSON.stringify({
      type: 'stop_speaking',
      timestamp: new Date().toISOString(),
    }));
    console.log('🛑 Listening stopped successfully');
  }, []);

  // Interrupt assistant speech
  const interruptSpeech = () => {
    if (isSpeaking) {
      wsRef.current?.send(JSON.stringify({
        type: 'interrupt',
        timestamp: new Date().toISOString(),
      }));
    }
  };

  // Start/end conversation
  const startConversation = () => {
    connectWebSocket();
  };

  const endConversation = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Clean up audio resources
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
    setMessages([]);
    setIsListening(false);
    setIsSpeaking(false);
    setAudioLevel(0);
    setVadConfidence(0);
  };

  // Update settings
  const updateSettings = (newSettings: Partial<VoiceSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    
    // Send config update to WebSocket
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({
        type: 'config',
        config: {
          vad_sensitivity: updatedSettings.vadSensitivity,
        },
        timestamp: new Date().toISOString(),
      }));
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      endConversation();
    };
  }, []);

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5" component="h1">
              🎤 Real-Time Voice Assistant
            </Typography>
            <Box>
              <IconButton onClick={() => setShowSettings(!showSettings)}>
                <Settings />
              </IconButton>
            </Box>
          </Box>

          {/* Connection Status */}
          <Box sx={{ mb: 2 }}>
            <Chip
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'default'}
              variant="outlined"
              sx={{ mr: 1 }}
            />
            {isListening && (
              <Chip
                label="Listening"
                color="primary"
                variant="filled"
                sx={{ mr: 1 }}
              />
            )}
            {isSpeaking && (
              <Chip
                label="Speaking"
                color="secondary"
                variant="filled"
                sx={{ mr: 1 }}
              />
            )}
          </Box>

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Settings Panel */}
          {showSettings && (
            <Card variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Voice Settings
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  VAD Sensitivity: {Math.round(settings.vadSensitivity * 100)}%
                </Typography>
                <Slider
                  value={settings.vadSensitivity}
                  onChange={(_, value) => updateSettings({ vadSensitivity: value as number })}
                  min={0}
                  max={1}
                  step={0.1}
                  marks
                />
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoInterrupt}
                    onChange={(e) => updateSettings({ autoInterrupt: e.target.checked })}
                  />
                }
                label="Auto-interrupt when speaking"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.continuousListening}
                    onChange={(e) => updateSettings({ continuousListening: e.target.checked })}
                  />
                }
                label="Continuous listening mode"
              />
            </Card>
          )}

          {/* Audio Visualization */}
          {(isListening || isSpeaking) && (
            <Card variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Audio Activity
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Audio Level: {Math.round(audioLevel * 100)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={audioLevel * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Voice Activity: {Math.round(vadConfidence * 100)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={vadConfidence * 100}
                  color="secondary"
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </Card>
          )}

          {/* Control Buttons */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, justifyContent: 'center' }}>
            {!isConnected ? (
              <Button
                variant="contained"
                size="large"
                startIcon={<Phone />}
                onClick={startConversation}
                sx={{ minWidth: 200 }}
              >
                Start Conversation
              </Button>
            ) : (
              <>
                <Button
                  variant={isListening ? "contained" : "outlined"}
                  size="large"
                  startIcon={isListening ? <Mic /> : <MicOff />}
                  onClick={isListening ? stopListening : () => {
                    setIsUserInitiatedListening(true); // Mark as user-initiated
                    startListening();
                  }}
                  disabled={isSpeaking}
                  color={isListening ? "primary" : "inherit"}
                >
                  {isListening ? "Stop Listening" : "Start Listening"}
                </Button>
                
                {isSpeaking && (
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<VolumeOff />}
                    onClick={interruptSpeech}
                    color="warning"
                  >
                    Interrupt
                  </Button>
                )}
                
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<CallEnd />}
                  onClick={endConversation}
                  color="error"
                >
                  End Call
                </Button>
              </>
            )}
          </Box>

          <Divider sx={{ mb: 2 }} />

          {/* Conversation History */}
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Conversation
            </Typography>
            
            {messages.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                {isConnected ? "Start speaking to begin the conversation..." : "Connect to start chatting"}
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {messages.map((message) => (
                  <Card
                    key={message.id}
                    variant="outlined"
                    sx={{
                      alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '80%',
                      bgcolor: message.type === 'user' 
                        ? theme.palette.primary.light 
                        : theme.palette.grey[100],
                    }}
                  >
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {message.type === 'user' ? '👤 You' : '🤖 Assistant'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                      <Typography variant="body1">
                        {message.text}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Box>

          {/* Status Information */}
          {isConnected && (
            <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.grey[50], borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Session ID: {sessionId}
              </Typography>
              <br />
              <Typography variant="caption" color="text.secondary">
                Status: {isListening ? 'Listening for speech...' : isSpeaking ? 'Assistant speaking...' : 'Ready'}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default RealTimeVoiceAssistant;
