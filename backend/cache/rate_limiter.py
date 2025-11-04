"""
Rate limiting utilities for Tamil AI Voice Assistant.

This module provides:
- Redis-based rate limiting
- User-specific rate limits
- API endpoint protection
- Login attempt limiting
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from .redis_client import get_redis_client, increment_counter

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Types of rate limits."""
    LOGIN_ATTEMPTS = "login_attempts"
    API_REQUESTS = "api_requests"
    DOCUMENT_UPLOADS = "document_uploads"
    AUDIO_UPLOADS = "audio_uploads"
    CHAT_MESSAGES = "chat_messages"


class RateLimiter:
    """Redis-based rate limiter for various operations."""

    def __init__(self):
        # Default rate limits (can be overridden by environment variables)
        self.rate_limits = {
            RateLimitType.LOGIN_ATTEMPTS: {"limit": 5, "window": 3600},  # 5 attempts per hour
            RateLimitType.API_REQUESTS: {"limit": 100, "window": 60},    # 100 requests per minute
            RateLimitType.DOCUMENT_UPLOADS: {"limit": 10, "window": 3600},  # 10 uploads per hour
            RateLimitType.AUDIO_UPLOADS: {"limit": 50, "window": 3600},  # 50 uploads per hour
            RateLimitType.CHAT_MESSAGES: {"limit": 30, "window": 60},    # 30 messages per minute
        }

    def _get_rate_limit_key(
        self,
        rate_type: RateLimitType,
        identifier: str,
        window_start: int
    ) -> str:
        """Generate Redis key for rate limit tracking."""
        return f"rate_limit:{rate_type}:{identifier}:{window_start}"

    def _get_current_window(self, window_seconds: int) -> int:
        """Get current time window for rate limiting."""
        return int(datetime.utcnow().timestamp()) // window_seconds

    async def check_rate_limit(
        self,
        rate_type: RateLimitType,
        identifier: str,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if identifier is within rate limit.

        Args:
            rate_type: Type of rate limit to check
            identifier: Unique identifier (user_id, IP address, etc.)
            custom_limit: Override default limit
            custom_window: Override default window (seconds)

        Returns:
            dict: Rate limit status with keys:
                - allowed: bool - Whether the request is allowed
                - current_count: int - Current request count
                - limit: int - Rate limit
                - reset_time: int - Unix timestamp when limit resets
                - remaining: int - Remaining requests
        """
        try:
            # Get rate limit configuration
            config = self.rate_limits.get(rate_type, {"limit": 10, "window": 60})
            limit = custom_limit or config["limit"]
            window = custom_window or config["window"]

            # Calculate current window
            current_window = self._get_current_window(window)
            rate_key = self._get_rate_limit_key(rate_type, identifier, current_window)

            # Get current count
            client = await get_redis_client()
            current_count = await client.get(rate_key)
            current_count = int(current_count) if current_count else 0

            # Calculate reset time
            reset_time = (current_window + 1) * window

            # Check if limit exceeded
            allowed = current_count < limit
            remaining = max(0, limit - current_count)

            result = {
                "allowed": allowed,
                "current_count": current_count,
                "limit": limit,
                "reset_time": reset_time,
                "remaining": remaining,
                "rate_type": rate_type,
                "identifier": identifier
            }

            logger.debug(f"Rate limit check for {rate_type}:{identifier} - {result}")
            return result

        except Exception as e:
            logger.error(f"Error checking rate limit for {rate_type}:{identifier}: {e}")
            # On error, allow the request but log the issue
            return {
                "allowed": True,
                "current_count": 0,
                "limit": 999999,
                "reset_time": int(datetime.utcnow().timestamp()) + 3600,
                "remaining": 999999,
                "error": str(e)
            }

    async def increment_rate_limit(
        self,
        rate_type: RateLimitType,
        identifier: str,
        amount: int = 1,
        custom_window: Optional[int] = None
    ) -> int:
        """
        Increment rate limit counter.

        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier
            amount: Amount to increment by
            custom_window: Override default window (seconds)

        Returns:
            int: New count value
        """
        try:
            # Get window configuration
            config = self.rate_limits.get(rate_type, {"window": 60})
            window = custom_window or config["window"]

            # Calculate current window
            current_window = self._get_current_window(window)
            rate_key = self._get_rate_limit_key(rate_type, identifier, current_window)

            # Increment counter with expiration
            new_count = await increment_counter(rate_key, amount, window)

            logger.debug(f"Incremented rate limit {rate_type}:{identifier} to {new_count}")
            return new_count or amount

        except Exception as e:
            logger.error(f"Error incrementing rate limit for {rate_type}:{identifier}: {e}")
            return 0

    async def reset_rate_limit(
        self,
        rate_type: RateLimitType,
        identifier: str
    ) -> bool:
        """
        Reset rate limit for an identifier.

        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get window configuration
            config = self.rate_limits.get(rate_type, {"window": 60})
            window = config["window"]

            # Calculate current window
            current_window = self._get_current_window(window)
            rate_key = self._get_rate_limit_key(rate_type, identifier, current_window)

            # Delete the key
            client = await get_redis_client()
            result = await client.delete(rate_key)

            logger.info(f"Reset rate limit for {rate_type}:{identifier}")
            return bool(result)

        except Exception as e:
            logger.error(f"Error resetting rate limit for {rate_type}:{identifier}: {e}")
            return False

    async def check_and_increment(
        self,
        rate_type: RateLimitType,
        identifier: str,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check rate limit and increment if allowed.

        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier
            custom_limit: Override default limit
            custom_window: Override default window (seconds)

        Returns:
            dict: Rate limit status (same as check_rate_limit)
        """
        # Check current status
        status = await self.check_rate_limit(
            rate_type, identifier, custom_limit, custom_window
        )

        # If allowed, increment the counter
        if status["allowed"]:
            new_count = await self.increment_rate_limit(
                rate_type, identifier, 1, custom_window
            )
            status["current_count"] = new_count
            status["remaining"] = max(0, status["limit"] - new_count)

        return status

    async def get_rate_limit_status(
        self,
        rate_type: RateLimitType,
        identifier: str
    ) -> Dict[str, Any]:
        """
        Get current rate limit status without incrementing.

        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier

        Returns:
            dict: Current rate limit status
        """
        return await self.check_rate_limit(rate_type, identifier)

    async def is_rate_limited(
        self,
        rate_type: RateLimitType,
        identifier: str,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> bool:
        """
        Check if identifier is currently rate limited.

        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier
            custom_limit: Override default limit
            custom_window: Override default window (seconds)

        Returns:
            bool: True if rate limited, False if allowed
        """
        status = await self.check_rate_limit(
            rate_type, identifier, custom_limit, custom_window
        )
        return not status["allowed"]

    def configure_rate_limit(
        self,
        rate_type: RateLimitType,
        limit: int,
        window_seconds: int
    ):
        """
        Configure rate limit for a specific type.

        Args:
            rate_type: Type of rate limit
            limit: Number of allowed requests
            window_seconds: Time window in seconds
        """
        self.rate_limits[rate_type] = {
            "limit": limit,
            "window": window_seconds
        }
        logger.info(f"Configured rate limit {rate_type}: {limit} requests per {window_seconds} seconds")

    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired rate limit keys.

        Returns:
            int: Number of keys cleaned up
        """
        try:
            client = await get_redis_client()

            # Get all rate limit keys
            pattern = "rate_limit:*"
            keys = await client.keys(pattern)

            cleaned_count = 0
            current_time = int(datetime.utcnow().timestamp())

            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                # Extract window from key
                try:
                    parts = key.split(':')
                    if len(parts) >= 4:
                        window_start = int(parts[-1])
                        rate_type = parts[1]

                        # Get window duration
                        config = self.rate_limits.get(rate_type, {"window": 60})
                        window_duration = config["window"]

                        # Check if window has expired
                        if current_time > (window_start + 1) * window_duration:
                            await client.delete(key)
                            cleaned_count += 1

                except (ValueError, IndexError):
                    # Skip malformed keys
                    continue

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired rate limit keys")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up rate limit keys: {e}")
            return 0