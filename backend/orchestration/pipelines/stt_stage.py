"""Speech-to-Text Pipeline Stage

This module handles the conversion of audio input to text using the configured
STT engine, with proper error handling and performance monitoring.
"""

from typing import Optional
from pathlib import Path

from backend.orchestration.pipelines.base_pipeline import (
    BasePipelineStage, PipelineStageType, ConversationState, PipelineStageError
)
from backend.speech import initialize_stt, transcribe_audio, get_stt_engine


class STTStage(BasePipelineStage):
    """Speech-to-Text pipeline stage"""

    def __init__(self):
        super().__init__(
            stage_type=PipelineStageType.STT,
            stage_name="stt"
        )

        # Configure stage requirements
        self.required_inputs = ["audio_input_path"]  # Either audio_input_path or audio_input
        self.provided_outputs = ["user_text"]

        # STT configuration
        self.stt_initialized = False

    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process audio input through STT to generate user text

        Args:
            state: Current conversation state

        Returns:
            Updated state with user_text populated

        Raises:
            PipelineStageError: If STT processing fails
        """
        try:
            # Check if we have audio input
            if not state.get("audio_input_path") and not state.get("audio_input"):
                raise PipelineStageError(
                    self.stage_name,
                    "No audio input provided (neither audio_input_path nor audio_input)"
                )

            # Initialize STT engine if needed
            if not self.stt_initialized:
                self.logger.info("Initializing STT engine")
                if not initialize_stt():
                    raise PipelineStageError(
                        self.stage_name,
                        "Failed to initialize STT engine"
                    )
                self.stt_initialized = True

            # Get language for transcription
            language = state.get("language", "ta")

            # Transcribe audio
            user_text = ""
            transcription_method = ""

            if state.get("audio_input_path"):
                # Transcribe from file path
                audio_path = state["audio_input_path"]
                self.logger.info(f"Transcribing from file: {audio_path}")

                # Validate file exists
                if not Path(audio_path).exists():
                    raise PipelineStageError(
                        self.stage_name,
                        f"Audio file not found: {audio_path}"
                    )

                user_text = transcribe_audio(audio_path, language=language)
                transcription_method = "file_path"

            elif state.get("audio_input"):
                # Transcribe from audio bytes
                audio_bytes = state["audio_input"]
                self.logger.info(f"Transcribing from audio bytes ({len(audio_bytes)} bytes)")

                # For audio bytes, we need to save temporarily and then transcribe
                # This could be improved by adding direct bytes support to STT engine
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_bytes)
                    temp_path = temp_file.name

                try:
                    user_text = transcribe_audio(temp_path, language=language)
                    transcription_method = "audio_bytes"
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up temp file {temp_path}: {e}")

            # Validate transcription result
            if not user_text or not user_text.strip():
                # Empty transcription - this might be silence or unclear audio
                self.logger.warning("STT returned empty transcription")
                user_text = ""  # Ensure it's an empty string, not None

            # Update state
            state["user_text"] = user_text.strip()

            # Add STT metadata to custom context
            if "custom_context" not in state:
                state["custom_context"] = {}

            state["custom_context"]["stt_metadata"] = {
                "transcription_method": transcription_method,
                "language": language,
                "original_text_length": len(user_text),
                "engine": get_stt_engine().__class__.__name__ if get_stt_engine() else "Unknown"
            }

            self.logger.info(
                f"STT completed: '{user_text[:100]}{'...' if len(user_text) > 100 else ''}' "
                f"({len(user_text)} characters)"
            )

            return state

        except PipelineStageError:
            # Re-raise pipeline stage errors
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in STT stage: {str(e)}")
            raise PipelineStageError(
                self.stage_name,
                f"STT processing failed: {str(e)}",
                cause=e
            )

    def health_check(self) -> bool:
        """Check if STT engine is healthy"""
        try:
            # Initialize if needed
            if not self.stt_initialized:
                if not initialize_stt():
                    return False
                self.stt_initialized = True

            # Check if engine is available
            engine = get_stt_engine()
            return engine is not None

        except Exception as e:
            self.logger.error(f"STT health check failed: {e}")
            return False

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages for STT"""
        try:
            # This would depend on the specific STT engine implementation
            # For now, return the common languages we support
            return ["ta", "en", "hi", "te", "ml", "kn"]
        except Exception:
            return ["ta", "en"]  # Fallback to basic support

    def get_engine_info(self) -> dict:
        """Get information about the current STT engine"""
        try:
            engine = get_stt_engine()
            if not engine:
                return {"engine": "Not initialized", "status": "unavailable"}

            return {
                "engine": engine.__class__.__name__,
                "status": "ready" if self.stt_initialized else "not_initialized",
                "supported_languages": self.get_supported_languages(),
                "health": self.health_check()
            }
        except Exception as e:
            return {
                "engine": "Unknown",
                "status": "error",
                "error": str(e)
            }

    async def validate_audio_input(self, state: ConversationState) -> tuple[bool, str]:
        """
        Validate audio input before processing

        Args:
            state: Current conversation state

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if we have any audio input
            has_file_path = bool(state.get("audio_input_path"))
            has_audio_bytes = bool(state.get("audio_input"))

            if not has_file_path and not has_audio_bytes:
                return False, "No audio input provided"

            # Validate file path if provided
            if has_file_path:
                audio_path = Path(state["audio_input_path"])
                if not audio_path.exists():
                    return False, f"Audio file not found: {audio_path}"

                if not audio_path.is_file():
                    return False, f"Audio path is not a file: {audio_path}"

                # Check file size (basic validation)
                file_size = audio_path.stat().st_size
                if file_size == 0:
                    return False, "Audio file is empty"

                # Check file extension
                allowed_extensions = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
                if audio_path.suffix.lower() not in allowed_extensions:
                    return False, f"Unsupported audio format: {audio_path.suffix}"

            # Validate audio bytes if provided
            if has_audio_bytes:
                audio_bytes = state["audio_input"]
                if len(audio_bytes) == 0:
                    return False, "Audio bytes are empty"

                # Basic audio validation - check if it looks like audio data
                if len(audio_bytes) < 44:  # Minimum WAV header size
                    return False, "Audio data too short to be valid audio"

            return True, "Audio input validation passed"

        except Exception as e:
            return False, f"Audio validation error: {str(e)}"

    def configure_stt(
        self,
        language: Optional[str] = None,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False
    ) -> None:
        """
        Configure STT engine settings

        Args:
            language: Primary language for recognition
            enable_automatic_punctuation: Whether to enable automatic punctuation
            enable_word_time_offsets: Whether to return word-level timestamps
        """
        # This would configure the STT engine if it supports runtime configuration
        # Implementation depends on specific STT engine capabilities
        self.logger.info(
            f"STT configuration updated: "
            f"language={language}, "
            f"punctuation={enable_automatic_punctuation}, "
            f"timestamps={enable_word_time_offsets}"
        )

        # Store configuration in service for future use
        if not hasattr(self, 'stt_config'):
            self.stt_config = {}

        self.stt_config.update({
            "language": language,
            "enable_automatic_punctuation": enable_automatic_punctuation,
            "enable_word_time_offsets": enable_word_time_offsets
        })