"""WebSocket Message Handlers

This module contains specialized handlers for different WebSocket message types,
providing a clean separation of concerns for the real-time voice conversation system.
"""

import json
import logging
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import WebSocket

from backend.utils.base_service import BaseService
from backend.orchestration import conversation_orchestrator, OrchestrationMode
from backend.websocket.audio_processor import AudioProcessor


logger = logging.getLogger(__name__)


class BaseMessageHandler(BaseService):
    """Base class for WebSocket message handlers"""

    def __init__(self, handler_type: str):
        super().__init__()
        self.service_name = f"MessageHandler_{handler_type}"
        self.handler_type = handler_type

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle the message - to be implemented by subclasses"""
        raise NotImplementedError


class AudioChunkHandler(BaseMessageHandler):
    """Handler for audio chunk messages"""

    def __init__(self):
        super().__init__("audio_chunk")
        self.audio_processor = AudioProcessor()

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle incoming audio chunk data"""
        try:
            # Validate message format
            if "audio_data" not in message:
                await manager.send_error(session_id, "Missing audio_data in audio_chunk message")
                return

            # Extract audio data (base64 encoded)
            audio_data_b64 = message["audio_data"]

            # Process the audio chunk
            await self.audio_processor.process_audio_chunk(
                session_id=session_id,
                audio_data_b64=audio_data_b64,
                session=session,
                manager=manager
            )

            self.logger.debug(f"Processed audio chunk for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error handling audio chunk for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Failed to process audio chunk: {str(e)}")


class StartSpeakingHandler(BaseMessageHandler):
    """Handler for start speaking events"""

    def __init__(self):
        super().__init__("start_speaking")

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle start speaking notification"""
        try:
            self.logger.info(f"User started speaking in session {session_id}")

            # Clear any existing speech buffer
            session["speech_buffer"] = []
            session["is_speaking"] = True
            session["speech_start_time"] = datetime.now().isoformat()

            # Stop any currently playing assistant speech
            session["interrupt_playback"] = True

            # Send acknowledgment
            await manager.send_message(session_id, {
                "type": "speaking_started",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling start speaking for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Failed to handle start speaking: {str(e)}")


class StopSpeakingHandler(BaseMessageHandler):
    """Handler for stop speaking events"""

    def __init__(self):
        super().__init__("stop_speaking")
        self.audio_processor = AudioProcessor()

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle stop speaking notification and process accumulated speech"""
        try:
            self.logger.info(f"User stopped speaking in session {session_id}")

            session["is_speaking"] = False
            session["speech_end_time"] = datetime.now().isoformat()

            # Send acknowledgment
            await manager.send_message(session_id, {
                "type": "speaking_stopped",
                "timestamp": datetime.now().isoformat()
            })

            # Process the complete speech buffer
            if session.get("speech_buffer"):
                await self.audio_processor.process_complete_speech(
                    session_id=session_id,
                    session=session,
                    manager=manager
                )
            else:
                self.logger.info(f"No speech buffer to process for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error handling stop speaking for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Failed to handle stop speaking: {str(e)}")


class InterruptHandler(BaseMessageHandler):
    """Handler for interrupt events"""

    def __init__(self):
        super().__init__("interrupt")

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle interrupt request to stop assistant speech"""
        try:
            self.logger.info(f"Interrupt requested for session {session_id}")

            # Set interrupt flag
            session["interrupt_playback"] = True

            # Clear any ongoing speech processing
            session["is_processing"] = False

            # Send confirmation
            await manager.send_message(session_id, {
                "type": "interrupted",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling interrupt for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Failed to handle interrupt: {str(e)}")


class ConfigUpdateHandler(BaseMessageHandler):
    """Handler for configuration update messages"""

    def __init__(self):
        super().__init__("config_update")

    async def handle(self, session_id: str, message: Dict[str, Any], session: Dict[str, Any], manager) -> None:
        """Handle configuration updates"""
        try:
            config_updates = message.get("config", {})

            if not config_updates:
                await manager.send_error(session_id, "No config data provided in config_update message")
                return

            self.logger.info(f"Updating config for session {session_id}: {config_updates}")

            # Update session configuration
            if "config" not in session:
                session["config"] = {}

            # Apply updates
            for key, value in config_updates.items():
                if self._is_valid_config_key(key):
                    session["config"][key] = value
                    self.logger.debug(f"Updated config {key} = {value} for session {session_id}")
                else:
                    self.logger.warning(f"Invalid config key '{key}' ignored for session {session_id}")

            # Send confirmation
            await manager.send_message(session_id, {
                "type": "config_updated",
                "config": session["config"],
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling config update for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Failed to handle config update: {str(e)}")

    def _is_valid_config_key(self, key: str) -> bool:
        """Validate configuration keys"""
        valid_keys = {
            "language", "voice", "speaking_rate", "pitch", "volume",
            "rag_enabled", "max_history_turns", "auto_interrupt",
            "silence_threshold", "speech_timeout"
        }
        return key in valid_keys


class WelcomeMessageHandler(BaseMessageHandler):
    """Handler for sending welcome messages"""

    def __init__(self):
        super().__init__("welcome_message")

    async def send_welcome_message(self, session_id: str, session: Dict[str, Any], manager) -> None:
        """Send welcome message to new session"""
        try:
            # Get user's language preference
            language = session.get("config", {}).get("language", "ta")

            # Prepare welcome messages in different languages
            welcome_messages = {
                "ta": "வணக்கம்! நான் உங்கள் Tamil AI குரல் உதவியாளர். நீங்கள் எப்படி இருக்கிறீர்கள்?",
                "en": "Hello! I'm your Tamil AI voice assistant. How are you today?",
                "hi": "नमस्ते! मैं आपका Tamil AI आवाज सहायक हूँ। आप कैसे हैं?"
            }

            welcome_text = welcome_messages.get(language, welcome_messages["ta"])

            # Use conversation orchestrator to generate welcome audio
            try:
                result = await conversation_orchestrator.execute_conversation_turn(
                    session_id=session_id,
                    text_input=welcome_text,
                    mode=OrchestrationMode.AUDIO_GENERATION,
                    language=language
                )

                if result["success"] and result["outputs"]["audio_output_path"]:
                    # Send welcome message with audio
                    await manager.send_message(session_id, {
                        "type": "assistant_message",
                        "text": welcome_text,
                        "audio_url": result["outputs"]["audio_output_path"],
                        "timestamp": datetime.now().isoformat(),
                        "is_welcome": True
                    })
                else:
                    # Fallback to text-only welcome
                    await manager.send_message(session_id, {
                        "type": "assistant_message",
                        "text": welcome_text,
                        "timestamp": datetime.now().isoformat(),
                        "is_welcome": True,
                        "error": "Audio generation failed"
                    })

            except Exception as e:
                self.logger.error(f"Failed to generate welcome audio for session {session_id}: {str(e)}")
                # Send text-only welcome as fallback
                await manager.send_message(session_id, {
                    "type": "assistant_message",
                    "text": welcome_text,
                    "timestamp": datetime.now().isoformat(),
                    "is_welcome": True,
                    "error": "Welcome audio unavailable"
                })

        except Exception as e:
            self.logger.error(f"Error sending welcome message for session {session_id}: {str(e)}")


class MessageHandlerRegistry:
    """Registry for managing message handlers"""

    def __init__(self):
        self.handlers = {}
        self.welcome_handler = WelcomeMessageHandler()
        self._register_handlers()

    def _register_handlers(self):
        """Register all message handlers"""
        self.handlers = {
            "audio_chunk": AudioChunkHandler(),
            "start_speaking": StartSpeakingHandler(),
            "stop_speaking": StopSpeakingHandler(),
            "interrupt": InterruptHandler(),
            "config_update": ConfigUpdateHandler()
        }

    async def handle_message(
        self,
        message_type: str,
        session_id: str,
        message: Dict[str, Any],
        session: Dict[str, Any],
        manager
    ) -> bool:
        """
        Handle a message using the appropriate handler

        Returns:
            True if message was handled successfully, False otherwise
        """
        if message_type not in self.handlers:
            logger.warning(f"Unknown message type '{message_type}' for session {session_id}")
            await manager.send_error(session_id, f"Unknown message type: {message_type}")
            return False

        try:
            handler = self.handlers[message_type]
            await handler.handle(session_id, message, session, manager)
            return True

        except Exception as e:
            logger.error(f"Handler error for message type '{message_type}' in session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Handler error: {str(e)}")
            return False

    async def send_welcome_message(self, session_id: str, session: Dict[str, Any], manager) -> None:
        """Send welcome message using the welcome handler"""
        await self.welcome_handler.send_welcome_message(session_id, session, manager)

    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about registered handlers"""
        return {
            "registered_handlers": list(self.handlers.keys()),
            "handler_details": {
                name: {
                    "handler_type": handler.handler_type,
                    "service_name": handler.service_name
                }
                for name, handler in self.handlers.items()
            },
            "welcome_handler": {
                "handler_type": self.welcome_handler.handler_type,
                "service_name": self.welcome_handler.service_name
            }
        }


# Global handler registry instance
message_handler_registry = MessageHandlerRegistry()