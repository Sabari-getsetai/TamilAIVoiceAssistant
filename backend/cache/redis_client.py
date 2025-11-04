"""
Redis client configuration and utilities for Tamil AI Voice Assistant.

This module provides:
- Redis connection management
- Connection pooling
- Health checking
- Error handling for Redis operations
"""

import os
import logging
from typing import Optional, Any, Union
import json
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, RedisError

logger = logging.getLogger(__name__)

# Redis configuration from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://:tamil_redis_password_dev@localhost:6379/0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "tamil_redis_password_dev")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "7200"))  # 2 hours default

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None
_connection_pool: Optional[ConnectionPool] = None


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client instance with connection pooling.

    Returns:
        redis.Redis: Configured Redis client

    Raises:
        ConnectionError: If unable to connect to Redis server
    """
    global _redis_client, _connection_pool

    if _redis_client is None:
        try:
            # Create connection pool
            _connection_pool = ConnectionPool.from_url(
                REDIS_URL,
                max_connections=REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )

            # Create Redis client
            _redis_client = redis.Redis(connection_pool=_connection_pool)

            # Test connection
            await _redis_client.ping()
            logger.info("Redis client connected successfully")

        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Cannot connect to Redis server: {e}")

    return _redis_client


async def init_redis():
    """
    Initialize Redis connection and perform setup tasks.

    This function:
    1. Establishes Redis connection
    2. Tests connectivity
    3. Sets up any required Redis configurations
    """
    try:
        client = await get_redis_client()

        # Test connection
        pong = await client.ping()
        if pong:
            logger.info("Redis initialization successful")
        else:
            raise ConnectionError("Redis ping failed")

        # Set up any required configurations
        # For example, configure memory usage policies
        try:
            await client.config_set("maxmemory-policy", "allkeys-lru")
            logger.info("Redis memory policy configured")
        except RedisError:
            logger.warning("Could not configure Redis memory policy (may not have permission)")

    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        raise


async def close_redis():
    """
    Close Redis connections.
    This should be called on application shutdown.
    """
    global _redis_client, _connection_pool

    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")

    if _connection_pool:
        try:
            await _connection_pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")

    _redis_client = None
    _connection_pool = None


async def check_redis_health() -> bool:
    """
    Check if Redis server is healthy and accessible.

    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client = await get_redis_client()
        pong = await client.ping()
        logger.debug("Redis health check passed")
        return bool(pong)

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Utility functions for common Redis operations

async def set_value(
    key: str,
    value: Any,
    expire: Optional[Union[int, timedelta]] = None,
    json_encode: bool = True
) -> bool:
    """
    Set a value in Redis with optional expiration.

    Args:
        key: Redis key
        value: Value to store
        expire: Expiration time (seconds or timedelta)
        json_encode: Whether to JSON encode the value

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = await get_redis_client()

        # Encode value if needed
        if json_encode and not isinstance(value, (str, bytes)):
            value = json.dumps(value)

        # Set value with optional expiration
        result = await client.set(key, value, ex=expire)
        return bool(result)

    except Exception as e:
        logger.error(f"Error setting Redis key {key}: {e}")
        return False


async def get_value(
    key: str,
    json_decode: bool = True,
    default: Any = None
) -> Any:
    """
    Get a value from Redis.

    Args:
        key: Redis key
        json_decode: Whether to JSON decode the value
        default: Default value if key doesn't exist

    Returns:
        Any: Retrieved value or default
    """
    try:
        client = await get_redis_client()
        value = await client.get(key)

        if value is None:
            return default

        # Decode value if needed
        if json_decode and isinstance(value, bytes):
            try:
                return json.loads(value.decode('utf-8'))
            except json.JSONDecodeError:
                # Return as string if JSON decode fails
                return value.decode('utf-8')

        return value.decode('utf-8') if isinstance(value, bytes) else value

    except Exception as e:
        logger.error(f"Error getting Redis key {key}: {e}")
        return default


async def delete_key(key: str) -> bool:
    """
    Delete a key from Redis.

    Args:
        key: Redis key to delete

    Returns:
        bool: True if key was deleted, False otherwise
    """
    try:
        client = await get_redis_client()
        result = await client.delete(key)
        return bool(result)

    except Exception as e:
        logger.error(f"Error deleting Redis key {key}: {e}")
        return False


async def exists_key(key: str) -> bool:
    """
    Check if a key exists in Redis.

    Args:
        key: Redis key to check

    Returns:
        bool: True if key exists, False otherwise
    """
    try:
        client = await get_redis_client()
        result = await client.exists(key)
        return bool(result)

    except Exception as e:
        logger.error(f"Error checking Redis key {key}: {e}")
        return False


async def increment_counter(
    key: str,
    amount: int = 1,
    expire: Optional[int] = None
) -> Optional[int]:
    """
    Increment a counter in Redis.

    Args:
        key: Redis key for the counter
        amount: Amount to increment by
        expire: Optional expiration time in seconds

    Returns:
        int: New counter value or None if failed
    """
    try:
        client = await get_redis_client()

        # Use pipeline for atomic operations
        async with client.pipeline() as pipe:
            await pipe.incrby(key, amount)
            if expire:
                await pipe.expire(key, expire)
            results = await pipe.execute()

        return results[0]  # The incremented value

    except Exception as e:
        logger.error(f"Error incrementing Redis counter {key}: {e}")
        return None


async def set_hash(key: str, mapping: dict, expire: Optional[int] = None) -> bool:
    """
    Set hash fields in Redis.

    Args:
        key: Redis key for the hash
        mapping: Dictionary of field-value pairs
        expire: Optional expiration time in seconds

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = await get_redis_client()

        # Convert values to strings and handle JSON encoding
        processed_mapping = {}
        for field, value in mapping.items():
            if isinstance(value, (dict, list)):
                processed_mapping[field] = json.dumps(value)
            else:
                processed_mapping[field] = str(value)

        # Set hash fields
        result = await client.hset(key, mapping=processed_mapping)

        # Set expiration if specified
        if expire:
            await client.expire(key, expire)

        return True

    except Exception as e:
        logger.error(f"Error setting Redis hash {key}: {e}")
        return False


async def get_hash(key: str, fields: Optional[list] = None) -> dict:
    """
    Get hash fields from Redis.

    Args:
        key: Redis key for the hash
        fields: Optional list of specific fields to get

    Returns:
        dict: Hash data with JSON decoded values where applicable
    """
    try:
        client = await get_redis_client()

        if fields:
            values = await client.hmget(key, fields)
            result = dict(zip(fields, values))
        else:
            result = await client.hgetall(key)

        # Decode values
        decoded_result = {}
        for field, value in result.items():
            if value is None:
                decoded_result[field] = None
                continue

            # Decode bytes
            if isinstance(value, bytes):
                value = value.decode('utf-8')

            # Try JSON decode
            try:
                decoded_result[field] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                decoded_result[field] = value

        return decoded_result

    except Exception as e:
        logger.error(f"Error getting Redis hash {key}: {e}")
        return {}