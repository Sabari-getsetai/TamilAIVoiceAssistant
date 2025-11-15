"""
User Tier Detection Service for Tamil AI Voice Assistant

This service provides functionality to detect and manage user subscription tiers,
supporting audio retention policies and feature access control.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import User, ConversationSession
from backend.database.connection import get_db
from backend.settings import get_audio_retention_hours

logger = logging.getLogger(__name__)


class UserTierService:
    """Service for managing user tier detection and tier-based features."""

    @staticmethod
    async def get_user_tier_by_user_id(user_id: str, db_session: Optional[AsyncSession] = None) -> str:
        """
        Get user tier by user ID.

        Args:
            user_id: User identifier
            db_session: Optional database session (will create new one if not provided)

        Returns:
            User tier ('FREE', 'PRO', 'ENTERPRISE') or 'FREE' as default
        """
        if not user_id or user_id == "anonymous":
            return "FREE"

        # Use provided session or create new one
        if db_session is None:
            async for db_session in get_db():
                return await UserTierService._fetch_user_tier(user_id, db_session)
        else:
            return await UserTierService._fetch_user_tier(user_id, db_session)

    @staticmethod
    async def _fetch_user_tier(user_id: str, db_session: AsyncSession) -> str:
        """
        Internal method to fetch user tier from database.

        Args:
            user_id: User identifier
            db_session: Database session

        Returns:
            User tier string
        """
        try:
            # Get tier from User table
            user_stmt = select(User.subscription_tier).where(User.id == user_id)
            user_result = await db_session.execute(user_stmt)
            user_tier = user_result.scalar()

            if user_tier:
                # Normalize tier to uppercase
                tier = user_tier.upper()
                if tier in ["FREE", "PRO", "ENTERPRISE"]:
                    logger.debug(f"User {user_id} tier: {tier}")
                    return tier

            # Default fallback
            logger.info(f"User {user_id} not found or no tier set, defaulting to FREE")
            return "FREE"

        except Exception as e:
            logger.error(f"Error fetching user tier for {user_id}: {e}")
            return "FREE"  # Safe default

    @staticmethod
    async def get_user_tier_by_session_id(session_id: str, db_session: Optional[AsyncSession] = None) -> str:
        """
        Get user tier by conversation session ID.

        Args:
            session_id: Conversation session identifier
            db_session: Optional database session

        Returns:
            User tier ('FREE', 'PRO', 'ENTERPRISE') or 'FREE' as default
        """
        if not session_id:
            return "FREE"

        # Use provided session or create new one
        if db_session is None:
            async for db_session in get_db():
                return await UserTierService._fetch_user_tier_by_session(session_id, db_session)
        else:
            return await UserTierService._fetch_user_tier_by_session(session_id, db_session)

    @staticmethod
    async def _fetch_user_tier_by_session(session_id: str, db_session: AsyncSession) -> str:
        """
        Internal method to fetch user tier by session ID.

        Args:
            session_id: Session identifier
            db_session: Database session

        Returns:
            User tier string
        """
        try:
            # Get user_id from conversation session
            session_stmt = select(ConversationSession.user_id).where(
                ConversationSession.id == session_id
            )
            session_result = await db_session.execute(session_stmt)
            user_id = session_result.scalar()

            if user_id:
                return await UserTierService._fetch_user_tier(user_id, db_session)
            else:
                # Anonymous session
                logger.debug(f"Session {session_id} has no user_id (anonymous), defaulting to FREE")
                return "FREE"

        except Exception as e:
            logger.error(f"Error fetching user tier for session {session_id}: {e}")
            return "FREE"  # Safe default

    @staticmethod
    async def get_audio_retention_for_user(user_id: str, db_session: Optional[AsyncSession] = None) -> int:
        """
        Get audio retention period in hours for a user based on their tier.

        Args:
            user_id: User identifier
            db_session: Optional database session

        Returns:
            Retention period in hours
        """
        user_tier = await UserTierService.get_user_tier_by_user_id(user_id, db_session)
        return get_audio_retention_hours(user_tier)

    @staticmethod
    async def get_audio_retention_for_session(session_id: str, db_session: Optional[AsyncSession] = None) -> int:
        """
        Get audio retention period in hours for a session based on user tier.

        Args:
            session_id: Session identifier
            db_session: Optional database session

        Returns:
            Retention period in hours
        """
        user_tier = await UserTierService.get_user_tier_by_session_id(session_id, db_session)
        return get_audio_retention_hours(user_tier)

    @staticmethod
    async def get_user_tier_info(user_id: str, db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Get comprehensive tier information for a user.

        Args:
            user_id: User identifier
            db_session: Optional database session

        Returns:
            Dictionary containing tier information
        """
        user_tier = await UserTierService.get_user_tier_by_user_id(user_id, db_session)
        retention_hours = get_audio_retention_hours(user_tier)

        return {
            "user_id": user_id,
            "tier": user_tier,
            "audio_retention_hours": retention_hours,
            "audio_retention_days": retention_hours // 24,
            "is_anonymous": user_id == "anonymous" or not user_id,
            "tier_features": UserTierService._get_tier_features(user_tier)
        }

    @staticmethod
    def _get_tier_features(tier: str) -> Dict[str, Any]:
        """
        Get feature set for a given tier.

        Args:
            tier: User tier

        Returns:
            Dictionary of tier features
        """
        features = {
            "FREE": {
                "audio_retention_hours": 24,
                "max_sessions_per_day": 10,
                "max_audio_duration_minutes": 5,
                "analytics_access": False,
                "priority_support": False
            },
            "PRO": {
                "audio_retention_hours": 168,  # 7 days
                "max_sessions_per_day": 100,
                "max_audio_duration_minutes": 30,
                "analytics_access": True,
                "priority_support": False
            },
            "ENTERPRISE": {
                "audio_retention_hours": 720,  # 30 days
                "max_sessions_per_day": -1,  # Unlimited
                "max_audio_duration_minutes": -1,  # Unlimited
                "analytics_access": True,
                "priority_support": True
            }
        }

        return features.get(tier, features["FREE"])


# Convenience functions for common use cases
async def get_tier_for_user(user_id: str) -> str:
    """Convenience function to get user tier."""
    return await UserTierService.get_user_tier_by_user_id(user_id)


async def get_tier_for_session(session_id: str) -> str:
    """Convenience function to get tier for session."""
    return await UserTierService.get_user_tier_by_session_id(session_id)


async def get_retention_for_user(user_id: str) -> int:
    """Convenience function to get retention hours for user."""
    return await UserTierService.get_audio_retention_for_user(user_id)


async def get_retention_for_session(session_id: str) -> int:
    """Convenience function to get retention hours for session."""
    return await UserTierService.get_audio_retention_for_session(session_id)