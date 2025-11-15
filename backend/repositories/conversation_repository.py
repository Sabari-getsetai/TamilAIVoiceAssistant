"""
Conversation Repository - Session and Turn Data Access Layer

This repository handles all database operations for conversation sessions
and turns, including session lifecycle management, turn tracking, and
session analytics.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, asc, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from backend.repositories.base_repository import BaseRepository
from backend.database.models import ConversationSession, ConversationTurn, User
from backend.database.models import SessionStatus


class ConversationSessionRepository(BaseRepository[ConversationSession]):
    """Repository for ConversationSession operations."""

    def __init__(self):
        super().__init__(ConversationSession)

    async def create_session(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        language: str = "ta",
        rag_enabled: bool = True,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Create a new conversation session."""
        session_data = {
            "user_id": user_id,
            "organization_id": organization_id,
            "language": language,
            "rag_enabled": rag_enabled,
            "status": SessionStatus.ACTIVE,
            "session_metadata": session_metadata or {},
            "total_turns": 0,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        return await self.create(db, session_data)

    async def get_session_with_turns(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Optional[ConversationSession]:
        """Get a session with all its turns loaded."""
        try:
            result = await db.execute(
                select(ConversationSession)
                .options(selectinload(ConversationSession.turns))
                .where(ConversationSession.id == session_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get session with turns {session_id}: {e}")
            raise

    async def get_active_sessions_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[ConversationSession]:
        """Get active sessions for a user, most recent first."""
        try:
            result = await db.execute(
                select(ConversationSession)
                .where(
                    and_(
                        ConversationSession.user_id == user_id,
                        ConversationSession.status == SessionStatus.ACTIVE
                    )
                )
                .order_by(desc(ConversationSession.last_activity))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get active sessions for user {user_id}: {e}")
            raise

    async def get_sessions_for_organization(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        status: Optional[SessionStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ConversationSession]:
        """Get sessions for an organization with optional status filter."""
        try:
            query = select(ConversationSession).where(
                ConversationSession.organization_id == organization_id
            )

            if status:
                query = query.where(ConversationSession.status == status)

            query = query.order_by(desc(ConversationSession.created_at))
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get sessions for organization {organization_id}: {e}")
            raise

    async def update_last_activity(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Update the last activity timestamp for a session."""
        try:
            result = await db.execute(
                update(ConversationSession)
                .where(ConversationSession.id == session_id)
                .values(last_activity=datetime.utcnow())
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update last activity for session {session_id}: {e}")
            raise

    async def increment_turn_count(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Increment the turn count for a session."""
        try:
            result = await db.execute(
                update(ConversationSession)
                .where(ConversationSession.id == session_id)
                .values(
                    total_turns=ConversationSession.total_turns + 1,
                    last_activity=datetime.utcnow()
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to increment turn count for session {session_id}: {e}")
            raise

    async def end_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Mark a session as ended."""
        try:
            result = await db.execute(
                update(ConversationSession)
                .where(ConversationSession.id == session_id)
                .values(
                    status=SessionStatus.ENDED,
                    ended_at=datetime.utcnow()
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to end session {session_id}: {e}")
            raise

    async def get_session_analytics(
        self,
        db: AsyncSession,
        organization_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get session analytics for the last N days."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            base_query = select(ConversationSession).where(
                ConversationSession.created_at >= since_date
            )

            if organization_id:
                base_query = base_query.where(
                    ConversationSession.organization_id == organization_id
                )

            # Total sessions
            total_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_sessions = total_result.scalar()

            # Active sessions
            active_result = await db.execute(
                select(func.count())
                .select_from(base_query.subquery())
                .where(ConversationSession.status == SessionStatus.ACTIVE)
            )
            active_sessions = active_result.scalar()

            # Average turns per session
            avg_turns_result = await db.execute(
                select(func.avg(ConversationSession.total_turns))
                .select_from(base_query.subquery())
            )
            avg_turns = avg_turns_result.scalar() or 0

            # Sessions by language
            lang_result = await db.execute(
                select(
                    ConversationSession.language,
                    func.count().label('count')
                )
                .select_from(base_query.subquery())
                .group_by(ConversationSession.language)
            )
            sessions_by_language = {row.language: row.count for row in lang_result}

            return {
                "period_days": days,
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "ended_sessions": total_sessions - active_sessions,
                "avg_turns_per_session": round(avg_turns, 2),
                "sessions_by_language": sessions_by_language,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get session analytics: {e}")
            raise

    async def cleanup_old_sessions(
        self,
        db: AsyncSession,
        days_old: int = 90,
        batch_size: int = 100
    ) -> int:
        """Clean up old ended sessions."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Find sessions to delete
            result = await db.execute(
                select(ConversationSession.id)
                .where(
                    and_(
                        ConversationSession.status == SessionStatus.ENDED,
                        ConversationSession.ended_at < cutoff_date
                    )
                )
                .limit(batch_size)
            )
            session_ids = [row.id for row in result]

            if not session_ids:
                return 0

            # Delete the sessions (turns will cascade delete)
            delete_result = await db.execute(
                delete(ConversationSession)
                .where(ConversationSession.id.in_(session_ids))
            )

            await db.commit()
            deleted_count = delete_result.rowcount

            self.logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count

        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to cleanup old sessions: {e}")
            raise


class ConversationTurnRepository(BaseRepository[ConversationTurn]):
    """Repository for ConversationTurn operations."""

    def __init__(self):
        super().__init__(ConversationTurn)

    async def create_turn(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        turn_number: int,
        user_input: Optional[str] = None,
        assistant_response: Optional[str] = None,
        audio_input_path: Optional[str] = None,
        audio_output_path: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        turn_metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """Create a new conversation turn."""
        turn_data = {
            "session_id": session_id,
            "turn_number": turn_number,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "audio_input_path": audio_input_path,
            "audio_output_path": audio_output_path,
            "processing_time_ms": processing_time_ms,
            "turn_metadata": turn_metadata or {},
            "created_at": datetime.utcnow()
        }
        return await self.create(db, turn_data)

    async def get_turns_for_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get all turns for a session, ordered by turn number."""
        try:
            query = select(ConversationTurn).where(
                ConversationTurn.session_id == session_id
            ).order_by(asc(ConversationTurn.turn_number))

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get turns for session {session_id}: {e}")
            raise

    async def get_latest_turns(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        count: int = 5
    ) -> List[ConversationTurn]:
        """Get the latest N turns for a session."""
        try:
            result = await db.execute(
                select(ConversationTurn)
                .where(ConversationTurn.session_id == session_id)
                .order_by(desc(ConversationTurn.turn_number))
                .limit(count)
            )
            # Reverse to get chronological order
            return list(reversed(result.scalars().all()))
        except Exception as e:
            self.logger.error(f"Failed to get latest turns for session {session_id}: {e}")
            raise

    async def update_turn_response(
        self,
        db: AsyncSession,
        turn_id: uuid.UUID,
        assistant_response: str,
        audio_output_path: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> bool:
        """Update the assistant response for a turn."""
        try:
            update_data = {
                "assistant_response": assistant_response,
                "processing_time_ms": processing_time_ms
            }

            if audio_output_path:
                update_data["audio_output_path"] = audio_output_path

            result = await db.execute(
                update(ConversationTurn)
                .where(ConversationTurn.id == turn_id)
                .values(**update_data)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update turn response {turn_id}: {e}")
            raise

    async def get_turn_analytics(
        self,
        db: AsyncSession,
        session_id: Optional[uuid.UUID] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get turn analytics for recent conversations."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            query = select(ConversationTurn).where(
                ConversationTurn.created_at >= since_date
            )

            if session_id:
                query = query.where(ConversationTurn.session_id == session_id)

            # Total turns
            total_result = await db.execute(
                select(func.count()).select_from(query.subquery())
            )
            total_turns = total_result.scalar()

            # Average processing time
            avg_time_result = await db.execute(
                select(func.avg(ConversationTurn.processing_time_ms))
                .select_from(query.subquery())
                .where(ConversationTurn.processing_time_ms.isnot(None))
            )
            avg_processing_time = avg_time_result.scalar() or 0

            # Turns with audio
            audio_turns_result = await db.execute(
                select(func.count())
                .select_from(query.subquery())
                .where(ConversationTurn.audio_input_path.isnot(None))
            )
            audio_turns = audio_turns_result.scalar()

            return {
                "period_days": days,
                "total_turns": total_turns,
                "audio_turns": audio_turns,
                "text_only_turns": total_turns - audio_turns,
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "audio_usage_percentage": round((audio_turns / total_turns * 100), 2) if total_turns > 0 else 0,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get turn analytics: {e}")
            raise