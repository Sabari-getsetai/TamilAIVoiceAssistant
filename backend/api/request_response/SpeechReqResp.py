"""Speech request and response models."""

from pydantic import BaseModel
from typing import Optional

class STTResponse(BaseModel):
    """Speech-to-Text response"""
    text: str
    confidence: Optional[float] = None


class TTSRequest(BaseModel):
    """Text-to-Speech request"""
    text: str
    language: str = "ta"


class TTSResponse(BaseModel):
    """Text-to-Speech response"""
    audio_url: str