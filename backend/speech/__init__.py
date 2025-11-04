"""
Speech processing module for Tamil AI Voice Assistant

This module provides:
- Speech-to-Text (STT) using Faster-Whisper
- Text-to-Speech (TTS) using Google TTS (Female Voice)
- Voice Activity Detection (VAD)
- Audio utilities for processing
"""

from .stt import (
    FasterWhisperSTT,
    get_stt_engine,
    initialize_stt,
    transcribe_audio,
)

from .tts import (
    GoogleTTS,
    get_tts_engine,
    initialize_tts,
    synthesize_speech,
)

from .vad import (
    VoiceActivityDetector,
    get_vad,
    detect_speech_segments,
)

from .audio_utils import (
    load_audio,
    save_audio,
    convert_audio_format,
    get_audio_duration,
    normalize_audio,
)

__all__ = [
    # STT
    "FasterWhisperSTT",
    "get_stt_engine",
    "initialize_stt",
    "transcribe_audio",
    # TTS
    "GoogleTTS",
    "get_tts_engine",
    "initialize_tts",
    "synthesize_speech",
    # VAD
    "VoiceActivityDetector",
    "get_vad",
    "detect_speech_segments",
    # Audio utilities
    "load_audio",
    "save_audio",
    "convert_audio_format",
    "get_audio_duration",
    "normalize_audio",
]
