"""Chat session and conversation request/response schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class SessionCreateRequest(BaseModel):
    """Request to create a new chat session"""
    user_id: Optional[str] = None
    language: str = Field(default="ta", description="Language code (ta, en)")
    rag_enabled: bool = Field(default=True, description="Enable RAG retrieval")


class SessionResponse(BaseModel):
    """Response with session information"""
    session_id: str
    user_id: Optional[str]
    language: str
    rag_enabled: bool
    created_at: str
    last_activity: Optional[str] = None
    total_turns: int
    session_duration: Optional[float] = None
    status: str


class ConversationTurnResponse(BaseModel):
    """Response for a conversation turn"""
    success: bool
    session_id: str
    user_text: str
    assistant_text: str
    audio_output_url: Optional[str] = None
    processing_time: Dict[str, float]
    total_time: float
    error: Optional[str] = None


class TextConversationRequest(BaseModel):
    """Request for text-only conversation"""
    text: str
    language: str = "ta"


class TextConversationResponse(BaseModel):
    """Response for text-only conversation"""
    success: bool
    session_id: str
    user_text: str
    assistant_text: str
    processing_time: Dict[str, float]
    total_time: float
    error: Optional[str] = None


class TranscribeResponse(BaseModel):
    """Response for transcription"""
    success: bool
    text: str
    language: str
    confidence: Optional[float] = None
    duration: float


class SynthesizeRequest(BaseModel):
    """Request for speech synthesis"""
    text: str
    language: str = "ta"


class SynthesizeResponse(BaseModel):
    """Response for speech synthesis"""
    success: bool
    audio_url: str
    duration: float
    text_length: int


class GenerateRequest(BaseModel):
    """Request for text generation"""
    text: str
    language: str = "ta"
    use_rag: bool = True


class GenerateResponse(BaseModel):
    """Response for text generation"""
    success: bool
    response_text: str
    context_used: bool
    retrieved_chunks: int
    duration: float


class ConversationHistoryResponse(BaseModel):
    """Response with conversation history"""
    session_id: str
    total_turns: int
    history: List[Dict]


class SessionStatsResponse(BaseModel):
    """Response with session statistics"""
    total_sessions: int
    active_sessions: int
    total_turns: int
    average_session_duration: float
    average_turn_time: float