"""
Session Service for Tamil AI Voice Assistant

This module provides database-integrated session management with Redis caching:
- Persistent session storage in PostgreSQL
- Fast session retrieval with Redis caching
- Conversation turn persistence
- Audio file metadata tracking
- Session lifecycle management
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, update
from sqlalchemy.exc import IntegrityError

from database.connection import get_db
from database.models import (
    ConversationSession, ConversationTurn, AudioFile, User,
    SessionStatus, AudioFileType, generate_uuid, utc_now
)
from cache.session_cache import SessionCache
from settings import settings

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Database-integrated session manager with Redis caching.

    Provides:
    - Persistent session storage in PostgreSQL
    - Fast retrieval with Redis caching
    - Conversation turn management
    - Audio file tracking
    - Session analytics
    """

    def __init__(self):
        self.cache = SessionCache()
        self.session_timeout_minutes = settings.CHAT_SESSION_TIMEOUT_MINUTES
        self.max_history_turns = settings.CHAT_MAX_HISTORY_TURNS

    async def create_session(
        self,
        user_id: Optional[str] = None,
        language: str = "ta",
        rag_enabled: bool = True,
        session_metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Create a new conversation session.

        Args:
            user_id: User identifier (optional for anonymous sessions)
            language: Conversation language (default: "ta")
            rag_enabled: Enable RAG document retrieval
            session_metadata: Optional metadata dictionary
            db: Database session (will create if not provided)

        Returns:
            Session ID

        Raises:
            ValueError: If user_id is not a valid UUID format
            Exception: If session creation fails
        """
        session_id = generate_uuid()

        # Validate user_id is a valid UUID if provided
        if user_id:
            try:
                uuid.UUID(user_id)
            except (ValueError, AttributeError, TypeError) as e:
                raise ValueError(f"Invalid UUID format for user_id: {user_id}") from e

        # Use provided db session or create new one
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Validate user exists if user_id provided
            if user_id:
                result = await db_session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    raise ValueError(f"User not found: {user_id}")

                if not user.is_active:
                    raise ValueError(f"User account is disabled: {user_id}")

            # Create session record
            now = utc_now()
            session = ConversationSession(
                id=session_id,
                user_id=user_id,
                language=language,
                rag_enabled=rag_enabled,
                status=SessionStatus.ACTIVE,
                created_at=now,
                last_activity=now,
                ended_at=None,
                total_turns=0,
                session_metadata=session_metadata or {}
            )

            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            # Cache session data in Redis
            await self._cache_session_data(session)

            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to create session: {e}")
            raise
        finally:
            if should_close_db:
                await db_session.close()

    async def get_session(
        self,
        session_id: str,
        db: Optional[AsyncSession] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information.

        Args:
            session_id: Session identifier
            db: Database session (will create if not provided)
            use_cache: Use Redis cache for faster retrieval

        Returns:
            Session data dictionary or None if not found
        """
        # Try cache first if enabled
        if use_cache:
            cached_session = await self.cache.get_session(session_id)
            if cached_session:
                return cached_session

        # Use provided db session or create new one
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Query database
            result = await db_session.execute(
                select(ConversationSession).where(
                    ConversationSession.id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                return None

            # Check if session is expired
            if self._is_session_expired(session):
                await self._expire_session(session, db_session)
                return None

            # Update last activity
            await self._update_session_activity(session, db_session)

            # Convert to dictionary
            session_data = await self._session_to_dict(session, db_session)

            # Cache the session data
            if use_cache:
                await self._cache_session_data(session, session_data)

            return session_data

        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
        finally:
            if should_close_db:
                await db_session.close()

    async def update_session_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Update session metadata.

        Args:
            session_id: Session identifier
            metadata: Metadata to merge with existing
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Get current session
            result = await db_session.execute(
                select(ConversationSession).where(
                    ConversationSession.id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session or self._is_session_expired(session):
                return False

            # Merge metadata
            current_metadata = session.session_metadata or {}
            updated_metadata = {**current_metadata, **metadata}

            # Update session
            session.session_metadata = updated_metadata
            session.last_activity = utc_now()

            await db_session.commit()

            # Update cache
            await self.cache.update_session_activity(session_id)

            logger.debug(f"Updated metadata for session {session_id}")
            return True

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to update session metadata {session_id}: {e}")
            return False
        finally:
            if should_close_db:
                await db_session.close()

    async def add_conversation_turn(
        self,
        session_id: str,
        user_text: Optional[str] = None,
        assistant_text: Optional[str] = None,
        audio_input_key: Optional[str] = None,
        audio_output_key: Optional[str] = None,
        retrieved_chunks: Optional[List[str]] = None,
        processing_time: Optional[Dict[str, float]] = None,
        turn_metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> Optional[str]:
        """
        Add a conversation turn to the session.

        Args:
            session_id: Session identifier
            user_text: User's message text
            assistant_text: Assistant's response text
            audio_input_key: MinIO key for user audio
            audio_output_key: MinIO key for assistant audio
            retrieved_chunks: List of document chunk IDs used
            processing_time: Performance metrics
            turn_metadata: Additional turn metadata
            db: Database session

        Returns:
            Turn ID if successful, None otherwise
        """
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Get current session
            result = await db_session.execute(
                select(ConversationSession).where(
                    ConversationSession.id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session or self._is_session_expired(session):
                return None

            # Create conversation turn
            turn_id = generate_uuid()
            turn_number = session.total_turns + 1

            turn = ConversationTurn(
                id=turn_id,
                session_id=session_id,
                turn_number=turn_number,
                user_text=user_text,
                assistant_text=assistant_text,
                audio_input_key=audio_input_key,
                audio_output_key=audio_output_key,
                retrieved_chunks=retrieved_chunks or [],
                processing_time=processing_time or {},
                timestamp=utc_now(),
                turn_metadata=turn_metadata or {}
            )

            # Update session
            session.total_turns = turn_number
            session.last_activity = utc_now()

            db_session.add(turn)
            await db_session.commit()

            # Cache turn data
            await self.cache.store_conversation_turn(
                session_id,
                turn_number,
                {
                    "turn_id": turn_id,
                    "user_text": user_text,
                    "assistant_text": assistant_text,
                    "audio_input_key": audio_input_key,
                    "audio_output_key": audio_output_key,
                    "retrieved_chunks": retrieved_chunks,
                    "processing_time": processing_time,
                    "turn_metadata": turn_metadata
                }
            )

            logger.debug(f"Added turn {turn_number} to session {session_id}")
            return turn_id

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to add conversation turn to session {session_id}: {e}")
            return None
        finally:
            if should_close_db:
                await db_session.close()

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = None,
        db: Optional[AsyncSession] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of turns (default: max_history_turns)
            db: Database session
            use_cache: Use Redis cache for faster retrieval

        Returns:
            List of conversation turns
        """
        if limit is None:
            limit = self.max_history_turns

        # Try cache first if enabled
        if use_cache:
            cached_history = await self.cache.get_conversation_history(session_id, limit)
            if cached_history:
                return cached_history

        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Query database for recent turns
            result = await db_session.execute(
                select(ConversationTurn)
                .where(ConversationTurn.session_id == session_id)
                .order_by(desc(ConversationTurn.turn_number))
                .limit(limit)
            )
            turns = result.scalars().all()

            # Convert to list and reverse to get chronological order
            history = []
            for turn in reversed(turns):
                history.append({
                    "turn_id": turn.id,
                    "turn_number": turn.turn_number,
                    "user_text": turn.user_text,
                    "assistant_text": turn.assistant_text,
                    "audio_input_key": turn.audio_input_key,
                    "audio_output_key": turn.audio_output_key,
                    "retrieved_chunks": turn.retrieved_chunks,
                    "processing_time": turn.processing_time,
                    "timestamp": turn.timestamp.isoformat(),
                    "turn_metadata": turn.turn_metadata
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get conversation history for session {session_id}: {e}")
            return []
        finally:
            if should_close_db:
                await db_session.close()

    async def delete_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Delete a conversation session and all related data.

        Args:
            session_id: Session identifier
            user_id: User identifier for authorization check
            db: Database session

        Returns:
            True if deleted, False otherwise
        
        Raises:
            ValueError: If user_id is not a valid UUID format
        """
        # Validate user_id is a valid UUID if provided
        if user_id:
            try:
                uuid.UUID(user_id)
            except (ValueError, AttributeError, TypeError) as e:
                raise ValueError(f"Invalid UUID format for user_id: {user_id}") from e

        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Get session
            result = await db_session.execute(
                select(ConversationSession).where(
                    ConversationSession.id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                return False

            # Check authorization if user_id provided
            if user_id and session.user_id != user_id:
                logger.warning(f"Unauthorized session deletion attempt: user {user_id} vs session user {session.user_id}")
                return False

            # Update session status instead of hard delete for audit trail
            session.status = SessionStatus.ENDED
            session.ended_at = utc_now()
            session.last_activity = utc_now()

            await db_session.commit()

            # Remove from cache
            if session.user_id:
                await self.cache.delete_session(session_id, session.user_id)

            logger.info(f"Deleted session {session_id}")
            return True

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
        finally:
            if should_close_db:
                await db_session.close()

    async def list_user_sessions(
        self,
        user_id: str,
        status_filter: Optional[SessionStatus] = SessionStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        List sessions for a user.

        Args:
            user_id: User identifier
            status_filter: Filter by session status (None for all)
            limit: Maximum number of sessions
            offset: Pagination offset
            db: Database session

        Returns:
            List of session information dictionaries
        
        Raises:
            ValueError: If user_id is not a valid UUID format
        """
        # Validate user_id is a valid UUID
        try:
            uuid.UUID(user_id)
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"Invalid UUID format for user_id: {user_id}") from e

        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Build query
            query = select(ConversationSession).where(
                ConversationSession.user_id == user_id
            )

            if status_filter:
                query = query.where(ConversationSession.status == status_filter)

            query = query.order_by(desc(ConversationSession.last_activity))
            query = query.offset(offset).limit(limit)

            result = await db_session.execute(query)
            sessions = result.scalars().all()

            # Convert to dictionaries
            session_list = []
            for session in sessions:
                session_data = await self._session_to_dict(session, db_session)
                session_list.append(session_data)

            return session_list

        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return []
        finally:
            if should_close_db:
                await db_session.close()

    async def get_session_stats(
        self,
        session_id: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed session statistics.

        Args:
            session_id: Session identifier
            db: Database session

        Returns:
            Session statistics dictionary
        """
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Get session info
            session_result = await db_session.execute(
                select(ConversationSession).where(
                    ConversationSession.id == session_id
                )
            )
            session = session_result.scalar_one_or_none()

            if not session:
                return None

            # Get turn statistics
            turn_stats_result = await db_session.execute(
                select(
                    func.count(ConversationTurn.id).label('total_turns'),
                    func.sum(
                        func.cast(
                            func.json_extract_path_text(
                                ConversationTurn.processing_time, 'total'
                            ),
                            db_session.bind.dialect.type_descriptor(db_session.bind.dialect.FLOAT)
                        )
                    ).label('total_processing_time'),
                    func.avg(
                        func.cast(
                            func.json_extract_path_text(
                                ConversationTurn.processing_time, 'total'
                            ),
                            db_session.bind.dialect.type_descriptor(db_session.bind.dialect.FLOAT)
                        )
                    ).label('avg_processing_time')
                ).where(ConversationTurn.session_id == session_id)
            )
            turn_stats = turn_stats_result.first()

            # Calculate session duration
            duration_seconds = 0
            if session.ended_at:
                duration_seconds = (session.ended_at - session.created_at).total_seconds()
            else:
                duration_seconds = (session.last_activity - session.created_at).total_seconds()

            return {
                "session_id": session_id,
                "user_id": session.user_id,
                "status": session.status.value,
                "language": session.language,
                "rag_enabled": session.rag_enabled,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "duration_seconds": duration_seconds,
                "total_turns": turn_stats.total_turns or 0,
                "total_processing_time": float(turn_stats.total_processing_time or 0),
                "avg_processing_time": float(turn_stats.avg_processing_time or 0),
                "session_metadata": session.session_metadata
            }

        except Exception as e:
            logger.error(f"Failed to get session stats for {session_id}: {e}")
            return None
        finally:
            if should_close_db:
                await db_session.close()

    async def cleanup_expired_sessions(
        self,
        batch_size: int = 100,
        db: Optional[AsyncSession] = None
    ) -> int:
        """
        Clean up expired sessions.

        Args:
            batch_size: Number of sessions to process at once
            db: Database session

        Returns:
            Number of sessions cleaned up
        """
        db_session = db
        should_close_db = False
        if db_session is None:
            db_session = await anext(get_db())
            should_close_db = True

        try:
            # Calculate expiry threshold
            expiry_threshold = utc_now() - timedelta(minutes=self.session_timeout_minutes)

            # Find expired active sessions
            result = await db_session.execute(
                select(ConversationSession.id, ConversationSession.user_id)
                .where(
                    and_(
                        ConversationSession.status == SessionStatus.ACTIVE,
                        ConversationSession.last_activity < expiry_threshold
                    )
                )
                .limit(batch_size)
            )
            expired_sessions = result.fetchall()

            if not expired_sessions:
                return 0

            # Update expired sessions
            session_ids = [session.id for session in expired_sessions]
            await db_session.execute(
                update(ConversationSession)
                .where(ConversationSession.id.in_(session_ids))
                .values(
                    status=SessionStatus.EXPIRED,
                    ended_at=utc_now()
                )
            )

            await db_session.commit()

            # Remove from cache
            for session in expired_sessions:
                if session.user_id:
                    await self.cache.delete_session(session.id, session.user_id)

            cleanup_count = len(expired_sessions)
            logger.info(f"Cleaned up {cleanup_count} expired sessions")
            return cleanup_count

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
        finally:
            if should_close_db:
                await db_session.close()

    # Private helper methods

    def _is_session_expired(self, session: ConversationSession) -> bool:
        """Check if session is expired based on last activity."""
        if session.status != SessionStatus.ACTIVE:
            return True

        expiry_threshold = utc_now() - timedelta(minutes=self.session_timeout_minutes)
        return session.last_activity < expiry_threshold

    async def _expire_session(
        self,
        session: ConversationSession,
        db: AsyncSession
    ) -> None:
        """Mark session as expired in database."""
        session.status = SessionStatus.EXPIRED
        session.ended_at = utc_now()
        await db.commit()

    async def _update_session_activity(
        self,
        session: ConversationSession,
        db: AsyncSession
    ) -> None:
        """Update session last activity timestamp."""
        session.last_activity = utc_now()
        await db.commit()

    async def _session_to_dict(
        self,
        session: ConversationSession,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Convert session model to dictionary."""
        duration_seconds = 0
        if session.ended_at:
            duration_seconds = (session.ended_at - session.created_at).total_seconds()
        else:
            duration_seconds = (session.last_activity - session.created_at).total_seconds()

        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "language": session.language,
            "rag_enabled": session.rag_enabled,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "total_turns": session.total_turns,
            "duration_seconds": duration_seconds,
            "session_metadata": session.session_metadata or {}
        }

    async def _cache_session_data(
        self,
        session: ConversationSession,
        session_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Cache session data in Redis."""
        if not session.user_id:
            return  # Don't cache anonymous sessions

        try:
            if session_data is None:
                session_data = {
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "language": session.language,
                    "rag_enabled": session.rag_enabled,
                    "status": session.status.value,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "total_turns": session.total_turns,
                    "session_metadata": session.session_metadata or {}
                }

            await self.cache.store_session(
                session.id,
                session.user_id,
                session_data
            )
        except Exception as e:
            logger.warning(f"Failed to cache session data {session.id}: {e}")


# Global instance
_session_manager = None

async def get_session_manager() -> DatabaseSessionManager:
    """Get singleton session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager
