"""WebSocket Audio Processor

This module handles audio processing for WebSocket connections,
including audio buffering, format conversion, and pipeline integration.
"""

import base64
import io
import wave
import logging
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List

from backend.utils.base_service import BaseService
from backend.services.media import AudioService
from backend.orchestration import conversation_orchestrator, OrchestrationMode
from backend.storage.file_manager import FileManager
from backend.services.tier_service import get_tier_for_session, get_retention_for_session


logger = logging.getLogger(__name__)


class AudioProcessor(BaseService):
    """Handles audio processing for WebSocket connections"""

    def __init__(self):
        super().__init__()
        self.service_name = "AudioProcessor"

        # Audio processing configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.max_buffer_duration = 30  # seconds
        self.silence_threshold = 0.01
        self.min_speech_duration = 0.5  # seconds

        # Initialize services
        self.audio_service = AudioService()
        self.file_manager = FileManager()

    async def process_audio_chunk(
        self,
        session_id: str,
        audio_data_b64: str,
        session: Dict[str, Any],
        manager
    ) -> None:
        """Process incoming audio chunk and add to speech buffer"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_b64)

            # Convert to numpy array
            audio_array = self._bytes_to_numpy(audio_bytes)

            # Add to speech buffer
            if "speech_buffer" not in session:
                session["speech_buffer"] = []

            session["speech_buffer"].append(audio_array)

            # Update session activity
            session["last_audio_time"] = datetime.now().isoformat()

            # Check buffer size and duration
            await self._check_buffer_limits(session_id, session, manager)

            self.logger.debug(
                f"Added audio chunk to buffer for session {session_id} "
                f"(buffer size: {len(session['speech_buffer'])} chunks)"
            )

        except Exception as e:
            self.logger.error(f"Error processing audio chunk for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Audio processing error: {str(e)}")

    async def process_complete_speech(
        self,
        session_id: str,
        session: Dict[str, Any],
        manager
    ) -> None:
        """Process complete speech buffer through conversation pipeline"""
        try:
            speech_buffer = session.get("speech_buffer", [])

            if not speech_buffer:
                self.logger.info(f"No speech buffer to process for session {session_id}")
                return

            # Concatenate all audio chunks
            complete_audio = np.concatenate(speech_buffer)

            # Validate audio quality
            if not self._validate_audio_quality(complete_audio):
                await manager.send_message(session_id, {
                    "type": "audio_quality_warning",
                    "message": "Audio quality may be poor",
                    "timestamp": datetime.now().isoformat()
                })

            # Save audio to temporary file
            audio_path = await self._save_audio_temporarily(complete_audio, session_id)

            if not audio_path:
                await manager.send_error(session_id, "Failed to save audio for processing")
                return

            # Clear the speech buffer
            session["speech_buffer"] = []

            # Set processing flag
            session["is_processing"] = True

            # Notify client that processing started
            await manager.send_message(session_id, {
                "type": "processing_started",
                "timestamp": datetime.now().isoformat()
            })

            # Process through conversation pipeline
            await self._process_through_pipeline(session_id, audio_path, session, manager)

        except Exception as e:
            self.logger.error(f"Error processing complete speech for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Speech processing error: {str(e)}")
        finally:
            # Clear processing flag
            session["is_processing"] = False

    async def _check_buffer_limits(
        self,
        session_id: str,
        session: Dict[str, Any],
        manager
    ) -> None:
        """Check if speech buffer exceeds limits and handle accordingly"""
        speech_buffer = session.get("speech_buffer", [])

        if not speech_buffer:
            return

        # Calculate total duration
        total_samples = sum(len(chunk) for chunk in speech_buffer)
        duration_seconds = total_samples / self.sample_rate

        if duration_seconds > self.max_buffer_duration:
            self.logger.warning(
                f"Speech buffer exceeded max duration ({duration_seconds:.2f}s) for session {session_id}"
            )

            # Auto-process the buffer to prevent overflow
            await self.process_complete_speech(session_id, session, manager)

            await manager.send_message(session_id, {
                "type": "buffer_overflow",
                "message": f"Speech buffer processed automatically (duration: {duration_seconds:.2f}s)",
                "timestamp": datetime.now().isoformat()
            })

    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        try:
            # Assume 16-bit PCM audio
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            # Normalize to float32 [-1, 1]
            return audio_array.astype(np.float32) / 32768.0

        except Exception as e:
            self.logger.error(f"Error converting audio bytes to numpy: {str(e)}")
            # Return empty array as fallback
            return np.array([], dtype=np.float32)

    def _numpy_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int = None) -> bytes:
        """Convert numpy array to WAV bytes"""
        if sample_rate is None:
            sample_rate = self.sample_rate

        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            return wav_buffer.getvalue()

        except Exception as e:
            self.logger.error(f"Error converting numpy to WAV bytes: {str(e)}")
            return b''

    def _validate_audio_quality(self, audio_data: np.ndarray) -> bool:
        """Basic audio quality validation"""
        try:
            # Check if audio is not silent
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < self.silence_threshold:
                return False

            # Check duration
            duration = len(audio_data) / self.sample_rate
            if duration < self.min_speech_duration:
                return False

            # Check for clipping
            clipping_ratio = np.sum(np.abs(audio_data) > 0.95) / len(audio_data)
            if clipping_ratio > 0.1:  # More than 10% clipped
                self.logger.warning("High clipping detected in audio")

            return True

        except Exception as e:
            self.logger.error(f"Error validating audio quality: {str(e)}")
            return True  # Default to valid

    async def _save_audio_temporarily(self, audio_data: np.ndarray, session_id: str) -> Optional[str]:
        """Save audio to temporary file for processing"""
        try:
            # Convert to WAV bytes
            wav_bytes = self._numpy_to_wav_bytes(audio_data)

            if not wav_bytes:
                return None

            # Generate temporary filename
            timestamp = int(datetime.now().timestamp() * 1000)
            filename = f"ws_audio_{session_id}_{timestamp}.wav"

            # Upload to MinIO temporarily
            audio_file = io.BytesIO(wav_bytes)

            # Get user tier for metadata
            try:
                user_tier = await get_tier_for_session(session_id)
                retention_hours = await get_retention_for_session(session_id)
            except Exception:
                user_tier = "free"
                retention_hours = 1  # Short retention for WebSocket audio

            metadata = {
                "session_id": session_id,
                "content_type": "audio/wav",
                "source": "websocket_input",
                "user_tier": user_tier,
                "retention_hours": retention_hours,
                "temporary": True
            }

            # Upload to storage
            object_key = await self.file_manager.upload_file(
                file=audio_file,
                filename=filename,
                content_type="audio/wav",
                metadata=metadata
            )

            if object_key:
                # Return file path for pipeline processing
                return f"{self.file_manager.bucket_name}/{object_key}"

            return None

        except Exception as e:
            self.logger.error(f"Error saving audio temporarily for session {session_id}: {str(e)}")
            return None

    async def _process_through_pipeline(
        self,
        session_id: str,
        audio_path: str,
        session: Dict[str, Any],
        manager
    ) -> None:
        """Process audio through conversation pipeline"""
        try:
            # Get session configuration
            config = session.get("config", {})
            language = config.get("language", "ta")
            rag_enabled = config.get("rag_enabled", True)

            # Determine pipeline mode based on configuration
            if rag_enabled:
                mode = OrchestrationMode.FULL
            else:
                mode = OrchestrationMode.FULL_NO_RAG

            # Process through conversation orchestrator
            result = await conversation_orchestrator.execute_conversation_turn(
                session_id=session_id,
                audio_input_path=audio_path,
                language=language,
                rag_enabled=rag_enabled,
                mode=mode
            )

            # Handle pipeline result
            if result["success"]:
                await self._handle_successful_processing(session_id, result, session, manager)
            else:
                await self._handle_failed_processing(session_id, result, session, manager)

        except Exception as e:
            self.logger.error(f"Error in pipeline processing for session {session_id}: {str(e)}")
            await manager.send_error(session_id, f"Pipeline processing failed: {str(e)}")

    async def _handle_successful_processing(
        self,
        session_id: str,
        result: Dict[str, Any],
        session: Dict[str, Any],
        manager
    ) -> None:
        """Handle successful pipeline processing result"""
        try:
            outputs = result["outputs"]

            # Send transcription result
            if outputs.get("user_text"):
                await manager.send_message(session_id, {
                    "type": "transcription",
                    "text": outputs["user_text"],
                    "timestamp": datetime.now().isoformat()
                })

            # Send assistant response
            if outputs.get("assistant_text"):
                response_message = {
                    "type": "assistant_message",
                    "text": outputs["assistant_text"],
                    "timestamp": datetime.now().isoformat(),
                    "execution_id": result.get("execution_id"),
                    "execution_time_ms": result.get("execution_time_ms")
                }

                # Add audio URL if available
                if outputs.get("audio_output_path"):
                    response_message["audio_url"] = outputs["audio_output_path"]

                # Add retrieved documents if any
                if outputs.get("retrieved_documents"):
                    response_message["sources"] = len(outputs["retrieved_documents"])

                await manager.send_message(session_id, response_message)

            # Send processing completion notification
            await manager.send_message(session_id, {
                "type": "processing_completed",
                "execution_time_ms": result.get("execution_time_ms"),
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling successful processing for session {session_id}: {str(e)}")

    async def _handle_failed_processing(
        self,
        session_id: str,
        result: Dict[str, Any],
        session: Dict[str, Any],
        manager
    ) -> None:
        """Handle failed pipeline processing result"""
        try:
            error_message = result.get("error", "Processing failed")

            await manager.send_message(session_id, {
                "type": "processing_error",
                "error": error_message,
                "execution_id": result.get("execution_id"),
                "stage_results": result.get("stage_results", {}),
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling failed processing for session {session_id}: {str(e)}")

    def get_processor_status(self) -> Dict[str, Any]:
        """Get audio processor status and configuration"""
        return {
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "max_buffer_duration": self.max_buffer_duration,
            "silence_threshold": self.silence_threshold,
            "min_speech_duration": self.min_speech_duration,
            "audio_service_loaded": self.audio_service is not None,
            "file_manager_loaded": self.file_manager is not None
        }

    def configure_processor(
        self,
        sample_rate: Optional[int] = None,
        chunk_size: Optional[int] = None,
        max_buffer_duration: Optional[float] = None,
        silence_threshold: Optional[float] = None,
        min_speech_duration: Optional[float] = None
    ) -> None:
        """Configure audio processor parameters"""
        if sample_rate is not None:
            self.sample_rate = sample_rate

        if chunk_size is not None:
            self.chunk_size = chunk_size

        if max_buffer_duration is not None:
            self.max_buffer_duration = max_buffer_duration

        if silence_threshold is not None:
            self.silence_threshold = silence_threshold

        if min_speech_duration is not None:
            self.min_speech_duration = min_speech_duration

        self.logger.info(
            f"Audio processor configured: "
            f"sample_rate={self.sample_rate}, "
            f"chunk_size={self.chunk_size}, "
            f"max_buffer={self.max_buffer_duration}s"
        )