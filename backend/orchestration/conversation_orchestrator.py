"""Conversation Orchestrator - Modular Pipeline Execution Engine

This module replaces the monolithic LangGraph implementation with a
flexible, microservice-ready pipeline orchestrator that coordinates
the conversation processing stages.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from backend.utils.base_service import BaseService
from backend.orchestration.pipelines.base_pipeline import (
    ConversationState, PipelineStageResult, PipelineStageType,
    create_conversation_state
)
from backend.orchestration.pipelines.stt_stage import STTStage
from backend.orchestration.pipelines.rag_stage import RAGStage
from backend.orchestration.pipelines.llm_stage import LLMStage
from backend.orchestration.pipelines.tts_stage import TTSStage
from backend.orchestration.pipelines.history_stage import HistoryStage


class OrchestrationMode(Enum):
    """Pipeline execution modes"""
    FULL = "full"                    # Complete pipeline: STT → RAG → LLM → TTS → History
    FULL_NO_RAG = "full_no_rag"      # Skip RAG: STT → LLM → TTS → History
    TEXT_ONLY = "text_only"          # No audio: RAG → LLM → History
    TEXT_NO_RAG = "text_no_rag"      # Text without RAG: LLM → History
    AUDIO_GENERATION = "audio_gen"   # Text to audio: TTS → History
    TRANSCRIPTION = "transcription"  # Audio to text: STT only
    CUSTOM = "custom"                # Custom pipeline sequence


class ConversationOrchestrator(BaseService):
    """
    Orchestrator for conversation pipeline execution

    Coordinates multiple pipeline stages in a flexible, configurable manner
    with proper error handling, metrics collection, and conditional routing.
    """

    def __init__(self):
        super().__init__()
        self.service_name = "ConversationOrchestrator"

        # Pipeline stages
        self.stt_stage = STTStage()
        self.rag_stage = RAGStage()
        self.llm_stage = LLMStage()
        self.tts_stage = TTSStage()
        self.history_stage = HistoryStage()

        # Orchestration configuration
        self.default_mode = OrchestrationMode.FULL
        self.continue_on_stage_failure = False
        self.parallel_execution_enabled = False

        # Metrics
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.successful_executions = 0
        self.failed_executions = 0

    async def execute_conversation_turn(
        self,
        session_id: str,
        mode: Optional[OrchestrationMode] = None,
        audio_input_path: Optional[str] = None,
        audio_input: Optional[bytes] = None,
        text_input: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        language: str = "ta",
        rag_enabled: bool = True,
        custom_stages: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a complete conversation turn through the pipeline

        Args:
            session_id: Session identifier
            mode: Pipeline execution mode
            audio_input_path: Path to audio input file
            audio_input: Audio input as bytes
            text_input: Direct text input (bypasses STT)
            user_id: User identifier
            organization_id: Organization identifier
            language: Language code
            rag_enabled: Whether to use RAG
            custom_stages: Custom stage sequence for CUSTOM mode
            **kwargs: Additional configuration

        Returns:
            Dictionary with execution results and state
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())[:8]

        self.logger.info(
            f"Starting conversation turn execution "
            f"(session: {session_id}, mode: {mode or self.default_mode}, "
            f"execution_id: {execution_id})"
        )

        try:
            # Initialize conversation state
            state = create_conversation_state(
                session_id=session_id,
                user_id=user_id,
                organization_id=organization_id,
                language=language,
                rag_enabled=rag_enabled,
                **kwargs
            )

            # Set input data based on available inputs
            if audio_input_path:
                state["audio_input_path"] = audio_input_path
            if audio_input:
                state["audio_input"] = audio_input
            if text_input:
                state["user_text"] = text_input

            # Determine execution mode
            execution_mode = mode or self.default_mode
            if execution_mode == OrchestrationMode.CUSTOM and custom_stages:
                pipeline_sequence = custom_stages
            else:
                pipeline_sequence = self._get_pipeline_sequence(execution_mode, state)

            # Execute pipeline stages
            execution_results = await self._execute_pipeline_sequence(
                state, pipeline_sequence, execution_id
            )

            # Calculate total execution time
            total_time = time.time() - start_time
            self.execution_count += 1
            self.total_execution_time += total_time

            # Determine overall success
            all_successful = all(
                result.get("success", False) for result in execution_results.values()
            )

            if all_successful:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            # Build response
            response = {
                "success": all_successful,
                "execution_id": execution_id,
                "session_id": session_id,
                "execution_time_ms": total_time * 1000,
                "mode": execution_mode.value,
                "pipeline_sequence": pipeline_sequence,
                "stage_results": execution_results,
                "final_state": state,
                "outputs": {
                    "user_text": state.get("user_text", ""),
                    "assistant_text": state.get("assistant_text", ""),
                    "audio_output_path": state.get("audio_output_path"),
                    "conversation_history": state.get("conversation_history", []),
                    "retrieved_documents": state.get("retrieved_documents", [])
                }
            }

            self.logger.info(
                f"Conversation turn completed: "
                f"{'SUCCESS' if all_successful else 'PARTIAL_FAILURE'} "
                f"in {total_time * 1000:.2f}ms "
                f"(execution_id: {execution_id})"
            )

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_executions += 1

            error_message = f"Conversation orchestration failed: {str(e)}"
            self.logger.error(f"{error_message} (execution_id: {execution_id})")

            return {
                "success": False,
                "execution_id": execution_id,
                "session_id": session_id,
                "execution_time_ms": execution_time * 1000,
                "error": error_message,
                "stage_results": {},
                "final_state": {},
                "outputs": {}
            }

    def _get_pipeline_sequence(
        self,
        mode: OrchestrationMode,
        state: ConversationState
    ) -> List[str]:
        """Get pipeline sequence based on execution mode"""

        # Determine if we need STT based on inputs
        needs_stt = bool(
            state.get("audio_input_path") or state.get("audio_input")
        ) and not state.get("user_text")

        # Determine if RAG should be used
        use_rag = state.get("rag_enabled", True) and mode not in [
            OrchestrationMode.FULL_NO_RAG,
            OrchestrationMode.TEXT_NO_RAG
        ]

        # Define sequences for each mode
        sequences = {
            OrchestrationMode.FULL: {
                True: ["stt", "rag", "llm", "tts", "history"],    # with STT
                False: ["rag", "llm", "tts", "history"]           # without STT
            },
            OrchestrationMode.FULL_NO_RAG: {
                True: ["stt", "llm", "tts", "history"],           # with STT
                False: ["llm", "tts", "history"]                  # without STT
            },
            OrchestrationMode.TEXT_ONLY: {
                True: ["stt", "rag", "llm", "history"] if use_rag else ["stt", "llm", "history"],
                False: ["rag", "llm", "history"] if use_rag else ["llm", "history"]
            },
            OrchestrationMode.TEXT_NO_RAG: {
                True: ["stt", "llm", "history"],                  # with STT
                False: ["llm", "history"]                         # without STT
            },
            OrchestrationMode.AUDIO_GENERATION: {
                True: ["tts", "history"],                         # assumes text already available
                False: ["tts", "history"]
            },
            OrchestrationMode.TRANSCRIPTION: {
                True: ["stt"],                                    # STT only
                False: []                                         # no stages needed
            }
        }

        sequence = sequences.get(mode, sequences[OrchestrationMode.FULL])
        return sequence.get(needs_stt, sequence[False])

    async def _execute_pipeline_sequence(
        self,
        state: ConversationState,
        pipeline_sequence: List[str],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute the pipeline stages in sequence"""

        stage_mapping = {
            "stt": self.stt_stage,
            "rag": self.rag_stage,
            "llm": self.llm_stage,
            "tts": self.tts_stage,
            "history": self.history_stage
        }

        execution_results = {}

        for stage_name in pipeline_sequence:
            if stage_name not in stage_mapping:
                self.logger.warning(f"Unknown stage '{stage_name}' in sequence, skipping")
                continue

            stage = stage_mapping[stage_name]

            try:
                self.logger.debug(f"Executing stage: {stage_name} (execution_id: {execution_id})")

                # Execute stage
                stage_result = await stage.execute(state)
                execution_results[stage_name] = {
                    "success": stage_result.success,
                    "execution_time_ms": stage_result.execution_time_ms,
                    "error_message": stage_result.error_message,
                    "stage_type": stage_result.stage_type.value
                }

                # Update state with stage result
                state = stage_result.state

                # Handle stage failure
                if not stage_result.success:
                    self.logger.error(
                        f"Stage {stage_name} failed: {stage_result.error_message} "
                        f"(execution_id: {execution_id})"
                    )

                    if not self.continue_on_stage_failure:
                        self.logger.info(f"Stopping pipeline execution due to stage failure")
                        break
                    else:
                        self.logger.info(f"Continuing pipeline despite stage failure")

            except Exception as e:
                error_message = f"Unexpected error in stage {stage_name}: {str(e)}"
                self.logger.error(f"{error_message} (execution_id: {execution_id})")

                execution_results[stage_name] = {
                    "success": False,
                    "execution_time_ms": 0,
                    "error_message": error_message,
                    "stage_type": stage_name
                }

                if not self.continue_on_stage_failure:
                    break

        return execution_results

    async def process_conversation_turn_async(
        self,
        session_id: str,
        audio_input_path: Optional[str] = None,
        text_input: Optional[str] = None,
        language: str = "ta",
        db=None  # Backward compatibility parameter
    ) -> Dict[str, Any]:
        """
        Backward compatible async conversation processing

        This method maintains compatibility with the original chat_graph.py interface
        """
        return await self.execute_conversation_turn(
            session_id=session_id,
            audio_input_path=audio_input_path,
            text_input=text_input,
            language=language,
            mode=OrchestrationMode.FULL
        )

    def process_conversation_turn(
        self,
        session_id: str,
        audio_input_path: Optional[str] = None,
        text_input: Optional[str] = None,
        language: str = "ta",
        db=None  # Backward compatibility parameter
    ) -> Dict[str, Any]:
        """
        Backward compatible sync conversation processing

        This method maintains compatibility with the original chat_graph.py interface
        """
        import asyncio

        # Run async method in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.execute_conversation_turn(
                session_id=session_id,
                audio_input_path=audio_input_path,
                text_input=text_input,
                language=language,
                mode=OrchestrationMode.FULL
            )
        )

    def configure_orchestrator(
        self,
        default_mode: Optional[OrchestrationMode] = None,
        continue_on_stage_failure: Optional[bool] = None,
        parallel_execution_enabled: Optional[bool] = None
    ) -> None:
        """Configure orchestrator behavior"""

        if default_mode is not None:
            self.default_mode = default_mode

        if continue_on_stage_failure is not None:
            self.continue_on_stage_failure = continue_on_stage_failure

        if parallel_execution_enabled is not None:
            self.parallel_execution_enabled = parallel_execution_enabled

        self.logger.info(
            f"Orchestrator configured: "
            f"mode={self.default_mode.value}, "
            f"continue_on_failure={self.continue_on_stage_failure}, "
            f"parallel={self.parallel_execution_enabled}"
        )

    def configure_stages(
        self,
        stt_config: Optional[Dict[str, Any]] = None,
        rag_config: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        tts_config: Optional[Dict[str, Any]] = None,
        history_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Configure individual pipeline stages"""

        if stt_config:
            self.stt_stage.configure_stt(**stt_config)

        if rag_config:
            self.rag_stage.configure_rag(**rag_config)

        if llm_config:
            self.llm_stage.configure_llm(**llm_config)

        if tts_config:
            self.tts_stage.configure_tts(**tts_config)

        if history_config:
            self.history_stage.configure_history(**history_config)

        self.logger.info("Pipeline stages configured")

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status"""

        stage_statuses = {
            "stt": {
                "health": self.stt_stage.health_check(),
                "metrics": self.stt_stage.get_stage_metrics()
            },
            "rag": {
                "status": self.rag_stage.get_rag_status(),
                "metrics": self.rag_stage.get_stage_metrics()
            },
            "llm": {
                "info": self.llm_stage.get_model_info(),
                "metrics": self.llm_stage.get_stage_metrics()
            },
            "tts": {
                "status": self.tts_stage.get_tts_status(),
                "metrics": self.tts_stage.get_stage_metrics()
            },
            "history": {
                "status": self.history_stage.get_history_status(),
                "metrics": self.history_stage.get_stage_metrics()
            }
        }

        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0 else 0
        )

        return {
            "orchestrator": {
                "default_mode": self.default_mode.value,
                "continue_on_stage_failure": self.continue_on_stage_failure,
                "parallel_execution_enabled": self.parallel_execution_enabled
            },
            "metrics": {
                "execution_count": self.execution_count,
                "successful_executions": self.successful_executions,
                "failed_executions": self.failed_executions,
                "success_rate": (
                    self.successful_executions / self.execution_count
                    if self.execution_count > 0 else 0
                ),
                "avg_execution_time_ms": avg_execution_time * 1000,
                "total_execution_time_ms": self.total_execution_time * 1000
            },
            "stages": stage_statuses
        }

    def reset_metrics(self) -> None:
        """Reset all orchestrator and stage metrics"""
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.successful_executions = 0
        self.failed_executions = 0

        # Reset stage metrics
        for stage in [self.stt_stage, self.rag_stage, self.llm_stage,
                     self.tts_stage, self.history_stage]:
            stage.reset_metrics()

        self.logger.info("All orchestrator and stage metrics reset")

    async def health_check_all_stages(self) -> Dict[str, bool]:
        """Perform health check on all pipeline stages"""
        return {
            "stt": self.stt_stage.health_check(),
            "rag": True,  # RAG doesn't have a direct health check
            "llm": self.llm_stage.health_check(),
            "tts": self.tts_stage.health_check(),
            "history": True  # History is always available if DB is up
        }


# Global orchestrator instance (for backward compatibility)
conversation_orchestrator = ConversationOrchestrator()


# Backward compatibility functions
async def process_conversation_turn_async(*args, **kwargs):
    """Backward compatible function"""
    return await conversation_orchestrator.process_conversation_turn_async(*args, **kwargs)


def process_conversation_turn(*args, **kwargs):
    """Backward compatible function"""
    return conversation_orchestrator.process_conversation_turn(*args, **kwargs)