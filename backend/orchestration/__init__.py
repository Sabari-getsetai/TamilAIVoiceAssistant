"""
Orchestration Package - High-Level Service Coordination

This package contains orchestration logic that coordinates multiple services
to fulfill complex business workflows. Designed for microservice architecture.

Modules:
- conversation_orchestrator: Main conversation flow coordination
- pipelines: Modular conversation processing stages
  - base_pipeline: Base interface and shared components
  - stt_stage: Speech-to-Text processing
  - rag_stage: Retrieval-Augmented Generation
  - llm_stage: Large Language Model response generation
  - tts_stage: Text-to-Speech synthesis
  - history_stage: Conversation history management
"""

from .conversation_orchestrator import (
    ConversationOrchestrator,
    OrchestrationMode,
    conversation_orchestrator,
    process_conversation_turn_async,
    process_conversation_turn
)

from .pipelines import (
    BasePipelineStage,
    PipelineStageType,
    PipelineStageResult,
    ConversationState,
    PipelineStageError,
    create_conversation_state,
    STTStage,
    RAGStage,
    LLMStage,
    TTSStage,
    HistoryStage
)

__all__ = [
    # Orchestrator
    "ConversationOrchestrator",
    "OrchestrationMode",
    "conversation_orchestrator",
    "process_conversation_turn_async",
    "process_conversation_turn",

    # Pipeline components
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