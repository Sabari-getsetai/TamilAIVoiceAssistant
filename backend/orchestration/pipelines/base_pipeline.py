"""Base Pipeline Interface for Conversation Processing

This module defines the base interface for conversation pipeline stages,
enabling modular, testable, and microservice-ready conversation processing.

Each pipeline stage processes a conversation state and passes it to the next stage,
with proper error handling, metrics collection, and async support.
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypedDict
from datetime import datetime
from enum import Enum
import logging

from backend.utils.base_service import BaseService


class PipelineStageType(Enum):
    """Types of pipeline stages"""
    STT = "stt"           # Speech-to-Text
    RAG = "rag"           # Retrieval-Augmented Generation
    LLM = "llm"           # Large Language Model
    TTS = "tts"           # Text-to-Speech
    HISTORY = "history"   # History Management
    VALIDATION = "validation"
    ROUTING = "routing"


class ConversationState(TypedDict, total=False):
    """
    Enhanced conversation state schema for pipeline processing

    This replaces the original ChatState with better typing and extensibility
    """

    # Session management
    session_id: str
    user_id: Optional[str]
    organization_id: Optional[str]
    created_at: datetime
    last_activity: datetime

    # Current turn input/output
    audio_input: Optional[bytes]
    audio_input_path: Optional[str]
    user_text: str
    assistant_text: str
    audio_output: Optional[bytes]
    audio_output_path: Optional[str]

    # Conversation history
    conversation_history: List[Dict[str, Any]]

    # RAG context
    retrieved_documents: List[Dict[str, Any]]
    context_used: str
    rag_enabled: bool

    # Processing status
    current_stage: str
    completed_stages: List[str]
    error_message: Optional[str]
    stage_metrics: Dict[str, Dict[str, Any]]

    # Configuration
    language: str
    max_history_turns: int

    # Metadata
    total_turns: int
    session_duration: float
    pipeline_id: str

    # Additional context for extensibility
    custom_context: Dict[str, Any]


class PipelineStageResult(TypedDict):
    """Result from a pipeline stage execution"""
    success: bool
    state: ConversationState
    error_message: Optional[str]
    execution_time_ms: float
    metrics: Dict[str, Any]
    stage_type: PipelineStageType


class BasePipelineStage(BaseService, ABC):
    """Base class for all conversation pipeline stages"""

    def __init__(self, stage_type: PipelineStageType, stage_name: Optional[str] = None):
        super().__init__()
        self.stage_type = stage_type
        self.stage_name = stage_name or stage_type.value
        self.service_name = f"PipelineStage_{self.stage_name}"

        # Stage configuration
        self.timeout_seconds = 30
        self.retry_attempts = 0
        self.required_inputs: List[str] = []
        self.provided_outputs: List[str] = []

        # Metrics collection
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0

    @abstractmethod
    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through this pipeline stage

        Args:
            state: Current conversation state

        Returns:
            Updated conversation state

        Raises:
            PipelineStageError: If processing fails
        """
        pass

    async def execute(self, state: ConversationState) -> PipelineStageResult:
        """
        Execute the pipeline stage with error handling and metrics collection

        Args:
            state: Current conversation state

        Returns:
            PipelineStageResult with execution details
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())[:8]

        self.logger.info(
            f"Starting pipeline stage {self.stage_name} "
            f"for session {state.get('session_id', 'unknown')} "
            f"(execution_id: {execution_id})"
        )

        # Initialize stage metrics in state if not present
        if 'stage_metrics' not in state:
            state['stage_metrics'] = {}

        state['stage_metrics'][self.stage_name] = {
            'start_time': start_time,
            'execution_id': execution_id
        }

        try:
            # Validate inputs
            self._validate_inputs(state)

            # Update state tracking
            state['current_stage'] = self.stage_name
            if 'completed_stages' not in state:
                state['completed_stages'] = []

            # Process the state
            updated_state = await self.process(state)

            # Validate outputs
            self._validate_outputs(updated_state)

            # Update completion tracking
            updated_state['completed_stages'].append(self.stage_name)

            # Calculate execution time
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000

            # Update metrics
            self.execution_count += 1
            self.total_execution_time += execution_time

            # Update stage metrics in state
            updated_state['stage_metrics'][self.stage_name].update({
                'end_time': time.time(),
                'execution_time_ms': execution_time_ms,
                'success': True,
                'error_message': None
            })

            self.logger.info(
                f"Pipeline stage {self.stage_name} completed successfully "
                f"in {execution_time_ms:.2f}ms "
                f"(execution_id: {execution_id})"
            )

            return PipelineStageResult(
                success=True,
                state=updated_state,
                error_message=None,
                execution_time_ms=execution_time_ms,
                metrics=self.get_stage_metrics(),
                stage_type=self.stage_type
            )

        except Exception as e:
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000

            self.error_count += 1
            error_message = f"Pipeline stage {self.stage_name} failed: {str(e)}"

            # Update stage metrics in state
            state['stage_metrics'][self.stage_name].update({
                'end_time': time.time(),
                'execution_time_ms': execution_time_ms,
                'success': False,
                'error_message': error_message
            })

            state['error_message'] = error_message

            self.logger.error(
                f"Pipeline stage {self.stage_name} failed "
                f"after {execution_time_ms:.2f}ms: {str(e)} "
                f"(execution_id: {execution_id})"
            )

            return PipelineStageResult(
                success=False,
                state=state,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                metrics=self.get_stage_metrics(),
                stage_type=self.stage_type
            )

    def _validate_inputs(self, state: ConversationState) -> None:
        """Validate that required inputs are present in state"""
        missing_inputs = []

        for required_input in self.required_inputs:
            if required_input not in state or state[required_input] is None:
                missing_inputs.append(required_input)

        if missing_inputs:
            raise ValueError(
                f"Missing required inputs for {self.stage_name}: {missing_inputs}"
            )

    def _validate_outputs(self, state: ConversationState) -> None:
        """Validate that expected outputs are present in state"""
        missing_outputs = []

        for provided_output in self.provided_outputs:
            if provided_output not in state or state[provided_output] is None:
                missing_outputs.append(provided_output)

        if missing_outputs:
            self.logger.warning(
                f"Pipeline stage {self.stage_name} did not provide expected outputs: {missing_outputs}"
            )

    def get_stage_metrics(self) -> Dict[str, Any]:
        """Get metrics for this pipeline stage"""
        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0 else 0
        )

        return {
            'stage_name': self.stage_name,
            'stage_type': self.stage_type.value,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'success_rate': (
                (self.execution_count - self.error_count) / self.execution_count
                if self.execution_count > 0 else 0
            ),
            'avg_execution_time_ms': avg_execution_time * 1000,
            'total_execution_time_ms': self.total_execution_time * 1000
        }

    def reset_metrics(self) -> None:
        """Reset stage metrics"""
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0
        self.logger.info(f"Reset metrics for pipeline stage {self.stage_name}")

    def configure(
        self,
        timeout_seconds: Optional[int] = None,
        retry_attempts: Optional[int] = None,
        required_inputs: Optional[List[str]] = None,
        provided_outputs: Optional[List[str]] = None
    ) -> None:
        """Configure the pipeline stage"""
        if timeout_seconds is not None:
            self.timeout_seconds = timeout_seconds

        if retry_attempts is not None:
            self.retry_attempts = retry_attempts

        if required_inputs is not None:
            self.required_inputs = required_inputs

        if provided_outputs is not None:
            self.provided_outputs = provided_outputs

        self.logger.info(f"Configured pipeline stage {self.stage_name}")


class PipelineStageError(Exception):
    """Exception raised by pipeline stages"""

    def __init__(self, stage_name: str, message: str, cause: Optional[Exception] = None):
        self.stage_name = stage_name
        self.cause = cause
        super().__init__(f"Pipeline stage {stage_name}: {message}")


def create_conversation_state(
    session_id: str,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    language: str = "ta",
    rag_enabled: bool = True,
    **kwargs
) -> ConversationState:
    """Create a new conversation state for pipeline processing"""

    current_time = datetime.utcnow()
    pipeline_id = str(uuid.uuid4())

    state = ConversationState(
        session_id=session_id,
        user_id=user_id,
        organization_id=organization_id,
        created_at=current_time,
        last_activity=current_time,

        # Initialize empty values
        user_text="",
        assistant_text="",
        conversation_history=[],
        retrieved_documents=[],
        context_used="",
        rag_enabled=rag_enabled,

        # Processing state
        current_stage="",
        completed_stages=[],
        stage_metrics={},

        # Configuration
        language=language,
        max_history_turns=20,

        # Metadata
        total_turns=0,
        session_duration=0.0,
        pipeline_id=pipeline_id,

        # Custom context
        custom_context={}
    )

    # Add any additional keyword arguments
    for key, value in kwargs.items():
        if key not in state:
            state[key] = value

    return state