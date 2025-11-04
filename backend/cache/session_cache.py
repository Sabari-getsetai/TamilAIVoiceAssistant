"""
Session caching utilities for Tamil AI Voice Assistant.

This module provides:
- Session data caching in Redis
- Fast session retrieval
- Session expiration management
- Conversation state persistence
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from .redis_client import get_redis_client, REDIS_SESSION_TTL

logger = logging.getLogger(__name__)


class SessionCache:
    """Redis-based session cache for conversation management."""

    def __init__(self, ttl_seconds: int = REDIS_SESSION_TTL):
        self.ttl_seconds = ttl_seconds
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session data."""
        return f"{self.session_prefix}{session_id}"

    def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user's session list."""
        return f"{self.user_sessions_prefix}{user_id}"

    async def store_session(
        self,
        session_id: str,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """
        Store session data in Redis.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            session_data: Session data to store

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            session_key = self._get_session_key(session_id)
            user_sessions_key = self._get_user_sessions_key(user_id)

            # Add metadata to session data
            session_data_with_meta = {
                **session_data,
                "session_id": session_id,
                "user_id": user_id,
                "cached_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }

            # Use pipeline for atomic operations
            async with client.pipeline() as pipe:
                # Store session data
                await pipe.hset(
                    session_key,
                    mapping={
                        field: json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                        for field, value in session_data_with_meta.items()
                    }
                )
                await pipe.expire(session_key, self.ttl_seconds)

                # Add session to user's session set
                await pipe.sadd(user_sessions_key, session_id)
                await pipe.expire(user_sessions_key, self.ttl_seconds)

                await pipe.execute()

            logger.debug(f"Stored session {session_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing session {session_id}: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.

        Args:
            session_id: Session identifier

        Returns:
            dict: Session data or None if not found
        """
        try:
            client = await get_redis_client()
            session_key = self._get_session_key(session_id)

            # Get all session data
            session_data = await client.hgetall(session_key)

            if not session_data:
                return None

            # Decode and parse session data
            decoded_data = {}
            for field, value in session_data.items():
                if isinstance(field, bytes):
                    field = field.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')

                # Try to JSON decode
                try:
                    decoded_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    decoded_data[field] = value

            # Update last access time
            await self.update_session_activity(session_id)

            logger.debug(f"Retrieved session {session_id}")
            return decoded_data

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    async def update_session_activity(self, session_id: str) -> bool:
        """
        Update session's last activity timestamp.

        Args:
            session_id: Session identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            session_key = self._get_session_key(session_id)

            # Update last activity and extend TTL
            async with client.pipeline() as pipe:
                await pipe.hset(
                    session_key,
                    "last_activity",
                    datetime.utcnow().isoformat()
                )
                await pipe.expire(session_key, self.ttl_seconds)
                await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Error updating session activity {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete session from Redis.

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            session_key = self._get_session_key(session_id)
            user_sessions_key = self._get_user_sessions_key(user_id)

            # Use pipeline for atomic operations
            async with client.pipeline() as pipe:
                await pipe.delete(session_key)
                await pipe.srem(user_sessions_key, session_id)
                await pipe.execute()

            logger.debug(f"Deleted session {session_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get list of active sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            list: List of session IDs
        """
        try:
            client = await get_redis_client()
            user_sessions_key = self._get_user_sessions_key(user_id)

            session_ids = await client.smembers(user_sessions_key)
            return [sid.decode('utf-8') if isinstance(sid, bytes) else sid for sid in session_ids]

        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

    async def cleanup_expired_sessions(self, user_id: str) -> int:
        """
        Clean up expired sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            int: Number of sessions cleaned up
        """
        try:
            client = await get_redis_client()
            user_sessions_key = self._get_user_sessions_key(user_id)

            # Get all session IDs for user
            session_ids = await self.get_user_sessions(user_id)
            cleaned_count = 0

            for session_id in session_ids:
                session_key = self._get_session_key(session_id)

                # Check if session exists
                exists = await client.exists(session_key)
                if not exists:
                    # Remove from user's session set
                    await client.srem(user_sessions_key, session_id)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions for user {user_id}")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up sessions for user {user_id}: {e}")
            return 0

    async def store_conversation_turn(
        self,
        session_id: str,
        turn_number: int,
        turn_data: Dict[str, Any]
    ) -> bool:
        """
        Store conversation turn data.

        Args:
            session_id: Session identifier
            turn_number: Turn number in conversation
            turn_data: Turn data to store

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            turn_key = f"turn:{session_id}:{turn_number}"

            # Store turn data with expiration
            turn_data_with_meta = {
                **turn_data,
                "session_id": session_id,
                "turn_number": turn_number,
                "timestamp": datetime.utcnow().isoformat()
            }

            await client.hset(
                turn_key,
                mapping={
                    field: json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                    for field, value in turn_data_with_meta.items()
                }
            )
            await client.expire(turn_key, self.ttl_seconds)

            logger.debug(f"Stored turn {turn_number} for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing conversation turn {session_id}:{turn_number}: {e}")
            return False

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of turns to retrieve

        Returns:
            list: List of conversation turns
        """
        try:
            client = await get_redis_client()

            # Find all turn keys for this session
            turn_pattern = f"turn:{session_id}:*"
            turn_keys = await client.keys(turn_pattern)

            if not turn_keys:
                return []

            # Sort by turn number and limit
            sorted_keys = sorted(
                turn_keys,
                key=lambda k: int(k.decode('utf-8').split(':')[-1]) if isinstance(k, bytes) else int(k.split(':')[-1])
            )[-limit:]

            # Get turn data
            history = []
            for turn_key in sorted_keys:
                turn_data = await client.hgetall(turn_key)
                if turn_data:
                    # Decode turn data
                    decoded_turn = {}
                    for field, value in turn_data.items():
                        if isinstance(field, bytes):
                            field = field.decode('utf-8')
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')

                        try:
                            decoded_turn[field] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            decoded_turn[field] = value

                    history.append(decoded_turn)

            return history

        except Exception as e:
            logger.error(f"Error getting conversation history for session {session_id}: {e}")
            return []

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists in cache.

        Args:
            session_id: Session identifier

        Returns:
            bool: True if session exists, False otherwise
        """
        try:
            client = await get_redis_client()
            session_key = self._get_session_key(session_id)
            return bool(await client.exists(session_key))

        except Exception as e:
            logger.error(f"Error checking session existence {session_id}: {e}")
            return False