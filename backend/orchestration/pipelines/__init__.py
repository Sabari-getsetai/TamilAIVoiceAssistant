"""
Pipeline Components Package

This package contains modular pipeline stages for conversation processing,
replacing the monolithic LangGraph implementation with microservice-ready
components.

Pipeline Stages:
- base_pipeline: Base interface and shared components
- stt_stage: Speech-to-Text processing
- rag_stage: Retrieval-Augmented Generation
- llm_stage: Large Language Model response generation
- tts_stage: Text-to-Speech synthesis
- history_stage: Conversation history management
"""

from .base_pipeline import (
    BasePipelineStage,
    PipelineStageType,
    PipelineStageResult,
    ConversationState,
    PipelineStageError,
    create_conversation_state
)
from .stt_stage import STTStage
from .rag_stage import RAGStage
from .llm_stage import LLMStage
from .tts_stage import TTSStage
from .history_stage import HistoryStage

__all__ = [
    # Base pipeline components
    "BasePipelineStage",
    "PipelineStageType",
    "PipelineStageResult",
    "ConversationState",
    "PipelineStageError",
    "create_conversation_state",

    # Pipeline stages
    "STTStage",
    "RAGStage",
    "LLMStage",
    "TTSStage",
    "HistoryStage"
]