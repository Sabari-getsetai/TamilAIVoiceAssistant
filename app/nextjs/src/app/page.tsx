'use client';

import {
  Container,
  Typography,
  Box,
  IconButton,
  Paper,
  Button,
  Fade,
  Chip,
  Alert,
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Settings as SettingsIcon,
  VolumeUp as SpeakerIcon,
  CallEnd as CallEndIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/auth/AuthGuard';
import { chatApi } from '@/services/api/chatApi';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: Date;
  error?: boolean;
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

export default function VoiceHomePage() {
  const router = useRouter();
  
  // Connection & conversation state
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [vadConfidence, setVadConfidence] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isInitializingSession, setIsInitializingSession] = useState(false);
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const [audioChunkCount, setAudioChunkCount] = useState(0);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connected'>('disconnected');
  const [audioContextState, setAudioContextState] = useState<string>('none');
  const [microphoneStatus, setMicrophoneStatus] = useState<string>('none');
  const [streamActive, setStreamActive] = useState(false);

  // Refs for WebSocket and audio
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isRecordingRef = useRef<boolean>(false);
  const recordingStartTimeRef = useRef<number | null>(null);
  const pendingResumeListeningRef = useRef<boolean>(false); // Flag for pending resume_listening signal

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
  // Initialize session with database
  const initializeSession = useCallback(async (): Promise<string> => {
    setIsInitializingSession(true);
    setError(null);

    try {
      console.log('🔄 Creating new conversation session...');
      const sessionResponse = await chatApi.createSession({
        language: 'ta',
        rag_enabled: true
      });

      console.log('✅ Session created:', sessionResponse.session_id);
      setSessionId(sessionResponse.session_id);
      return sessionResponse.session_id;

    } catch (error) {
      console.error('❌ Failed to create session:', error);
      setError('Failed to initialize conversation session. Please try again.');
      throw error;
    } finally {
      setIsInitializingSession(false);
    }
  }, []);

  const sendAudioChunk = useCallback((audioData: Int16Array) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('🔇 Cannot send audio: WebSocket not connected');
      return;
    }
    
    try {
      // Convert Int16Array to base64
      const uint8Array = new Uint8Array(audioData.buffer);
      const base64Audio = btoa(String.fromCharCode(...uint8Array));
      
      // Calculate audio level for logging
      const audioLevel = Math.sqrt(audioData.reduce((sum, sample) => sum + sample * sample, 0) / audioData.length) / 32768;
      
      // Update chunk counter
      setAudioChunkCount(prev => prev + 1);
      
      console.log(`🎤 Audio chunk sent: ${audioData.length} samples, level: ${(audioLevel * 100).toFixed(1)}%, size: ${base64Audio.length} bytes`);
      
      wsRef.current.send(JSON.stringify({
        type: 'audio_chunk',
        audio_data: base64Audio,
        timestamp: new Date().toISOString(),
      }));
    } catch (err) {
      console.error('❌ Error sending audio chunk:', err);
    }
  }, []);

  // Initialize audio recording with Web Audio API
  const initializeAudio = useCallback(async () => {
    try {
      console.log('🎤 Initializing audio capture...');
      
      // Request microphone access with specific constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      console.log('✅ Microphone access granted');
      console.log('🔊 Stream tracks:', stream.getTracks().map(track => ({
        kind: track.kind,
        enabled: track.enabled,
        readyState: track.readyState,
        settings: track.getSettings()
      })));
      
      streamRef.current = stream;
      setMicrophoneStatus('active');
      setStreamActive(true);
      
      // Monitor stream status
      stream.getTracks().forEach(track => {
        track.onended = () => {
          console.log('🔇 Microphone track ended');
          setMicrophoneStatus('ended');
          setStreamActive(false);
        };
        track.onmute = () => {
          console.log('🔇 Microphone track muted');
          setMicrophoneStatus('muted');
        };
        track.onunmute = () => {
          console.log('🔊 Microphone track unmuted');
          setMicrophoneStatus('active');
        };
      });
      
      // Create audio context with proper sample rate
      const audioContext = new AudioContext({ 
        sampleRate: 16000,
        latencyHint: 'interactive'
      });
      
      console.log('🎵 Audio context created:', {
        state: audioContext.state,
        sampleRate: audioContext.sampleRate,
        baseLatency: audioContext.baseLatency
      });
      
      // Resume audio context if suspended (required by browser policies)
      if (audioContext.state === 'suspended') {
        console.log('▶️ Resuming suspended audio context...');
        await audioContext.resume();
        console.log('✅ Audio context resumed, state:', audioContext.state);
      }
      
      // Create analyser for audio level monitoring
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048; // Larger FFT for better resolution
      analyser.smoothingTimeConstant = 0.3;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      
      // Create media stream source
      const source = audioContext.createMediaStreamSource(stream);
      console.log('🎯 Media stream source created');
      
      // Connect source to analyser for level monitoring
      source.connect(analyser);
      
      // Create gain node for volume control
      const gainNode = audioContext.createGain();
      gainNode.gain.value = 1.0;
      source.connect(gainNode);
      
      // Set up ScriptProcessorNode for real-time audio processing
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      
      console.log('🔧 Setting up ScriptProcessorNode audio processing...');
      
      processor.onaudioprocess = (event) => {
        const currentTime = new Date().toISOString();
        const recordingState = isRecordingRef.current;
        const recordingDuration = recordingStartTimeRef.current
          ? Date.now() - recordingStartTimeRef.current
          : 0;

        console.log(`🎵 [${currentTime}] Audio process event fired`);
        console.log(`   📊 Recording state: ${recordingState}`);
        console.log(`   ⏱️  Recording duration: ${recordingDuration}ms`);
        console.log(`   🔌 WebSocket connected: ${!!wsRef.current}`);
        console.log(`   🎤 isListening: ${isListening}`);

        if (!recordingState) {
          console.log('⏸️ Not recording, skipping audio processing');
          return;
        }

        // CRITICAL FIX: Don't process/send audio while assistant is speaking
        // Check if audio is actively playing to prevent echo/feedback
        const isAudioPlaying = currentAudioRef.current && !currentAudioRef.current.paused;
        if (isAudioPlaying) {
          console.log('🔇 Skipping audio processing - assistant is speaking (audio actively playing)');
          return;
        }
        
        const inputBuffer = event.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        console.log(`🎤 Processing audio: ${inputData.length} samples`);
        
        // Calculate RMS level for real-time monitoring
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        const level = Math.min(1, rms * 10); // Amplify for better visualization
        
        console.log(`📊 Calculated audio level: ${(level * 100).toFixed(1)}%`);
        
        // Update audio level state
        setAudioLevel(level);
        
        // Convert Float32 to Int16 PCM
        const pcmData = float32ToInt16(inputData);
        
        // Send audio chunk
        sendAudioChunk(pcmData);
        
        // Log audio activity
        if (level > 0.01) {
          console.log(`🎤 Audio detected: level=${(level * 100).toFixed(1)}%, samples=${inputData.length}`);
        }
      };
      
      // Connect audio processing chain
      gainNode.connect(processor);
      processor.connect(audioContext.destination);
      
      console.log('🔗 Audio processing chain connected');
      
      // Store references
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      processorRef.current = processor;
      setAudioContextState(audioContext.state);
      
      console.log('✅ Audio initialization complete');
      console.log('🔗 Audio chain: MediaStream → Source → [Analyser + Gain] → Processor → Destination');
      
      return true;
    } catch (err) {
      console.error('❌ Audio initialization failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Microphone access failed: ${errorMessage}`);
      return false;
    }
  }, [sendAudioChunk]);

  // Monitor audio levels for visualization using time domain data
  const startAudioLevelMonitoring = () => {
    if (!analyserRef.current) {
      console.warn('⚠️ Cannot start audio monitoring: analyser not available');
      return;
    }
    
    const analyser = analyserRef.current;
    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);
    
    console.log('📊 Starting audio level monitoring with buffer size:', bufferLength);
    
    const updateLevel = () => {
      if (!isConnected || !analyserRef.current) {
        console.log('🛑 Stopping audio monitoring: disconnected');
        return;
      }
      
      // Get time domain data for accurate level measurement
      analyser.getByteTimeDomainData(dataArray);
      
      // Calculate RMS level from time domain data
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        const sample = (dataArray[i] - 128) / 128; // Convert to -1 to 1 range
        sum += sample * sample;
      }
      const rms = Math.sqrt(sum / bufferLength);
      const level = Math.min(1, rms * 5); // Amplify for better visualization
      
      // Update audio level state
      setAudioLevel(level);
      
      // Log significant audio activity
      if (level > 0.05) {
        console.log(`📊 Audio level: ${(level * 100).toFixed(1)}%`);
      }
      
      animationFrameRef.current = requestAnimationFrame(updateLevel);
    };
    
    updateLevel();
  };

  // Start listening function (simplified since recording flag is set in startConversation)
  const startListening = useCallback(async () => {
    if (!isConnected) return;
    
    console.log('🎤 Starting listening...');
    
    if (!streamRef.current) {
      console.log('🔧 No stream found, initializing audio...');
      const success = await initializeAudio();
      if (!success) return;
    }
    
    setIsListening(true);
    setError(null);
    
    // Recording flag should already be set by startConversation
    console.log('✅ Recording flag status:', isRecordingRef.current);
    
    // Notify WebSocket
    wsRef.current?.send(JSON.stringify({
      type: 'start_speaking',
      timestamp: new Date().toISOString(),
    }));
    
    startAudioLevelMonitoring();
  }, [isConnected, initializeAudio, startAudioLevelMonitoring]);

  // Add message to conversation
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  // Play audio response (backend will signal when to resume listening)
  const playAudioResponse = useCallback(async (audioData: string, text: string, isWelcome: boolean = false) => {
    try {
      console.log(`🔊 Starting audio playback for ${isWelcome ? 'welcome message' : 'assistant response'}`);
      setIsSpeaking(true);

      // Convert base64 to blob
      const audioBlob = new Blob([
        Uint8Array.from(atob(audioData), c => c.charCodeAt(0))
      ], { type: 'audio/wav' });

      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      // Clear any pending resume flag when starting new audio playback
      console.log('🔊 Starting audio playback, clearing any pending resume flag');
      pendingResumeListeningRef.current = false;

      audio.onended = () => {
        console.log('🔊 Audio playback finished');
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);

        if (isWelcome) {
          // 🎤 AUTO-START: After welcome message, automatically start listening
          console.log('👋 Welcome message finished, auto-starting recording...');
          setTimeout(() => {
            if (isConnected && !isListening) {
              startListening();
            }
          }, 500);  // Small delay to ensure audio system is ready
        } else {
          // Check if backend sent resume_listening while we were playing
          if (pendingResumeListeningRef.current) {
            console.log('🔄 Pending resume_listening detected, resuming now that audio finished');
            pendingResumeListeningRef.current = false; // Clear the flag

            // Start recording immediately (audio has finished)
            console.log('🔴 SETTING isRecordingRef.current = true (post-audio resume)');
            isRecordingRef.current = true;
            recordingStartTimeRef.current = Date.now();

            setTimeout(() => {
              console.log('🎤 Resuming listening after audio playback finished');

              // Clear audio level from speaking
              setAudioLevel(0);

              // UI state updates
              setIsListening(true);
              setIsProcessing(false);
              setError(null);

              // Notify WebSocket that we're ready for next input
              wsRef.current?.send(JSON.stringify({
                type: 'start_speaking',
                timestamp: new Date().toISOString(),
              }));

              // Restart audio level monitoring for ripple effects
              startAudioLevelMonitoring();
              console.log('✅ Seamless listening resumed after audio playback');
              console.log('📊 Final recording state:', isRecordingRef.current);
            }, 100); // Small delay after audio ends
          } else {
            // Backend will send resume_listening signal - wait for it
            console.log('🔄 Waiting for backend resume_listening signal...');
          }
        }
      };
      
      audio.onerror = () => {
        console.error('❌ Audio playback error');
        setIsSpeaking(false);
        setError('Failed to play audio response');
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
      console.log('🔊 Audio playback started successfully');
      
    } catch (err) {
      setIsSpeaking(false);
      setError('Failed to play audio response');
      console.error('❌ Audio playback error:', err);
    }
  }, [isConnected, isListening, startListening]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('Voice session connected:', message.session_id);
        break;
        
      case 'vad_result':
        setVadConfidence(message.confidence || 0);
        break;
        
      case 'stop_recording':
        console.log('🛑 Stop recording signal received from backend');

        // VALIDATION: Only stop if we've been recording for at least 1 second
        const MIN_RECORDING_DURATION_MS = 1000; // 1 second minimum
        const recordingDuration = recordingStartTimeRef.current
          ? Date.now() - recordingStartTimeRef.current
          : 0;

        if (recordingDuration < MIN_RECORDING_DURATION_MS) {
          console.log(`⏭️ Ignoring stop_recording signal - duration ${recordingDuration}ms < minimum ${MIN_RECORDING_DURATION_MS}ms`);
          console.log('🔄 Continuing to record...');
          break; // Ignore the signal and keep recording
        }

        // Duration is sufficient, stop recording
        console.log(`✅ Recording duration ${recordingDuration}ms >= minimum, stopping...`);
        isRecordingRef.current = false;
        recordingStartTimeRef.current = null;  // Reset timestamp
        setIsListening(false);
        setIsProcessing(true);
        console.log('⏸️ Recording stopped, entering processing state');
        break;
        
      case 'transcription':
        addMessage({
          id: `user_${crypto.randomUUID()}`,
          type: 'user',
          content: message.text || '',
          timestamp: new Date(),
        });
        // Still processing - waiting for response
        setIsProcessing(true);
        break;
        
      case 'chat_response':
        addMessage({
          id: `assistant_${crypto.randomUUID()}`,
          type: 'assistant',
          content: message.text || '',
          timestamp: new Date(),
        });
        // Response received, still processing TTS
        break;
        
      case 'audio_response':
        if (message.audio_data && message.text) {
          // Exit processing state when audio response arrives
          setIsProcessing(false);
          const isWelcome = message.is_welcome === true;
          playAudioResponse(message.audio_data, message.text, isWelcome);
        }
        break;

      case 'resume_listening':
        // 🔄 SEAMLESS CONVERSATION: Backend signals to resume listening
        console.log('🔄 Resume listening signal received from backend');
        console.log('🔍 Current state - isConnected:', isConnected, 'isSpeaking:', isSpeaking, 'isProcessing:', isProcessing);
        console.log('🔍 Audio refs - audioContext:', !!audioContextRef.current, 'processor:', !!processorRef.current, 'stream:', !!streamRef.current);
        console.log('🔍 WebSocket ref:', !!wsRef.current, 'readyState:', wsRef.current?.readyState);

        // CRITICAL FIX: Use wsRef instead of isConnected state to avoid stale closure
        // Check if WebSocket is actually connected (readyState === 1)
        const isWsConnected = wsRef.current?.readyState === WebSocket.OPEN;
        console.log('🔍 WebSocket actually connected:', isWsConnected);

        if (!isWsConnected) {
          console.warn('⚠️ Cannot resume listening: WebSocket not connected (readyState:', wsRef.current?.readyState, ')');
          break;
        }

        // CRITICAL FIX: Don't start recording while audio is playing
        // Check ACTUAL audio playback status (not state which can be stale due to React closure)
        const isAudioPlaying = currentAudioRef.current && !currentAudioRef.current.paused;
        console.log('🔍 Checking if audio is playing:', isAudioPlaying);
        console.log('   currentAudioRef exists:', !!currentAudioRef.current);
        console.log('   audio.paused:', currentAudioRef.current?.paused);

        if (isAudioPlaying) {
          console.log('🔊 Audio is ACTIVELY playing, setting pendingResumeListening flag');
          console.log('   Will resume recording when audio.onended fires');
          pendingResumeListeningRef.current = true;
          break; // Exit early, audio.onended will handle resume
        }

        console.log('✅ Audio is NOT playing, safe to resume immediately');

        // Audio is not playing, safe to resume immediately
        console.log('✅ Audio not playing, resuming listening immediately');

        // CRITICAL FIX: Set recording flag IMMEDIATELY before any delays
        // This prevents race condition with processor.onaudioprocess callback
        console.log('🔴 SETTING isRecordingRef.current = true IMMEDIATELY (before setTimeout)');
        isRecordingRef.current = true;
        recordingStartTimeRef.current = Date.now();
        console.log('✅ Recording flag set to:', isRecordingRef.current);

        // Now handle UI updates with small delay for smooth transition
        setTimeout(() => {
          console.log('🎤 Backend-triggered listening resumption for seamless conversation');

          // Clear audio level from speaking
          setAudioLevel(0);

          // UI state updates
          setIsListening(true);
          setIsProcessing(false);
          setError(null);

          // Notify WebSocket that we're ready for next input
          wsRef.current?.send(JSON.stringify({
            type: 'start_speaking',
            timestamp: new Date().toISOString(),
          }));

          // Restart audio level monitoring for ripple effects
          startAudioLevelMonitoring();
          console.log('✅ Seamless listening resumed via backend signal with ripple effects');
          console.log('📊 Final recording state:', isRecordingRef.current);
        }, 50); // Reduced delay from 100ms to 50ms
        break;
        
      case 'speaking_started':
        setIsListening(true);
        isRecordingRef.current = true;
        recordingStartTimeRef.current = Date.now();  // Track when recording started
        setIsProcessing(false);
        break;
        
      case 'speaking_stopped':
        setIsListening(false);
        isRecordingRef.current = false;
        break;
        
      case 'interrupted':
        setIsSpeaking(false);
        setIsProcessing(false);
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
        }
        break;
        
      case 'error':
        setError(message.message || 'Unknown error occurred');
        setIsProcessing(false);
        addMessage({
          id: `error_${crypto.randomUUID()}`,
          type: 'error',
          content: message.message || 'An error occurred',
          timestamp: new Date(),
          error: true,
        });
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  }, [addMessage, playAudioResponse, isConnected, isSpeaking, isProcessing, startAudioLevelMonitoring]);

  // Stop listening
  const stopListening = () => {
    setIsListening(false);
    isRecordingRef.current = false;
    
    // Notify WebSocket
    wsRef.current?.send(JSON.stringify({
      type: 'stop_speaking',
      timestamp: new Date().toISOString(),
    }));
  };

  // Start conversation (WebSocket connection)
  const startConversation = async () => {
    try {
      setError(null);

      // Create database session if not already created
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        console.log('🔄 No session found, creating new session...');
        currentSessionId = await initializeSession();
      }

      // Set recording flag BEFORE initializing audio to avoid timing issues
      console.log('🔴 Pre-setting recording flag to true before audio initialization');
      isRecordingRef.current = true;
      recordingStartTimeRef.current = Date.now();  // Track when recording started

      // Initialize audio first
      const audioSuccess = await initializeAudio();
      if (!audioSuccess) {
        isRecordingRef.current = false;
        return;
      }

      // Connect WebSocket with valid session ID
      const wsUrl = `ws://localhost:8000/ws/voice/${currentSessionId}`;
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setWsStatus('connected');
        wsRef.current = ws;
        
        // Set UI state and start monitoring
        setIsListening(true);
        setError(null);
        
        // Confirm recording is active
        console.log('✅ WebSocket connected, recording flag confirmed:', isRecordingRef.current);
        
        // Notify WebSocket that we're ready to listen
        ws.send(JSON.stringify({
          type: 'start_speaking',
          timestamp: new Date().toISOString(),
        }));
        
        // Start audio level monitoring
        startAudioLevelMonitoring();
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data) as WebSocketMessage;
        console.log('📨 WebSocket message received:', message.type, message);
        handleWebSocketMessage(message);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected', { code: event.code, reason: event.reason });
        setIsConnected(false);
        setIsListening(false);
        setIsSpeaking(false);
        isRecordingRef.current = false;

        // Handle specific close codes from backend
        if (event.code === 4004) {
          setError('Session not found. Please start a new conversation.');
          setSessionId(null); // Clear invalid session
        } else if (event.code === 4005) {
          setError('Session expired or inactive. Please start a new conversation.');
          setSessionId(null); // Clear invalid session
        } else if (event.code === 4000) {
          setError('Session validation failed. Please try again.');
          setSessionId(null); // Clear invalid session
        } else if (event.code === 1000) {
          // Normal closure
          console.log('Connection closed normally');
        } else {
          setError('Connection lost. Please try again.');
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please check if the backend is running.');
        setIsConnected(false);
        isRecordingRef.current = false;
      };
      
    } catch (err) {
      setError('Failed to start conversation. Please try again.');
      console.error('Conversation start error:', err);
      isRecordingRef.current = false;
    }
  };

  // End conversation
  const endConversation = async () => {
    // Clean up session in database
    if (sessionId) {
      try {
        console.log('🧹 Cleaning up session:', sessionId);
        await chatApi.deleteSession(sessionId);
        console.log('✅ Session cleaned up successfully');
      } catch (error) {
        console.warn('⚠️ Failed to clean up session:', error);
        // Don't throw error for cleanup failures
      }
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Stop audio monitoring
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Stop recording
    isRecordingRef.current = false;
    
    // Clean up audio resources
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setAudioLevel(0);
    setVadConfidence(0);
    setSessionId(null); // Clear session ID
  };

  const clearConversation = () => {
    setMessages([]);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      endConversation();
    };
  }, []);

  // Handle mic button click
  const handleMicClick = () => {
    if (isConnected) {
      endConversation();
    } else {
      startConversation();
    }
  };

  return (
    <AuthGuard requireOrganization={true}>
      <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: 'white',
            fontWeight: 'bold',
            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
          }}
        >
          Tamil AI Voice Assistant
        </Typography>
        <Button
          variant="outlined"
          startIcon={<SettingsIcon />}
          onClick={() => router.push('/org/settings')}
          sx={{
            color: 'white',
            borderColor: 'rgba(255,255,255,0.5)',
            '&:hover': {
              borderColor: 'white',
              backgroundColor: 'rgba(255,255,255,0.1)',
            },
          }}
        >
          Settings
        </Button>
      </Box>

      {/* Main Content */}
      <Container
        maxWidth="md"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 8,
        }}
      >
        {/* Error Display */}
        {error && (
          <Fade in={true}>
            <Alert
              severity="error"
              onClose={() => setError(null)}
              sx={{ width: '100%', mb: 3 }}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {/* Conversation Area */}
        {messages.length > 0 && (
          <Fade in={true}>
            <Paper
              elevation={8}
              sx={{
                width: '100%',
                maxHeight: '300px',
                overflowY: 'auto',
                mb: 4,
                p: 3,
                backgroundColor: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(10px)',
              }}
            >
              {messages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    mb: 2,
                    display: 'flex',
                    justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Paper
                    elevation={2}
                    sx={{
                      p: 2,
                      maxWidth: '80%',
                      backgroundColor: 
                        message.type === 'user' ? 'primary.main' : 
                        message.type === 'error' ? 'error.light' : 'grey.100',
                      color: 
                        message.type === 'user' ? 'white' : 
                        message.type === 'error' ? 'error.contrastText' : 'text.primary',
                      border: message.type === 'error' ? '1px solid' : 'none',
                      borderColor: message.type === 'error' ? 'error.main' : 'transparent',
                    }}
                  >
                    {message.type === 'error' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <ErrorIcon fontSize="small" />
                        <Typography variant="caption" fontWeight="bold">
                          Warning
                        </Typography>
                      </Box>
                    )}
                    <Typography variant="body1">{message.content}</Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        opacity: 0.7,
                        display: 'block',
                        mt: 0.5,
                      }}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Paper>
                </Box>
              ))}
            </Paper>
          </Fade>
        )}

        {/* Voice Interface */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
          }}
        >
          {/* Status Indicators */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            {isConnected && (
              <Chip
                label="🔄 Seamless Mode"
                color="success"
                variant="filled"
                sx={{ 
                  animation: 'pulse 2s infinite',
                  fontWeight: 'bold'
                }}
              />
            )}
            {isListening && (
              <Chip
                icon={<MicIcon />}
                label={`Listening... ${(audioLevel * 100).toFixed(0)}%`}
                color="primary"
                variant="filled"
                sx={{ animation: 'pulse 1.5s infinite' }}
              />
            )}
            {isProcessing && (
              <Chip
                label="Processing..."
                color="warning"
                variant="filled"
                sx={{ animation: 'pulse 1.5s infinite' }}
              />
            )}
            {isSpeaking && (
              <Chip
                icon={<SpeakerIcon />}
                label="Speaking..."
                color="info"
                variant="filled"
                sx={{ animation: 'pulse 1.5s infinite' }}
              />
            )}
            {vadConfidence > 0 && (
              <Chip
                label={`Voice: ${(vadConfidence * 100).toFixed(0)}%`}
                color={vadConfidence > 0.5 ? "success" : "warning"}
                variant="outlined"
                sx={{ 
                  color: 'white',
                  borderColor: vadConfidence > 0.5 ? 'rgba(76, 175, 80, 0.8)' : 'rgba(255, 193, 7, 0.8)',
                  backgroundColor: vadConfidence > 0.5 ? 'rgba(76, 175, 80, 0.2)' : 'rgba(255, 193, 7, 0.2)',
                }}
              />
            )}
            {audioChunkCount > 0 && showDebugInfo && (
              <Chip
                label={`Chunks: ${audioChunkCount}`}
                variant="outlined"
                sx={{ 
                  color: 'white',
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                }}
              />
            )}
          </Box>

          {/* Audio Visualization Container */}
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Enhanced Audio Level Rings - Show for listening and speaking, hide during processing */}
            {(isListening || isSpeaking) && !isProcessing && (
              <>
                {[1, 2, 3, 4].map((ring) => {
                  // Different colors for listening vs speaking
                  const ringColor = isSpeaking
                    ? 'rgba(33, 150, 243, 0.4)' // Blue for speaking
                    : vadConfidence > 0.5 
                    ? 'rgba(76, 175, 80, 0.4)' // Green for voice detected
                    : audioLevel > 0.3 
                    ? 'rgba(255, 193, 7, 0.4)' // Yellow for audio detected
                    : 'rgba(244, 67, 54, 0.3)'; // Red for listening
                  
                  return (
                    <Box
                      key={ring}
                      sx={{
                        position: 'absolute',
                        width: 120 + (ring * 25),
                        height: 120 + (ring * 25),
                        borderRadius: '50%',
                        border: `${ring === 1 ? 3 : 2}px solid ${ringColor}`,
                        opacity: Math.max(0.1, (audioLevel + vadConfidence) * ring * 0.25),
                        transform: `scale(${1 + ((audioLevel + vadConfidence) * ring * 0.08)})`,
                        transition: 'all 0.1s ease-out',
                        animation: isSpeaking
                          ? `speakingRipple ${1 + ring * 0.4}s infinite`
                          : vadConfidence > 0.5 
                          ? `voiceRipple ${1 + ring * 0.3}s infinite`
                          : `ripple ${1 + ring * 0.5}s infinite`,
                      }}
                    />
                  );
                })}
              </>
            )}

            {/* Enhanced Main Microphone Button */}
            <IconButton
              onClick={handleMicClick}
              disabled={error !== null || isProcessing || isInitializingSession}
              sx={{
                width: 120,
                height: 120,
                backgroundColor: isConnected 
                  ? isProcessing
                    ? 'warning.main' // Orange for processing
                    : isSpeaking
                    ? 'info.main' // Blue for speaking
                    : vadConfidence > 0.5 
                    ? 'success.main' // Green for voice detected
                    : isListening 
                    ? 'error.main' // Red for listening
                    : 'success.main' 
                  : 'white',
                color: isConnected ? 'white' : 'primary.main',
                boxShadow: isConnected && isSpeaking
                  ? '0 0 40px rgba(33, 150, 243, 0.8)' // Blue glow for speaking
                  : isConnected && isListening
                  ? vadConfidence > 0.5
                    ? `0 0 ${40 + (vadConfidence * 30)}px rgba(76, 175, 80, ${0.7 + (vadConfidence * 0.3)})`
                    : `0 0 ${30 + (audioLevel * 20)}px rgba(244, 67, 54, ${0.6 + (audioLevel * 0.3)})`
                  : isConnected && isProcessing
                  ? '0 0 30px rgba(255, 152, 0, 0.6)' // Orange glow for processing
                  : isConnected
                  ? '0 8px 32px rgba(76, 175, 80, 0.4)'
                  : '0 8px 32px rgba(0,0,0,0.3)',
                transform: isConnected && (isListening || isSpeaking)
                  ? `scale(${1.1 + ((audioLevel + vadConfidence) * 0.08)})` 
                  : isConnected && isProcessing
                  ? 'scale(1.05)'
                  : 'scale(1)',
                transition: 'all 0.2s ease-in-out',
                zIndex: 10,
                '&:hover': {
                  transform: isConnected && (isListening || isSpeaking)
                    ? `scale(${1.15 + ((audioLevel + vadConfidence) * 0.1)})` 
                    : 'scale(1.05)',
                  boxShadow: isConnected && isSpeaking
                    ? '0 0 50px rgba(33, 150, 243, 0.9)'
                    : isConnected && isListening
                    ? vadConfidence > 0.5
                      ? `0 0 ${50 + (vadConfidence * 40)}px rgba(76, 175, 80, ${0.8 + (vadConfidence * 0.2)})`
                      : `0 0 ${40 + (audioLevel * 30)}px rgba(244, 67, 54, ${0.8 + (audioLevel * 0.2)})`
                    : isConnected
                    ? '0 12px 40px rgba(76, 175, 80, 0.6)'
                    : '0 12px 40px rgba(0,0,0,0.4)',
                },
                '&:disabled': {
                  backgroundColor: 'grey.300',
                  color: 'grey.500',
                  opacity: 0.5,
                },
              }}
            >
              {isConnected ? (
                <CallEndIcon sx={{ fontSize: 48 }} />
              ) : (
                <MicIcon sx={{ fontSize: 48 }} />
              )}
            </IconButton>
          </Box>

          {/* Instructions */}
          <Typography
            variant="h6"
            sx={{
              color: 'white',
              textAlign: 'center',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              maxWidth: 500,
            }}
          >
            {error
              ? 'Please resolve the error above to continue'
              : isInitializingSession
              ? 'Initializing conversation session...'
              : !isConnected
              ? 'Click the microphone to start a seamless conversation'
              : isListening
              ? 'Listening... Speak naturally, conversation will continue automatically'
              : isProcessing
              ? 'Processing your speech...'
              : isSpeaking
              ? 'AI is speaking... Will resume listening automatically'
              : 'Connected - Seamless conversation mode active'}
          </Typography>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            {messages.length > 0 && (
              <Button
                variant="outlined"
                onClick={clearConversation}
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255,255,255,0.5)',
                  '&:hover': {
                    borderColor: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                  },
                }}
              >
                Clear Conversation
              </Button>
            )}
            {isConnected && (
              <Button
                variant="outlined"
                onClick={() => setShowDebugInfo(!showDebugInfo)}
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255,255,255,0.5)',
                  '&:hover': {
                    borderColor: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                  },
                }}
              >
                {showDebugInfo ? 'Hide Debug' : 'Show Debug'}
              </Button>
            )}
          </Box>

          {/* Debug Information Panel */}
          {showDebugInfo && isConnected && (
            <Fade in={true}>
              <Paper
                elevation={4}
                sx={{
                  p: 2,
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  borderRadius: 2,
                  minWidth: 300,
                }}
              >
                <Typography variant="h6" sx={{ mb: 2, color: 'white' }}>
                  Debug Information
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, fontSize: '0.875rem' }}>
                  <Typography>Audio Level:</Typography>
                  <Typography>{(audioLevel * 100).toFixed(1)}%</Typography>
                  
                  <Typography>VAD Confidence:</Typography>
                  <Typography>{(vadConfidence * 100).toFixed(1)}%</Typography>
                  
                  <Typography>Audio Chunks:</Typography>
                  <Typography>{audioChunkCount}</Typography>
                  
                  <Typography>Session ID:</Typography>
                  <Typography sx={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>
                    {sessionId ? sessionId.slice(-8) + '...' : 'Not created'}
                  </Typography>
                  
                  <Typography>WebSocket:</Typography>
                  <Typography color={wsStatus === 'connected' ? 'success.main' : 'error.main'}>
                    {wsStatus === 'connected' ? 'Connected' : 'Disconnected'}
                  </Typography>
                  
                  <Typography>Audio Context:</Typography>
                  <Typography color={audioContextState === 'running' ? 'success.main' : 'warning.main'}>
                    {audioContextState}
                  </Typography>
                  
                  <Typography>Microphone:</Typography>
                  <Typography color={microphoneStatus === 'active' ? 'success.main' : 'error.main'}>
                    {microphoneStatus}
                  </Typography>
                  
                  <Typography>Stream Active:</Typography>
                  <Typography color={streamActive ? 'success.main' : 'error.main'}>
                    {streamActive ? 'Yes' : 'No'}
                  </Typography>
                </Box>
              </Paper>
            </Fade>
          )}
        </Box>
      </Container>

      {/* CSS Animations */}
      <style jsx global>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        
        @keyframes ripple {
          0% {
            transform: scale(1);
            opacity: 0.8;
          }
          100% {
            transform: scale(1.2);
            opacity: 0;
          }
        }
        
        @keyframes voiceRipple {
          0% {
            transform: scale(1);
            opacity: 0.9;
          }
          50% {
            transform: scale(1.15);
            opacity: 0.6;
          }
          100% {
            transform: scale(1.3);
            opacity: 0;
          }
        }
        
        @keyframes speakingRipple {
          0% {
            transform: scale(1);
            opacity: 0.8;
          }
          50% {
            transform: scale(1.2);
            opacity: 0.5;
          }
          100% {
            transform: scale(1.4);
            opacity: 0;
          }
        }
      `}</style>
    </Box>
    </AuthGuard>
  );
}
