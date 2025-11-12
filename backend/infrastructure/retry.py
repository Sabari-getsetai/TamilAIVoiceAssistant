"""
Retry mechanisms with exponential backoff for Tamil AI Voice Assistant.

This module provides:
- Generic retry mechanism with configurable backoff strategies
- Service availability waiting with timeout
- Exponential backoff with jitter
- Connection resilience patterns
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_retries: int = 5
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    timeout: Optional[float] = None


class RetryManager:
    """Manages retry logic with configurable backoff strategies."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry manager.
        
        Args:
            config: Retry configuration, uses defaults if None
        """
        self.config = config or RetryConfig()
        self.attempt_count = 0
        self.start_time = None
    
    def reset(self):
        """Reset retry state for new operation."""
        self.attempt_count = 0
        self.start_time = None
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            exception: Exception that occurred
            
        Returns:
            bool: True if should retry, False otherwise
        """
        if self.attempt_count >= self.config.max_retries:
            return False
        
        if self.config.timeout and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.config.timeout:
                return False
        
        # Don't retry certain types of exceptions
        non_retryable = (
            ValueError,
            TypeError,
            AttributeError,
        )
        
        if isinstance(exception, non_retryable):
            return False
        
        return True
    
    def get_delay(self) -> float:
        """
        Calculate delay for next retry attempt.
        
        Returns:
            float: Delay in seconds
        """
        if self.attempt_count == 0:
            delay = self.config.initial_delay
        else:
            delay = min(
                self.config.initial_delay * (self.config.exponential_base ** (self.attempt_count - 1)),
                self.config.max_delay
            )
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "operation"
    ) -> T:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Async function to execute
            operation_name: Name for logging purposes
            
        Returns:
            T: Result of successful operation
            
        Raises:
            Exception: Last exception if all retries failed
        """
        self.reset()
        self.start_time = time.time()
        last_exception = None
        
        while True:
            try:
                self.attempt_count += 1
                logger.debug(f"Attempting {operation_name} (attempt {self.attempt_count}/{self.config.max_retries + 1})")
                
                result = await operation()
                
                if self.attempt_count > 1:
                    logger.info(f"{operation_name} succeeded after {self.attempt_count} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e):
                    logger.error(f"{operation_name} failed after {self.attempt_count} attempts: {e}")
                    raise e
                
                delay = self.get_delay()
                logger.warning(f"{operation_name} failed (attempt {self.attempt_count}), retrying in {delay:.2f}s: {e}")
                
                await asyncio.sleep(delay)


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation"
) -> T:
    """
    Execute operation with retry and exponential backoff.
    
    Args:
        operation: Async function to execute
        config: Retry configuration
        operation_name: Name for logging purposes
        
    Returns:
        T: Result of successful operation
        
    Raises:
        Exception: Last exception if all retries failed
    """
    retry_manager = RetryManager(config)
    return await retry_manager.execute(operation, operation_name)


async def wait_for_service(
    health_check: Callable[[], Awaitable[bool]],
    service_name: str,
    timeout: float = 60.0,
    check_interval: float = 2.0
) -> bool:
    """
    Wait for service to become available.
    
    Args:
        health_check: Async function that returns True if service is healthy
        service_name: Name of service for logging
        timeout: Maximum time to wait in seconds
        check_interval: Time between health checks in seconds
        
    Returns:
        bool: True if service became available, False if timeout
    """
    start_time = time.time()
    attempt = 0
    
    logger.info(f"Waiting for {service_name} to become available (timeout: {timeout}s)")
    
    while True:
        attempt += 1
        elapsed = time.time() - start_time
        
        if elapsed >= timeout:
            logger.error(f"Timeout waiting for {service_name} after {elapsed:.1f}s ({attempt} attempts)")
            return False
        
        try:
            if await health_check():
                logger.info(f"{service_name} is available after {elapsed:.1f}s ({attempt} attempts)")
                return True
                
        except Exception as e:
            logger.debug(f"{service_name} health check failed (attempt {attempt}): {e}")
        
        # Calculate remaining time and adjust sleep if needed
        remaining_time = timeout - elapsed
        sleep_time = min(check_interval, remaining_time)
        
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)


async def wait_for_multiple_services(
    services: dict[str, Callable[[], Awaitable[bool]]],
    timeout: float = 120.0,
    check_interval: float = 2.0
) -> dict[str, bool]:
    """
    Wait for multiple services to become available.
    
    Args:
        services: Dict mapping service names to health check functions
        timeout: Maximum time to wait in seconds
        check_interval: Time between health checks in seconds
        
    Returns:
        dict: Mapping of service names to availability status
    """
    logger.info(f"Waiting for {len(services)} services to become available")
    
    # Run all service waits concurrently
    tasks = {
        name: wait_for_service(health_check, name, timeout, check_interval)
        for name, health_check in services.items()
    }
    
    results = {}
    for name, task in tasks.items():
        try:
            results[name] = await task
        except Exception as e:
            logger.error(f"Error waiting for {name}: {e}")
            results[name] = False
    
    available_count = sum(results.values())
    logger.info(f"{available_count}/{len(services)} services are available")
    
    return results


class ConnectionPool:
    """Manages connection pooling with retry logic."""
    
    def __init__(
        self,
        create_connection: Callable[[], Awaitable[Any]],
        test_connection: Callable[[Any], Awaitable[bool]],
        close_connection: Callable[[Any], Awaitable[None]],
        max_connections: int = 10,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize connection pool.
        
        Args:
            create_connection: Function to create new connection
            test_connection: Function to test if connection is valid
            close_connection: Function to close connection
            max_connections: Maximum number of connections in pool
            retry_config: Retry configuration for connection operations
        """
        self.create_connection = create_connection
        self.test_connection = test_connection
        self.close_connection = close_connection
        self.max_connections = max_connections
        self.retry_config = retry_config or RetryConfig()
        
        self._pool: list[Any] = []
        self._lock = asyncio.Lock()
    
    async def get_connection(self) -> Any:
        """
        Get connection from pool or create new one.
        
        Returns:
            Connection object
        """
        async with self._lock:
            # Try to get existing connection from pool
            while self._pool:
                conn = self._pool.pop()
                try:
                    if await self.test_connection(conn):
                        return conn
                    else:
                        await self.close_connection(conn)
                except Exception:
                    try:
                        await self.close_connection(conn)
                    except Exception:
                        pass
            
            # Create new connection with retry
            return await retry_with_backoff(
                self.create_connection,
                self.retry_config,
                "create_connection"
            )
    
    async def return_connection(self, conn: Any):
        """
        Return connection to pool.
        
        Args:
            conn: Connection to return
        """
        async with self._lock:
            if len(self._pool) < self.max_connections:
                try:
                    if await self.test_connection(conn):
                        self._pool.append(conn)
                        return
                except Exception:
                    pass
            
            # Close connection if pool is full or connection is invalid
            try:
                await self.close_connection(conn)
            except Exception:
                pass
    
    async def close_all(self):
        """Close all connections in pool."""
        async with self._lock:
            while self._pool:
                conn = self._pool.pop()
                try:
                    await self.close_connection(conn)
                except Exception:
                    pass
