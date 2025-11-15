"""Manages WebSocket connections for real-time voice chat."""
import json
from typing import Dict
from datetime import datetime
from fastapi.websockets import WebSocket
from backend.speech.stt import FasterWhisperSTT
from backend.speech.tts import get_tts_engine, initialize_tts
from backend.speech.vad import VoiceActivityDetector
from backend.services.session_service import get_session_manager
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, dict] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection"""

        # Validate session using comprehensive validation method
        try:
            session_manager = await get_session_manager()

            # Use comprehensive session validation
            validation_result = await session_manager.validate_session_access(session_id)

            if not validation_result["valid"]:
                error_msg = validation_result.get("error", "Session validation failed")
                logger.error(f"Session validation failed for {session_id}: {error_msg}")

                if "not found" in error_msg:
                    await websocket.close(code=4004, reason="Session not found. Please create a session first.")
                elif "not active" in error_msg:
                    await websocket.close(code=4005, reason="Session expired or inactive.")
                else:
                    await websocket.close(code=4000, reason="Session validation failed")
                return

            logger.info(f"Session validation successful: {session_id}")
            chat_session_id = session_id

        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            await websocket.close(code=4000, reason="Session validation failed")
            return

        # Accept connection after validation
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
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


# Global connection manager instance
manager = ConnectionManager()

__all__ = ["ConnectionManager", "manager"]
