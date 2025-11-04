"""
WebSocket API for Real-time Voice Conversation
"""
import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import numpy as np
from datetime import datetime
import io
import wave

from backend.settings import settings
from backend.speech.vad import VoiceActivityDetector
from backend.speech.stt import FasterWhisperSTT
from backend.speech.tts import get_tts_engine, initialize_tts
from backend.graphs.chat_graph import process_conversation_turn, create_session as create_chat_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    """Manages WebSocket connections for real-time voice chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, dict] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        # Create chat session
        chat_session_id = create_chat_session(language="ta", rag_enabled=True)
        
        # Initialize STT and load model
        stt = FasterWhisperSTT()
        try:
            stt.load_model()
            logger.info(f"STT model loaded successfully for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to load STT model for session {session_id}: {e}")
        
        # Initialize TTS and load model (using configured engine - Google Cloud TTS or gTTS fallback)
        try:
            initialize_tts()
            tts = get_tts_engine()
            logger.info(f"TTS engine initialized for session {session_id}: {type(tts).__name__}")
            if hasattr(tts, 'voice_name'):
                logger.info(f"  Voice: {tts.voice_name} ({tts.voice_type})")
        except Exception as e:
            logger.error(f"Failed to initialize TTS for session {session_id}: {e}")
            # Fallback to basic gTTS if initialization fails
            from backend.speech.tts import GoogleTTS
            tts = GoogleTTS()
            tts.load_model()
        
        self.session_data[session_id] = {
            "vad": VoiceActivityDetector(),
            "stt": stt,
            "tts": tts,
            "chat_session_id": chat_session_id,
            "is_speaking": False,
            "audio_buffer": [],
            "last_activity": datetime.now()
        }
        logger.info(f"WebSocket connected: {session_id}")
        
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")
        
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                # Check WebSocket state before sending
                if websocket.client_state.name != "CONNECTED":
                    logger.warning(f"WebSocket not connected for {session_id}, state: {websocket.client_state.name}")
                    self.disconnect(session_id)
                    return
                
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

    def update_all_tts_instances(self):
        """Update TTS instances in all active sessions with fresh configuration"""
        from backend.speech.tts import get_tts_engine, initialize_tts

        initialize_tts()
        new_tts = get_tts_engine()

        updated_count = 0
        for session_id, session_data in self.session_data.items():
            session_data['tts'] = new_tts
            updated_count += 1
            logger.info(f"Updated TTS for session {session_id} to {type(new_tts).__name__}")

        return updated_count

manager = ConnectionManager()

def numpy_to_wav_bytes(audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Convert numpy audio array to WAV format bytes
    
    Args:
        audio_data: Audio data as numpy array (float32, range -1 to 1)
        sample_rate: Sample rate in Hz
        
    Returns:
        WAV file as bytes
    """
    # Convert float32 to int16 PCM
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    # Get WAV bytes
    wav_bytes = wav_buffer.getvalue()
    wav_buffer.close()
    
    return wav_bytes

@router.websocket("/voice/{session_id}")
async def websocket_voice_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice conversation
    
    Message Types:
    - audio_chunk: Raw audio data for processing
    - start_speaking: User started speaking
    - stop_speaking: User stopped speaking
    - interrupt: Interrupt assistant speech
    - config: Update session configuration
    """
    await manager.connect(websocket, session_id)
    session = manager.session_data[session_id]
    
    try:
        # Send initial connection confirmation
        await manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send welcome message
        await send_welcome_message(session_id, session)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                await handle_audio_chunk(session_id, message, session)
                
            elif message_type == "start_speaking":
                await handle_start_speaking(session_id, session)
                
            elif message_type == "stop_speaking":
                await handle_stop_speaking(session_id, session)
                
            elif message_type == "interrupt":
                await handle_interrupt(session_id, session)
                
            elif message_type == "config":
                await handle_config_update(session_id, message, session)
                
            elif message_type == "ping":
                await manager.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
    finally:
        manager.disconnect(session_id)

async def send_welcome_message(session_id: str, session: dict):
    """Send welcome message with TTS audio"""
    try:
        # Professional Tamil welcome message
        welcome_text = "வணக்கம்! உங்களை வரவேற்கிறேன். உங்களுக்கு என்ன உதவி தேவை?"
        
        logger.info(f"Sending welcome message to session {session_id}")
        
        # Verify session is still active before proceeding
        if session_id not in manager.active_connections:
            logger.warning(f"Session {session_id} disconnected before welcome message could be sent")
            return
        
        # Add welcome message to conversation
        await manager.send_message(session_id, {
            "type": "chat_response",
            "text": welcome_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate TTS audio for welcome message with error handling
        try:
            tts = session["tts"]
            audio_data = await asyncio.to_thread(tts.synthesize, welcome_text)
            
            if audio_data is not None and len(audio_data) > 0:
                # Convert numpy array to WAV format - preserve original TTS sample rate (24kHz for Chirp3 HD)
                wav_bytes = numpy_to_wav_bytes(audio_data, sample_rate=24000)
                
                # Encode WAV as base64
                import base64
                audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
                
                # Verify session is still active before sending audio
                if session_id not in manager.active_connections:
                    logger.warning(f"Session {session_id} disconnected during TTS generation")
                    return
                
                # Send audio response
                await manager.send_message(session_id, {
                    "type": "audio_response",
                    "audio_data": audio_b64,
                    "text": welcome_text,
                    "is_welcome": True,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Welcome message sent successfully to session {session_id} (WAV size: {len(wav_bytes)} bytes)")
            else:
                logger.warning(f"Failed to generate TTS audio for welcome message in session {session_id}")
        except Exception as tts_error:
            logger.error(f"TTS error in welcome message for {session_id}: {tts_error}")
            # Continue without audio - text message was already sent
            
    except Exception as e:
        logger.error(f"Error sending welcome message to {session_id}: {e}", exc_info=True)

async def handle_audio_chunk(session_id: str, message: dict, session: dict):
    """Process incoming audio chunk with VAD"""
    try:
        # Decode audio data (base64 encoded)
        import base64
        audio_data = base64.b64decode(message["audio_data"])

        # Convert to numpy array (assuming 16-bit PCM)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # DEBUG: Save audio chunks for verification
        # Create user_audio directory if it doesn't exist
        user_audio_dir = settings.AUDIO_OUT_DIR / "user_audio"
        user_audio_dir.mkdir(parents=True, exist_ok=True)

        # Save this chunk (append to current buffer file)
        if "debug_audio_file" not in session:
            # Create new debug file for this recording session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = user_audio_dir / f"{session_id}_{timestamp}.wav"
            session["debug_audio_file"] = str(debug_file)
            session["debug_audio_chunks"] = []
            logger.info(f"🎤 DEBUG: Started recording to {debug_file}")

        # Add this chunk to debug buffer
        session["debug_audio_chunks"].append(audio_array)

        # Add to buffer
        session["audio_buffer"].extend(audio_array)
        session["last_activity"] = datetime.now()
        
        # Initialize buffer start time if not set
        if "buffer_start_time" not in session:
            session["buffer_start_time"] = datetime.now()
        
        # Voice Activity Detection
        vad = session["vad"]
        vad_result = vad.process_frame(audio_array)
        is_speech = vad_result["is_speech"]
        speech_ended = vad_result.get("speech_ended", False)
        energy = vad_result.get("energy", 0.0)
        
        # Log VAD state for debugging
        logger.debug(f"VAD: is_speech={is_speech}, speech_ended={speech_ended}, energy={energy:.4f}, buffer_size={len(session['audio_buffer'])}")
        
        # Send VAD result (convert numpy types to Python native types for JSON serialization)
        await manager.send_message(session_id, {
            "type": "vad_result",
            "is_speech": bool(is_speech),
            "confidence": float(energy),
            "speech_ended": bool(speech_ended),
            "timestamp": datetime.now().isoformat()
        })
        
        # Check for timeout-based processing (fallback if VAD doesn't detect end)
        buffer_duration = (datetime.now() - session["buffer_start_time"]).total_seconds()
        max_buffer_duration = 10.0  # Process after 10 seconds regardless of VAD
        min_buffer_duration = settings.MIN_AUDIO_DURATION  # Minimum duration before allowing stop (default 1.0s)

        # If speech ended, stop recording and process the buffer
        # BUT: Only if we have minimum duration of audio to prevent stopping on brief noise
        if speech_ended and len(session["audio_buffer"]) > 0 and buffer_duration >= min_buffer_duration:
            logger.info(f"✅ Speech ended detected for session {session_id} (buffer: {len(session['audio_buffer'])} samples, duration: {buffer_duration:.2f}s)")

            # Send stop recording message to frontend
            await manager.send_message(session_id, {
                "type": "stop_recording",
                "reason": "silence_detected",
                "timestamp": datetime.now().isoformat()
            })

            # Process the accumulated speech
            await process_speech_buffer(session_id, session)

            # Reset buffer start time
            session["buffer_start_time"] = datetime.now()

        elif speech_ended and buffer_duration < min_buffer_duration:
            # Speech ended but duration too short - keep buffering
            logger.debug(f"🔄 Speech ended but duration {buffer_duration:.2f}s < minimum {min_buffer_duration}s, continuing to buffer...")
            
        elif buffer_duration >= max_buffer_duration and len(session["audio_buffer"]) > 0:
            # Timeout fallback - process buffer even if VAD didn't detect end
            logger.warning(f"⏱️  Buffer timeout reached for session {session_id} (duration: {buffer_duration:.2f}s), forcing processing...")
            
            # Send stop recording message to frontend
            await manager.send_message(session_id, {
                "type": "stop_recording",
                "reason": "timeout",
                "timestamp": datetime.now().isoformat()
            })
            
            # Process the accumulated speech
            await process_speech_buffer(session_id, session)
            
            # Reset buffer start time
            session["buffer_start_time"] = datetime.now()
            
    except Exception as e:
        logger.error(f"❌ Error processing audio chunk: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        })

async def handle_start_speaking(session_id: str, session: dict):
    """Handle user starting to speak"""
    session["is_speaking"] = True
    session["audio_buffer"] = []
    
    await manager.send_message(session_id, {
        "type": "speaking_started",
        "timestamp": datetime.now().isoformat()
    })

async def handle_stop_speaking(session_id: str, session: dict):
    """Handle user stopping speaking"""
    session["is_speaking"] = False
    
    # Process any remaining audio in buffer
    if session["audio_buffer"]:
        await process_speech_buffer(session_id, session)
    
    await manager.send_message(session_id, {
        "type": "speaking_stopped",
        "timestamp": datetime.now().isoformat()
    })

async def handle_interrupt(session_id: str, session: dict):
    """Handle interruption of assistant speech"""
    # Note: TTS interruption would need to be implemented in the TTS class
    # For now, just signal the interruption
    
    await manager.send_message(session_id, {
        "type": "interrupted",
        "timestamp": datetime.now().isoformat()
    })

async def handle_config_update(session_id: str, message: dict, session: dict):
    """Update session configuration"""
    config = message.get("config", {})
    
    # Update VAD sensitivity
    if "vad_sensitivity" in config:
        session["vad"].silence_threshold = config["vad_sensitivity"]
    
    # Update other settings as needed
    
    await manager.send_message(session_id, {
        "type": "config_updated",
        "config": config,
        "timestamp": datetime.now().isoformat()
    })

async def process_speech_buffer(session_id: str, session: dict):
    """Process accumulated speech audio"""
    try:
        # Convert buffer to audio format for STT
        audio_array = np.array(session["audio_buffer"], dtype=np.float32)
        buffer_duration = len(audio_array) / 16000.0

        logger.info(f"🎯 Processing speech buffer for session {session_id}: {len(audio_array)} samples ({buffer_duration:.2f}s)")

        # Store debug audio file path before cleanup (for refined audio)
        original_audio_file = session.get("debug_audio_file")

        # DEBUG: Save complete audio buffer to file for verification
        if "debug_audio_file" in session and session["debug_audio_chunks"]:
            try:
                # Concatenate all chunks
                complete_audio = np.concatenate(session["debug_audio_chunks"])

                # Save as WAV file
                debug_file = session["debug_audio_file"]
                wav_bytes = numpy_to_wav_bytes(complete_audio, sample_rate=16000)

                with open(debug_file, 'wb') as f:
                    f.write(wav_bytes)

                logger.info(f"🎤 DEBUG: Saved user audio to {debug_file} ({len(wav_bytes)} bytes, {len(complete_audio)/16000:.2f}s)")

                # Clean up debug data for next recording
                session["debug_audio_chunks"] = []
                del session["debug_audio_file"]
            except Exception as debug_error:
                logger.error(f"❌ DEBUG: Failed to save audio file: {debug_error}")

        # Clear buffer
        session["audio_buffer"] = []

        # Check if buffer has enough audio
        if buffer_duration < 0.1:
            logger.warning(f"⚠️  Buffer too short ({buffer_duration:.2f}s), skipping STT")
            return

        # Prepare refined audio path if noise reduction is enabled
        refined_audio_path = None
        if settings.ENABLE_NOISE_REDUCTION and original_audio_file:
            from pathlib import Path
            try:
                # Create user_audio_refined directory
                refined_dir = settings.AUDIO_OUT_DIR / "user_audio_refined"
                refined_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Created refined audio directory: {refined_dir}")

                # Create matching filename in refined directory
                original_file = Path(original_audio_file)
                refined_audio_path = str(refined_dir / original_file.name)
                logger.info(f"📁 Refined audio will be saved to: {refined_audio_path}")
            except Exception as e:
                logger.error(f"❌ Failed to prepare refined audio path: {e}")
                refined_audio_path = None

        # Speech-to-Text
        logger.info(f"🎤 Starting STT transcription for session {session_id}...")
        stt = session["stt"]
        result = await asyncio.to_thread(
            stt.transcribe_audio_data,
            audio_array,
            16000,
            save_refined_path=refined_audio_path
        )
        transcript = result.get("text", "") if isinstance(result, dict) else ""

        # Log both file paths for comparison
        if refined_audio_path and original_audio_file:
            logger.info(f"📁 Audio pair saved for comparison:")
            logger.info(f"   Original:  {original_audio_file}")
            logger.info(f"   Refined:   {refined_audio_path}")
        
        logger.info(f"📝 STT result for session {session_id}: '{transcript}' (length: {len(transcript)})")
        
        if transcript and transcript.strip():
            logger.info(f"✅ Valid transcription received: '{transcript}'")
            
            # Send transcription result
            await manager.send_message(session_id, {
                "type": "transcription",
                "text": transcript,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate response using chat graph
            logger.info(f"🤖 Generating AI response for: '{transcript}'")
            chat_session_id = session["chat_session_id"]
            result = await asyncio.to_thread(
                process_conversation_turn, 
                chat_session_id, 
                text_input=transcript
            )
            response = result.get("assistant_text", "மன்னிக்கவும், என்னால் பதிலளிக்க முடியவில்லை.")
            
            logger.info(f"💬 AI response: '{response}'")
            
            # Send chat response
            await manager.send_message(session_id, {
                "type": "chat_response",
                "text": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate speech audio
            logger.info(f"🔊 Generating TTS audio for response...")
            tts = session["tts"]
            audio_data = await asyncio.to_thread(tts.synthesize, response)
            
            if audio_data is not None and len(audio_data) > 0:
                # Convert numpy array to WAV format - preserve original TTS sample rate (24kHz for Chirp3 HD)
                wav_bytes = numpy_to_wav_bytes(audio_data, sample_rate=24000)
                
                # Encode WAV as base64
                import base64
                audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
                
                # Send audio response
                await manager.send_message(session_id, {
                    "type": "audio_response",
                    "audio_data": audio_b64,
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Complete conversation turn finished for session {session_id} (WAV size: {len(wav_bytes)} bytes)")
                
                # 🔄 SEAMLESS CONVERSATION: Signal frontend to resume listening after a brief pause
                await asyncio.sleep(0.8)  # Brief pause to let audio finish playing
                await manager.send_message(session_id, {
                    "type": "resume_listening",
                    "message": "Ready for next input",
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"🔄 Sent resume_listening signal to session {session_id}")
            else:
                logger.warning(f"⚠️  TTS failed to generate audio for session {session_id}")
        else:
            # Empty or invalid transcription - send fallback response
            logger.warning(f"⚠️  No valid transcription received (empty or whitespace only)")
            
            # Use specific Tamil fallback message
            fallback_text = "மன்னிக்கவும், உங்கள் குரல் தெளிவாக கேட்கவில்லை. மீண்டும் சொல்லுங்கள்"
            logger.info(f"🔄 Sending fallback response: '{fallback_text}'")
            
            # Send fallback text response
            await manager.send_message(session_id, {
                "type": "chat_response",
                "text": fallback_text,
                "is_fallback": True,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate and send fallback audio response
            try:
                logger.info(f"🔊 Generating TTS audio for fallback message...")
                tts = session["tts"]
                audio_data = await asyncio.to_thread(tts.synthesize, fallback_text)
                
                if audio_data is not None and len(audio_data) > 0:
                    # Convert numpy array to WAV format - preserve original TTS sample rate (24kHz for Chirp3 HD)
                    wav_bytes = numpy_to_wav_bytes(audio_data, sample_rate=24000)
                    
                    # Encode WAV as base64
                    import base64
                    audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
                    
                    # Send audio response
                    await manager.send_message(session_id, {
                        "type": "audio_response",
                        "audio_data": audio_b64,
                        "text": fallback_text,
                        "is_fallback": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    logger.info(f"✅ Fallback response sent for session {session_id} (WAV size: {len(wav_bytes)} bytes)")
                    
                    # 🔄 Resume listening after fallback message
                    await asyncio.sleep(0.8)  # Brief pause to let audio finish playing
                    await manager.send_message(session_id, {
                        "type": "resume_listening",
                        "message": "Ready for next input after fallback",
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"🔄 Sent resume_listening signal after fallback for session {session_id}")
                else:
                    logger.warning(f"⚠️  TTS failed to generate fallback audio for session {session_id}")
                    # Still send resume signal even if TTS fails
                    await asyncio.sleep(0.5)
                    await manager.send_message(session_id, {
                        "type": "resume_listening",
                        "message": "Ready for next input",
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as fallback_error:
                logger.error(f"❌ Error generating fallback response: {fallback_error}")
                # Ensure we still resume listening even on error
                await manager.send_message(session_id, {
                    "type": "resume_listening",
                    "message": "Ready for next input",
                    "timestamp": datetime.now().isoformat()
                })
        
    except Exception as e:
        logger.error(f"❌ Error processing speech buffer for session {session_id}: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"Speech processing error: {str(e)}"
        })

# Health check for WebSocket connections
@router.get("/health")
async def websocket_health():
    """Health check for WebSocket service"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }
