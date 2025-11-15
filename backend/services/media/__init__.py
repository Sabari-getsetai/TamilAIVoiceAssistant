"""
Media Service Module - Audio Processing and Speech

This module handles all audio and speech processing concerns,
designed to be microservice-ready.

Services:
- audio_service: Audio file lifecycle, processing, storage
- speech_service: STT/TTS coordination, speech pipeline
- voice_service: Voice activity detection, audio streaming
"""

from .audio_service import AudioService

__all__ = [
    "AudioService"
]