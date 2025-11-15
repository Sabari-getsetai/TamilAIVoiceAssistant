"""History Pipeline Stage

This module handles conversation history management, including saving
conversation turns and updating session metadata.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from backend.orchestration.pipelines.base_pipeline import (
    BasePipelineStage, PipelineStageType, ConversationState, PipelineStageError
)
from backend.repositories.conversation_repository import (
    ConversationSessionRepository, ConversationTurnRepository
)
from backend.database.models import SessionStatus


class HistoryStage(BasePipelineStage):
    """History management pipeline stage"""

    def __init__(self):
        super().__init__(
            stage_type=PipelineStageType.HISTORY,
            stage_name="history"
        )

        # Configure stage requirements
        self.required_inputs = ["session_id", "user_text", "assistant_text"]
        self.provided_outputs = ["conversation_history", "total_turns"]

        # History configuration
        self.max_history_turns = 50
        self.auto_summarize_threshold = 20  # Summarize when history exceeds this

        # Initialize repositories
        self.session_repo = ConversationSessionRepository()
        self.turn_repo = ConversationTurnRepository()

    async def process(self, state: ConversationState) -> ConversationState:
        """
        Process conversation turn and update history

        Args:
            state: Current conversation state

        Returns:
            Updated state with conversation_history and total_turns

        Raises:
            PipelineStageError: If history processing fails
        """
        try:
            session_id = state["session_id"]
            user_text = state["user_text"]
            assistant_text = state["assistant_text"]

            # Get database session
            async for db in self._get_db_session():
                try:
                    # Create conversation turn record
                    turn_data = await self._create_conversation_turn(
                        db, session_id, user_text, assistant_text, state
                    )

                    # Update session metadata
                    await self._update_session_metadata(db, session_id, state)

                    # Get updated conversation history
                    conversation_history = await self._get_conversation_history(db, session_id)

                    # Update state with history information
                    state["conversation_history"] = conversation_history
                    state["total_turns"] = len(conversation_history)

                    # Add history metadata to custom context
                    if "custom_context" not in state:
                        state["custom_context"] = {}

                    state["custom_context"]["history_metadata"] = {
                        "turn_id": turn_data["id"],
                        "session_id": session_id,
                        "total_turns": len(conversation_history),
                        "history_length": sum(
                            len(turn.get("user_text", "")) + len(turn.get("assistant_text", ""))
                            for turn in conversation_history
                        ),
                        "session_duration_minutes": self._calculate_session_duration(conversation_history)
                    }

                    self.logger.info(
                        f"History updated: Session {session_id} now has {len(conversation_history)} turns"
                    )

                    return state

                except Exception as e:
                    await db.rollback()
                    raise e
                finally:
                    await db.close()

        except Exception as e:
            self.logger.error(f"History processing failed: {str(e)}")
            raise PipelineStageError(
                self.stage_name,
                f"History management failed: {str(e)}",
                cause=e
            )

    async def _get_db_session(self):
        """Get database session"""
        from backend.database.connection import get_db
        async for db in get_db():
            yield db

    async def _create_conversation_turn(
        self,
        db,
        session_id: str,
        user_text: str,
        assistant_text: str,
        state: ConversationState
    ) -> Dict[str, Any]:
        """Create a conversation turn record in the database"""
        try:
            # Extract metadata from pipeline execution
            stage_metrics = state.get("stage_metrics", {})
            custom_context = state.get("custom_context", {})

            # Build turn metadata
            turn_metadata = {
                "pipeline_execution": {
                    "pipeline_id": state.get("pipeline_id"),
                    "completed_stages": state.get("completed_stages", []),
                    "stage_metrics": stage_metrics
                },
                "content_metadata": {
                    "user_text_length": len(user_text),
                    "assistant_text_length": len(assistant_text),
                    "language": state.get("language", "ta"),
                    "rag_used": bool(state.get("context_used")),
                    "num_retrieved_docs": len(state.get("retrieved_documents", []))
                },
                "audio_metadata": {
                    "has_audio_input": bool(state.get("audio_input_path") or state.get("audio_input")),
                    "has_audio_output": bool(state.get("audio_output")),
                    "audio_output_path": state.get("audio_output_path"),
                    "tts_metadata": custom_context.get("tts_metadata"),
                    "stt_metadata": custom_context.get("stt_metadata")
                },
                "processing_metadata": {
                    "rag_metadata": custom_context.get("rag_metadata"),
                    "llm_metadata": custom_context.get("llm_metadata")
                }
            }

            # Create turn using repository
            turn = await self.turn_repo.create_turn(
                db=db,
                session_id=session_id,
                user_text=user_text,
                assistant_text=assistant_text,
                audio_input_path=state.get("audio_input_path"),
                audio_output_path=state.get("audio_output_path"),
                metadata=turn_metadata
            )

            return {
                "id": turn.id,
                "created_at": turn.created_at,
                "metadata": turn_metadata
            }

        except Exception as e:
            raise PipelineStageError(
                self.stage_name,
                f"Failed to create conversation turn: {str(e)}",
                cause=e
            )

    async def _update_session_metadata(
        self,
        db,
        session_id: str,
        state: ConversationState
    ) -> None:
        """Update session metadata with current activity"""
        try:
            # Calculate session statistics
            current_time = datetime.utcnow()
            session_stats = {
                "last_activity": current_time,
                "total_pipeline_executions": state.get("total_turns", 0) + 1,
                "languages_used": [state.get("language", "ta")],  # Could track multiple languages
                "features_used": {
                    "rag": bool(state.get("context_used")),
                    "audio_input": bool(state.get("audio_input_path") or state.get("audio_input")),
                    "audio_output": bool(state.get("audio_output")),
                    "multimodal": bool(state.get("audio_input_path")) and bool(state.get("audio_output"))
                }
            }

            # Update session using repository
            await self.session_repo.update_activity(
                db=db,
                session_id=session_id,
                last_activity=current_time,
                metadata=session_stats
            )

        except Exception as e:
            self.logger.warning(f"Failed to update session metadata: {str(e)}")
            # Don't fail the entire pipeline for metadata updates

    async def _get_conversation_history(
        self,
        db,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history for the session"""
        try:
            # Get recent turns using repository
            recent_turns = await self.turn_repo.get_recent_turns(
                db=db,
                session_id=session_id,
                limit=self.max_history_turns
            )

            # Convert to conversation history format
            history = []
            for turn in recent_turns:
                history.append({
                    "turn_id": turn.id,
                    "user_text": turn.user_text,
                    "assistant_text": turn.assistant_text,
                    "created_at": turn.created_at,
                    "audio_input_path": turn.audio_input_path,
                    "audio_output_path": turn.audio_output_path,
                    "metadata": turn.metadata
                })

            # Sort by creation time (oldest first for proper conversation flow)
            history.sort(key=lambda x: x["created_at"])

            return history

        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {str(e)}")
            return []

    def _calculate_session_duration(self, conversation_history: List[Dict[str, Any]]) -> float:
        """Calculate session duration in minutes from conversation history"""
        if not conversation_history or len(conversation_history) < 2:
            return 0.0

        try:
            earliest = min(turn["created_at"] for turn in conversation_history)
            latest = max(turn["created_at"] for turn in conversation_history)
            duration = (latest - earliest).total_seconds() / 60.0
            return round(duration, 2)

        except Exception:
            return 0.0

    async def get_session_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        try:
            async for db in self._get_db_session():
                try:
                    # Get session info
                    session = await self.session_repo.get_by_id(db, session_id)
                    if not session:
                        return {"error": "Session not found"}

                    # Get session statistics
                    stats = await self.session_repo.get_session_analytics(db, session_id)

                    # Get conversation history
                    history = await self._get_conversation_history(db, session_id)

                    # Calculate summary metrics
                    summary_metrics = self._calculate_summary_metrics(history)

                    return {
                        "session_id": session_id,
                        "created_at": session.created_at,
                        "last_activity": session.last_activity,
                        "status": session.status.value if session.status else "unknown",
                        "total_turns": len(history),
                        "session_duration_minutes": self._calculate_session_duration(history),
                        "language": session.language,
                        "rag_enabled": session.rag_enabled,
                        "user_id": session.user_id,
                        "organization_id": session.organization_id,
                        "statistics": stats,
                        "summary_metrics": summary_metrics,
                        "recent_activity": history[-5:] if history else []  # Last 5 turns
                    }

                finally:
                    await db.close()

        except Exception as e:
            self.logger.error(f"Failed to get session summary: {str(e)}")
            return {"error": str(e)}

    def _calculate_summary_metrics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics from conversation history"""
        if not history:
            return {}

        try:
            total_user_chars = sum(len(turn.get("user_text", "")) for turn in history)
            total_assistant_chars = sum(len(turn.get("assistant_text", "")) for turn in history)
            audio_turns = sum(1 for turn in history if turn.get("audio_input_path"))
            rag_turns = sum(
                1 for turn in history
                if turn.get("metadata", {}).get("content_metadata", {}).get("rag_used", False)
            )

            avg_turn_length = (total_user_chars + total_assistant_chars) / (len(history) * 2) if history else 0

            return {
                "total_user_characters": total_user_chars,
                "total_assistant_characters": total_assistant_chars,
                "average_turn_length": round(avg_turn_length, 1),
                "audio_turns_count": audio_turns,
                "audio_usage_percentage": round(audio_turns / len(history) * 100, 1) if history else 0,
                "rag_turns_count": rag_turns,
                "rag_usage_percentage": round(rag_turns / len(history) * 100, 1) if history else 0,
                "conversation_intensity": self._calculate_conversation_intensity(history)
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate summary metrics: {str(e)}")
            return {}

    def _calculate_conversation_intensity(self, history: List[Dict[str, Any]]) -> str:
        """Calculate conversation intensity level"""
        if not history:
            return "none"

        try:
            if len(history) >= 20:
                return "high"
            elif len(history) >= 10:
                return "medium"
            elif len(history) >= 3:
                return "low"
            else:
                return "minimal"

        except Exception:
            return "unknown"

    async def cleanup_old_sessions(
        self,
        older_than_days: int = 30,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Clean up old inactive sessions"""
        try:
            cleanup_results = {
                "sessions_found": 0,
                "sessions_cleaned": 0,
                "turns_cleaned": 0,
                "errors": [],
                "dry_run": dry_run
            }

            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            async for db in self._get_db_session():
                try:
                    # Find old sessions
                    old_sessions = await self.session_repo.get_inactive_sessions(db, cutoff_date)
                    cleanup_results["sessions_found"] = len(old_sessions)

                    if not dry_run:
                        # Clean up each session
                        for session in old_sessions:
                            try:
                                # Delete turns first
                                turns_deleted = await self.turn_repo.delete_by_session(db, session.id)
                                cleanup_results["turns_cleaned"] += turns_deleted

                                # Delete session
                                await self.session_repo.delete_session(db, session.id)
                                cleanup_results["sessions_cleaned"] += 1

                            except Exception as e:
                                cleanup_results["errors"].append(
                                    f"Failed to clean session {session.id}: {str(e)}"
                                )

                        await db.commit()

                    return cleanup_results

                except Exception as e:
                    await db.rollback()
                    raise e
                finally:
                    await db.close()

        except Exception as e:
            self.logger.error(f"Session cleanup failed: {str(e)}")
            return {
                "error": str(e),
                "sessions_found": 0,
                "sessions_cleaned": 0,
                "turns_cleaned": 0,
                "dry_run": dry_run
            }

    def configure_history(
        self,
        max_history_turns: Optional[int] = None,
        auto_summarize_threshold: Optional[int] = None
    ) -> None:
        """
        Configure history management parameters

        Args:
            max_history_turns: Maximum turns to keep in active history
            auto_summarize_threshold: Turn count threshold for auto-summarization
        """
        if max_history_turns is not None:
            self.max_history_turns = max(1, min(100, max_history_turns))

        if auto_summarize_threshold is not None:
            self.auto_summarize_threshold = max(5, min(50, auto_summarize_threshold))

        self.logger.info(
            f"History configuration updated: "
            f"max_turns={self.max_history_turns}, "
            f"summarize_threshold={self.auto_summarize_threshold}"
        )

    def get_history_status(self) -> Dict[str, Any]:
        """Get current history management status"""
        return {
            "max_history_turns": self.max_history_turns,
            "auto_summarize_threshold": self.auto_summarize_threshold,
            "repositories_loaded": {
                "session_repo": self.session_repo is not None,
                "turn_repo": self.turn_repo is not None
            }
        }