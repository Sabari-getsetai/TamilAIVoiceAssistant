"""TTS (Text-to-Speech) Pipeline Stage

This module handles the conversion of assistant text to speech audio,
with support for multiple languages and voice configurations.
"""

import os
import io
import wave
import uuid
import time
from typing import Optional, Dict, Any
from pathlib import Path
import numpy as np

from backend.orchestration.pipelines.base_pipeline import (
    BasePipelineStage, PipelineStageType, ConversationState, PipelineStageError
)
from backend.speech import initialize_tts, synthesize_speech, get_tts_engine
from backend.storage.file_manager import FileManager
from backend.services.tier_service import get_tier_for_session, get_retention_for_session


class TTSStage(BasePipelineStage):
    """TTS (Text-to-Speech) pipeline stage"""

    def __init__(self):
        super().__init__(
            stage_type=PipelineStageType.TTS,
            stage_name="tts"
        )

        # Configure stage requirements
        self.required_inputs = ["assistant_text", "session_id"]
        self.provided_outputs = ["audio_output", "audio_output_path"]

        # TTS configuration
        self.voice_name = "ta-IN-PallaviNeural"  # Default Tamil voice
        self.speaking_rate = 1.0
        self.pitch = 0
        self.volume = 100
        self.audio_format = "wav"
        self.sample_rate = 24000  # Google Cloud TTS Chirp3 HD sample rate

        # Initialize components
        self.tts_initialized = False
        self.file_manager = FileManager()

    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process assistant text through TTS to generate audio output

        Args:
            state: Current conversation state

        Returns:
            Updated state with audio_output and audio_output_path

        Raises:
            PipelineStageError: If TTS processing fails
        """
        try:
            # Get assistant text
            assistant_text = state["assistant_text"]
            if not assistant_text or not assistant_text.strip():
                self.logger.info("Empty assistant text, skipping TTS generation")
                state["audio_output"] = None
                state["audio_output_path"] = None
                return state

            # Initialize TTS engine if needed
            if not self.tts_initialized:
                await self._initialize_tts()

            # Get language and voice configuration
            language = state.get("language", "ta")
            voice_config = self._get_voice_config_for_language(language)

            # Generate speech audio
            audio_data = await self._synthesize_speech(assistant_text, voice_config)

            # Convert audio to bytes
            audio_bytes = self._convert_audio_to_bytes(audio_data)

            # Upload audio to storage (MinIO)
            audio_path = await self._upload_audio_to_storage(
                audio_bytes, state["session_id"], state.get("user_id")
            )

            # Update state with TTS results
            state["audio_output"] = audio_bytes
            state["audio_output_path"] = audio_path

            # Add TTS metadata to custom context
            if "custom_context" not in state:
                state["custom_context"] = {}

            state["custom_context"]["tts_metadata"] = {
                "text": assistant_text,
                "text_length": len(assistant_text),
                "voice_name": voice_config.get("voice_name"),
                "language": language,
                "audio_duration_seconds": len(audio_data) / self.sample_rate if isinstance(audio_data, np.ndarray) else None,
                "audio_size_bytes": len(audio_bytes),
                "audio_path": audio_path,
                "engine": self._get_engine_name()
            }

            self.logger.info(
                f"TTS completed: Generated {len(audio_bytes)} bytes of audio "
                f"from {len(assistant_text)} characters of text"
            )

            return state

        except Exception as e:
            self.logger.error(f"TTS processing failed: {str(e)}")
            raise PipelineStageError(
                self.stage_name,
                f"TTS synthesis failed: {str(e)}",
                cause=e
            )

    async def _initialize_tts(self) -> None:
        """Initialize TTS engine if needed"""
        try:
            if not self.tts_initialized:
                self.logger.info("Initializing TTS engine")
                if not initialize_tts():
                    raise ValueError("Failed to initialize TTS engine")

                self.tts_initialized = True
                self.logger.info(f"TTS initialized: {self._get_engine_name()}")

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to initialize TTS: {str(e)}",
                cause=e
            )

    def _get_voice_config_for_language(self, language: str) -> Dict[str, Any]:
        """Get voice configuration for the specified language"""
        voice_configs = {
            "ta": {
                "voice_name": "ta-IN-PallaviNeural",
                "language_code": "ta-IN"
            },
            "en": {
                "voice_name": "en-US-JennyMultilingualNeural",
                "language_code": "en-US"
            },
            "hi": {
                "voice_name": "hi-IN-SwaraNeural",
                "language_code": "hi-IN"
            },
            "te": {
                "voice_name": "te-IN-ShrutiNeural",
                "language_code": "te-IN"
            },
            "ml": {
                "voice_name": "ml-IN-SobhanaNeural",
                "language_code": "ml-IN"
            },
            "kn": {
                "voice_name": "kn-IN-SapnaNeural",
                "language_code": "kn-IN"
            }
        }

        config = voice_configs.get(language, voice_configs["ta"])  # Default to Tamil

        # Override with instance configuration
        config.update({
            "speaking_rate": self.speaking_rate,
            "pitch": self.pitch,
            "volume": self.volume
        })

        return config

    async def _synthesize_speech(self, text: str, voice_config: Dict[str, Any]) -> np.ndarray:
        """Synthesize speech using TTS engine"""
        try:
            # Use the synthesize_speech function from the speech module
            audio_data = synthesize_speech(
                text=text,
                language=voice_config.get("language_code", "ta-IN"),
                voice=voice_config.get("voice_name")
            )

            if audio_data is None:
                raise ValueError("TTS synthesis returned no audio data")

            # Ensure we have a numpy array
            if not isinstance(audio_data, np.ndarray):
                # Try to convert to numpy array
                audio_data = np.array(audio_data, dtype=np.float32)

            return audio_data

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Speech synthesis failed: {str(e)}",
                cause=e
            )

    def _convert_audio_to_bytes(self, audio_data: np.ndarray) -> bytes:
        """Convert audio numpy array to WAV bytes"""
        try:
            # Convert float32 to int16 PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            wav_bytes = wav_buffer.getvalue()
            wav_buffer.close()

            return wav_bytes

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Audio conversion failed: {str(e)}",
                cause=e
            )

    async def _upload_audio_to_storage(
        self,
        audio_bytes: bytes,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Upload TTS audio to MinIO storage"""
        try:
            # Generate filename
            timestamp = int(time.time() * 1000)  # milliseconds
            audio_id = str(uuid.uuid4())[:8]
            filename = f"tts_{session_id}_{audio_id}_{timestamp}.wav"

            # Get user tier and retention info
            try:
                user_tier = await get_tier_for_session(session_id)
                retention_hours = await get_retention_for_session(session_id)
            except Exception as e:
                self.logger.warning(f"Failed to get tier info: {e}")
                user_tier = "free"
                retention_hours = 24

            # Create tier-based metadata
            tier_metadata = {
                "user_tier": user_tier,
                "retention_hours": retention_hours,
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "content_type": "audio/wav",
                "generated_by": "tts_pipeline"
            }

            # Create file-like object
            audio_file = io.BytesIO(audio_bytes)

            # Upload to MinIO
            object_key = await self.file_manager.upload_file(
                file=audio_file,
                filename=filename,
                content_type="audio/wav",
                metadata=tier_metadata
            )

            self.logger.info(f"Audio uploaded to storage: {object_key}")
            return object_key

        except Exception as e:
            self.logger.error(f"Audio upload failed: {str(e)}")
            # Don't fail the entire pipeline for upload issues
            return None

    def _get_engine_name(self) -> str:
        """Get the name of the current TTS engine"""
        try:
            engine = get_tts_engine()
            if engine and hasattr(engine, '__class__'):
                return engine.__class__.__name__
            else:
                return "Unknown"
        except Exception:
            return "Unknown"

    def configure_tts(
        self,
        voice_name: Optional[str] = None,
        speaking_rate: Optional[float] = None,
        pitch: Optional[int] = None,
        volume: Optional[int] = None,
        sample_rate: Optional[int] = None
    ) -> None:
        """
        Configure TTS synthesis parameters

        Args:
            voice_name: TTS voice to use
            speaking_rate: Speaking rate (0.5 to 2.0)
            pitch: Voice pitch adjustment (-50 to +50)
            volume: Voice volume (0 to 100)
            sample_rate: Audio sample rate
        """
        if voice_name is not None:
            self.voice_name = voice_name

        if speaking_rate is not None:
            self.speaking_rate = max(0.5, min(2.0, speaking_rate))

        if pitch is not None:
            self.pitch = max(-50, min(50, pitch))

        if volume is not None:
            self.volume = max(0, min(100, volume))

        if sample_rate is not None:
            self.sample_rate = sample_rate

        self.logger.info(
            f"TTS configuration updated: "
            f"voice={self.voice_name}, "
            f"rate={self.speaking_rate}, "
            f"pitch={self.pitch}, "
            f"volume={self.volume}, "
            f"sample_rate={self.sample_rate}"
        )

    def health_check(self) -> bool:
        """Check if TTS engine is healthy"""
        try:
            if not self.tts_initialized:
                return False

            engine = get_tts_engine()
            return engine is not None

        except Exception as e:
            self.logger.error(f"TTS health check failed: {e}")
            return False

    def get_available_voices(self, language: Optional[str] = None) -> list[Dict[str, str]]:
        """Get list of available voices"""
        all_voices = [
            {"language": "ta", "voice_name": "ta-IN-PallaviNeural", "gender": "female"},
            {"language": "ta", "voice_name": "ta-IN-ValluvarNeural", "gender": "male"},
            {"language": "en", "voice_name": "en-US-JennyMultilingualNeural", "gender": "female"},
            {"language": "en", "voice_name": "en-US-RyanMultilingualNeural", "gender": "male"},
            {"language": "hi", "voice_name": "hi-IN-SwaraNeural", "gender": "female"},
            {"language": "hi", "voice_name": "hi-IN-MadhurNeural", "gender": "male"},
            {"language": "te", "voice_name": "te-IN-ShrutiNeural", "gender": "female"},
            {"language": "te", "voice_name": "te-IN-MohanNeural", "gender": "male"},
            {"language": "ml", "voice_name": "ml-IN-SobhanaNeural", "gender": "female"},
            {"language": "ml", "voice_name": "ml-IN-MidhunNeural", "gender": "male"},
            {"language": "kn", "voice_name": "kn-IN-SapnaNeural", "gender": "female"},
            {"language": "kn", "voice_name": "kn-IN-GaganNeural", "gender": "male"},
        ]

        if language:
            return [voice for voice in all_voices if voice["language"] == language]

        return all_voices

    def get_tts_status(self) -> Dict[str, Any]:
        """Get current TTS configuration and status"""
        return {
            "engine_name": self._get_engine_name(),
            "initialized": self.tts_initialized,
            "health": self.health_check(),
            "configuration": {
                "voice_name": self.voice_name,
                "speaking_rate": self.speaking_rate,
                "pitch": self.pitch,
                "volume": self.volume,
                "sample_rate": self.sample_rate,
                "audio_format": self.audio_format
            },
            "available_voices_count": len(self.get_available_voices())
        }

    async def validate_text_for_synthesis(self, text: str, language: str = "ta") -> tuple[bool, str]:
        """
        Validate text before TTS synthesis

        Args:
            text: Text to validate
            language: Target language

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Empty text provided"

        # Check text length
        max_length = 5000  # Most TTS services have character limits
        if len(text) > max_length:
            return False, f"Text too long ({len(text)} chars, max {max_length})"

        # Check for unsupported characters (basic validation)
        # This could be expanded based on TTS engine capabilities
        if language == "ta":
            # Basic Tamil text validation
            import re
            tamil_pattern = re.compile(r'[\u0B80-\u0BFF\s\w\.,!?;:\-\'\"()]')
            if not all(tamil_pattern.match(char) for char in text):
                return False, "Text contains unsupported characters for Tamil TTS"

        return True, "Text validation passed"