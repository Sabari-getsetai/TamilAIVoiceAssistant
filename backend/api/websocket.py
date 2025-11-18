"""
WebSocket API for Real-time Voice Conversation
"""
import asyncio
import json
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import numpy as np
from datetime import datetime
import io
import wave


from backend.graphs.chat_graph import process_conversation_turn_async
from backend.storage.file_manager import FileManager

from backend.settings import settings
from backend.services.tier_service import get_tier_for_session, get_retention_for_session

from backend.websocket.ConnectionManager import manager as connection_manager


logger = logging.getLogger(__name__)


manager = connection_manager
router = APIRouter(prefix="/ws", tags=["websocket"])



# Initialize FileManager for MinIO uploads
file_manager = FileManager()

async def upload_audio_to_minio(
    audio_data: np.ndarray,
    filename: str,
    session_id: str,
    audio_type: str,  # 'input', 'output', 'refined'
    sample_rate: int = 16000,
    user_id: str = "anonymous"  # Default for anonymous sessions
) -> Optional[str]:
    """
    Upload audio data to MinIO and return the object key.

    Args:
        audio_data: Audio data as numpy array
        filename: Filename for the audio file
        session_id: Session identifier
        audio_type: Type of audio ('input', 'output', 'refined')
        sample_rate: Audio sample rate
        user_id: User identifier (default 'anonymous')

    Returns:
        MinIO object key if successful, None if failed
    """
    try:
        # Detect user tier for retention policy
        user_tier = await get_tier_for_session(session_id)
        retention_hours = await get_retention_for_session(session_id)

        # Convert audio data to WAV bytes
        wav_bytes = numpy_to_wav_bytes(audio_data, sample_rate)
        duration = len(audio_data) / sample_rate

        # Create BytesIO object for file upload
        audio_file = io.BytesIO(wav_bytes)

        # Add tier-based metadata
        tier_metadata = {
            "user_tier": user_tier,
            "retention_hours": str(retention_hours),
            "retention_policy": f"{retention_hours}h_from_upload"
        }

        # Upload to MinIO
        result = await file_manager.upload_audio(
            user_id=user_id,
            filename=filename,
            file_data=audio_file,
            audio_type=audio_type,
            session_id=session_id,
            duration=duration,
            sample_rate=sample_rate,
            metadata=tier_metadata
        )

        if result.get("success"):
            object_key = result.get("object_key")
            logger.info(f"✅ Audio uploaded to MinIO: {object_key} (size: {len(wav_bytes)} bytes, {duration:.2f}s)")

            # Save local debug copy if enabled
            if settings.ENABLE_LOCAL_AUDIO_DEBUG:
                debug_dir = settings.AUDIO_OUT_DIR / f"debug_{audio_type}"
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_file = debug_dir / filename

                with open(debug_file, 'wb') as f:
                    f.write(wav_bytes)
                logger.info(f"🐛 DEBUG: Local copy saved to {debug_file}")

            return object_key
        else:
            logger.error(f"❌ Failed to upload audio to MinIO: {result.get('errors', 'Unknown error')}")
            return None

    except Exception as e:
        logger.error(f"❌ Error uploading audio to MinIO: {e}")
        return None

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
    try:
        await manager.connect(websocket, session_id)

        # Check if connection was successful (session exists in manager)
        if session_id not in manager.session_data:
            logger.error(f"Session {session_id} not found in manager after connection attempt")
            return

        session = manager.session_data[session_id]
        
        # Retrieve user_id from session for audio uploads
        from backend.services.session_service import get_session_manager
        session_manager = await get_session_manager()
        session_info = await session_manager.get_session(session_id)
        session_user_id = session_info.get("user_id", "anonymous") if session_info else "anonymous"
        session["user_id"] = session_user_id  # Store in session for later use
        
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for session {session_id}: {e}")
        return
    
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

        # Prepare for MinIO upload - collect audio chunks
        if "audio_chunks_for_upload" not in session:
            # Initialize for new recording session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session["current_audio_filename"] = f"{session_id}_{timestamp}.wav"
            session["audio_chunks_for_upload"] = []
            logger.info(f"🎤 Started collecting audio chunks for MinIO upload")

        # Add this chunk to upload buffer
        session["audio_chunks_for_upload"].append(audio_array)

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

        # Upload user input audio to MinIO
        user_audio_minio_key = None
        if "audio_chunks_for_upload" in session and session["audio_chunks_for_upload"]:
            try:
                # Concatenate all chunks for upload
                complete_audio = np.concatenate(session["audio_chunks_for_upload"])
                filename = session.get("current_audio_filename", f"{session_id}_audio.wav")

                # Upload to MinIO
                user_audio_minio_key = await upload_audio_to_minio(
                    audio_data=complete_audio,
                    filename=filename,
                    session_id=session_id,
                    audio_type="input",
                    sample_rate=16000,
                    user_id=session.get("user_id", "anonymous")
                )

                if user_audio_minio_key:
                    logger.info(f"📁 User audio uploaded to MinIO: {user_audio_minio_key}")
                else:
                    logger.warning(f"⚠️  Failed to upload user audio to MinIO")

                # Clean up upload data for next recording
                session["audio_chunks_for_upload"] = []
                if "current_audio_filename" in session:
                    del session["current_audio_filename"]

            except Exception as upload_error:
                logger.error(f"❌ Error uploading user audio to MinIO: {upload_error}")

        # Clear buffer
        session["audio_buffer"] = []

        # Check if buffer has enough audio
        if buffer_duration < 0.1:
            logger.warning(f"⚠️  Buffer too short ({buffer_duration:.2f}s), skipping STT")
            return

        # Prepare for refined audio MinIO upload if noise reduction is enabled
        refined_audio_filename = None
        if settings.ENABLE_NOISE_REDUCTION and user_audio_minio_key:
            try:
                # Generate filename for refined audio based on original
                original_filename = session.get("current_audio_filename", f"{session_id}_audio.wav")
                base_name = original_filename.replace(".wav", "")
                refined_audio_filename = f"{base_name}_refined.wav"
                logger.info(f"📁 Prepared filename for refined audio: {refined_audio_filename}")
            except Exception as e:
                logger.error(f"❌ Failed to prepare refined audio filename: {e}")
                refined_audio_filename = None

        # Speech-to-Text (without local file saving)
        logger.info(f"🎤 Starting STT transcription for session {session_id}...")
        stt = session["stt"]
        result = await asyncio.to_thread(
            stt.transcribe_audio_data,
            audio_array,
            16000
        )
        transcript = result.get("text", "") if isinstance(result, dict) else ""

        # Upload refined audio to MinIO if available and noise reduction enabled
        refined_audio_minio_key = None
        if settings.ENABLE_NOISE_REDUCTION and refined_audio_filename and isinstance(result, dict):
            refined_audio_data = result.get("refined_audio")
            if refined_audio_data is not None and len(refined_audio_data) > 0:
                try:
                    refined_audio_minio_key = await upload_audio_to_minio(
                        audio_data=refined_audio_data,
                        filename=refined_audio_filename,
                        session_id=session_id,
                        audio_type="refined",
                        sample_rate=16000,
                        user_id=session.get("user_id", "anonymous")
                    )

                    if refined_audio_minio_key:
                        logger.info(f"📁 Refined audio uploaded to MinIO: {refined_audio_minio_key}")
                    else:
                        logger.warning(f"⚠️  Failed to upload refined audio to MinIO")
                except Exception as refined_upload_error:
                    logger.error(f"❌ Error uploading refined audio to MinIO: {refined_upload_error}")

        # Log both MinIO keys for comparison
        if user_audio_minio_key and refined_audio_minio_key:
            logger.info(f"📁 Audio pair uploaded to MinIO:")
            logger.info(f"   Original:  {user_audio_minio_key}")
            logger.info(f"   Refined:   {refined_audio_minio_key}")
        elif user_audio_minio_key:
            logger.info(f"📁 Original audio uploaded to MinIO: {user_audio_minio_key}")
        
        logger.info(f"📝 STT result for session {session_id}: '{transcript}' (length: {len(transcript)})")
        
        if transcript and transcript.strip():
            logger.info(f"✅ Valid transcription received: '{transcript}'")
            
            # Send transcription result
            await manager.send_message(session_id, {
                "type": "transcription",
                "text": transcript,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate response using chat graph with database persistence
            logger.info(f"🤖 Generating AI response for: '{transcript}'")
            chat_session_id = session["chat_session_id"]
            result = await process_conversation_turn_async(
                session_id=chat_session_id, 
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
