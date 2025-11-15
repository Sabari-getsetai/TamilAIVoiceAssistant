"""Resilience Patterns for Microservice Communication

This module provides circuit breakers, retry mechanisms, timeout handling,
and other resilience patterns for robust microservice communication.
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
from contextlib import asynccontextmanager

from backend.utils.base_service import BaseService


logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, all calls rejected
    HALF_OPEN = "half_open" # Testing if service recovered


class RetryStrategy(Enum):
    """Retry strategy types"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTERED_BACKOFF = "jittered_backoff"


@dataclass
class ResilienceRetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout_ms: int = 60000    # Time before testing recovery
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout_ms: int = 5000              # Individual call timeout
    minimum_calls: int = 10             # Minimum calls before considering failure rate


@dataclass
class CallResult:
    """Result of a service call"""
    success: bool
    duration_ms: float
    error: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for service resilience"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.call_history: deque = deque(maxlen=100)
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker.{name}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self._check_state()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            await self._record_success()
        else:
            await self._record_failure(exc_val)

    async def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        await self._check_state()

        start_time = time.time()
        try:
            # Set timeout for the call
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_ms / 1000
            )

            duration_ms = (time.time() - start_time) * 1000
            await self._record_success(duration_ms)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            await self._record_failure(e, duration_ms)
            raise

    async def _check_state(self):
        """Check and potentially update circuit breaker state"""
        current_time = time.time() * 1000

        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_failure_time >= self.config.recovery_timeout_ms:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN for recovery test")
            else:
                raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is OPEN")

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # In half-open state, allow limited calls through
            pass

    async def _record_success(self, duration_ms: float = 0):
        """Record successful call"""
        call_result = CallResult(success=True, duration_ms=duration_ms)
        self.call_history.append(call_result)

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info(f"Circuit breaker {self.name} CLOSED after successful recovery")

        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)

    async def _record_failure(self, error: Exception, duration_ms: float = 0):
        """Record failed call"""
        call_result = CallResult(success=False, duration_ms=duration_ms, error=error)
        self.call_history.append(call_result)

        self.failure_count += 1
        self.last_failure_time = time.time() * 1000

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Failure during recovery test - back to open
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} OPEN - recovery test failed")

        elif self.state == CircuitBreakerState.CLOSED:
            # Check if we should open the circuit
            if self._should_open_circuit():
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker {self.name} OPEN - failure threshold exceeded")

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened"""
        if len(self.call_history) < self.config.minimum_calls:
            return False

        # Check failure threshold
        if self.failure_count >= self.config.failure_threshold:
            return True

        # Check failure rate in recent calls
        recent_calls = list(self.call_history)[-self.config.minimum_calls:]
        failure_rate = sum(1 for call in recent_calls if not call.success) / len(recent_calls)

        return failure_rate >= 0.5  # 50% failure rate

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        recent_calls = list(self.call_history)[-20:] if self.call_history else []

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": len(self.call_history),
            "recent_calls": len(recent_calls),
            "recent_success_rate": (
                sum(1 for call in recent_calls if call.success) / len(recent_calls)
                if recent_calls else 0
            ),
            "average_response_time": (
                statistics.mean([call.duration_ms for call in recent_calls])
                if recent_calls else 0
            )
        }


class RetryHandler:
    """Retry handler with various strategies"""

    def __init__(self, config: ResilienceRetryConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")

    async def execute(self, func: Callable[[], T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                self.logger.debug(f"Attempting call (attempt {attempt + 1}/{self.config.max_attempts})")
                result = await func(*args, **kwargs)

                if attempt > 0:
                    self.logger.info(f"Call succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_exception = e

                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    self.logger.info(f"Non-retryable exception: {type(e).__name__}")
                    raise

                # Don't wait after the last attempt
                if attempt < self.config.max_attempts - 1:
                    delay_ms = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Call failed (attempt {attempt + 1}): {str(e)}. "
                        f"Retrying in {delay_ms}ms"
                    )
                    await asyncio.sleep(delay_ms / 1000)

        # All retries exhausted
        self.logger.error(f"All {self.config.max_attempts} retry attempts failed")
        raise last_exception

    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)

    def _calculate_delay(self, attempt: int) -> int:
        """Calculate delay for retry attempt"""
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay_ms

        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay_ms * (self.config.backoff_factor ** attempt)

        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay_ms * (attempt + 1)

        elif self.config.strategy == RetryStrategy.JITTERED_BACKOFF:
            exponential_delay = self.config.base_delay_ms * (self.config.backoff_factor ** attempt)
            jitter = random.uniform(0.1, 0.9) if self.config.jitter else 1.0
            delay = int(exponential_delay * jitter)

        else:
            delay = self.config.base_delay_ms

        # Apply maximum delay limit
        return min(delay, self.config.max_delay_ms)


class BulkheadIsolation:
    """Bulkhead pattern for resource isolation"""

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_calls = 0
        self.total_calls = 0
        self.rejected_calls = 0
        self.logger = logging.getLogger(f"{__name__}.Bulkhead.{name}")

    @asynccontextmanager
    async def acquire(self, timeout: Optional[float] = None):
        """Acquire bulkhead resource"""
        try:
            if timeout:
                await asyncio.wait_for(self.semaphore.acquire(), timeout=timeout)
            else:
                await self.semaphore.acquire()

            self.active_calls += 1
            self.total_calls += 1

            try:
                yield
            finally:
                self.active_calls -= 1
                self.semaphore.release()

        except asyncio.TimeoutError:
            self.rejected_calls += 1
            self.logger.warning(f"Bulkhead {self.name} rejected call due to timeout")
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get bulkhead metrics"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active_calls": self.active_calls,
            "available_slots": self.max_concurrent - self.active_calls,
            "total_calls": self.total_calls,
            "rejected_calls": self.rejected_calls,
            "rejection_rate": (
                self.rejected_calls / self.total_calls if self.total_calls > 0 else 0
            )
        }


class ResilientServiceClient(BaseService):
    """Service client with comprehensive resilience patterns"""

    def __init__(self):
        super().__init__()
        self.service_name = "ResilientServiceClient"

        # Circuit breakers by service name
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Retry handlers by service name
        self._retry_handlers: Dict[str, RetryHandler] = {}

        # Bulkheads by service name
        self._bulkheads: Dict[str, BulkheadIsolation] = {}

        # Default configurations
        self._default_circuit_config = CircuitBreakerConfig()
        self._default_retry_config = ResilienceRetryConfig()

    def configure_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig):
        """Configure circuit breaker for a service"""
        self._circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        self.logger.info(f"Configured circuit breaker for service {service_name}")

    def configure_retry(self, service_name: str, config: ResilienceRetryConfig):
        """Configure retry handler for a service"""
        self._retry_handlers[service_name] = RetryHandler(config)
        self.logger.info(f"Configured retry handler for service {service_name}")

    def configure_bulkhead(self, service_name: str, max_concurrent: int):
        """Configure bulkhead for a service"""
        self._bulkheads[service_name] = BulkheadIsolation(service_name, max_concurrent)
        self.logger.info(f"Configured bulkhead for service {service_name} (max: {max_concurrent})")

    async def call_service(self,
                          service_name: str,
                          func: Callable[[], T],
                          *args,
                          use_circuit_breaker: bool = True,
                          use_retry: bool = True,
                          use_bulkhead: bool = True,
                          timeout: Optional[float] = None,
                          **kwargs) -> T:
        """Call service with resilience patterns"""

        # Get or create circuit breaker
        circuit_breaker = None
        if use_circuit_breaker:
            if service_name not in self._circuit_breakers:
                self._circuit_breakers[service_name] = CircuitBreaker(
                    service_name, self._default_circuit_config
                )
            circuit_breaker = self._circuit_breakers[service_name]

        # Get or create retry handler
        retry_handler = None
        if use_retry:
            if service_name not in self._retry_handlers:
                self._retry_handlers[service_name] = RetryHandler(self._default_retry_config)
            retry_handler = self._retry_handlers[service_name]

        # Get or create bulkhead
        bulkhead = None
        if use_bulkhead:
            if service_name not in self._bulkheads:
                self._bulkheads[service_name] = BulkheadIsolation(service_name)
            bulkhead = self._bulkheads[service_name]

        # Execute with patterns
        async def _execute():
            if circuit_breaker:
                return await circuit_breaker.call(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)

        async def _execute_with_retry():
            if retry_handler:
                return await retry_handler.execute(_execute)
            else:
                return await _execute()

        # Apply bulkhead if configured
        if bulkhead:
            async with bulkhead.acquire(timeout=timeout):
                return await _execute_with_retry()
        else:
            return await _execute_with_retry()

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive health information for a service"""
        health_info = {
            "service_name": service_name,
            "circuit_breaker": None,
            "bulkhead": None,
            "overall_status": "healthy"
        }

        # Circuit breaker metrics
        if service_name in self._circuit_breakers:
            cb_metrics = self._circuit_breakers[service_name].get_metrics()
            health_info["circuit_breaker"] = cb_metrics

            if cb_metrics["state"] != "closed":
                health_info["overall_status"] = "degraded"

        # Bulkhead metrics
        if service_name in self._bulkheads:
            bulkhead_metrics = self._bulkheads[service_name].get_metrics()
            health_info["bulkhead"] = bulkhead_metrics

            if bulkhead_metrics["rejection_rate"] > 0.1:  # 10% rejection rate
                health_info["overall_status"] = "degraded"

        return health_info

    async def reset_circuit_breaker(self, service_name: str) -> bool:
        """Manually reset circuit breaker for a service"""
        if service_name in self._circuit_breakers:
            cb = self._circuit_breakers[service_name]
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            cb.success_count = 0
            self.logger.info(f"Circuit breaker reset for service {service_name}")
            return True
        return False

    async def get_all_service_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all configured services"""
        metrics = {}

        all_services = set()
        all_services.update(self._circuit_breakers.keys())
        all_services.update(self._bulkheads.keys())

        for service_name in all_services:
            metrics[service_name] = await self.get_service_health(service_name)

        return metrics

    async def configure_service_defaults(self,
                                       circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                                       retry_config: Optional[ResilienceRetryConfig] = None):
        """Configure default resilience patterns"""
        if circuit_breaker_config:
            self._default_circuit_config = circuit_breaker_config

        if retry_config:
            self._default_retry_config = retry_config

        self.logger.info("Updated default resilience configurations")


# Global resilient service client
resilient_client = ResilientServiceClient()


def configure_resilience_defaults():
    """Configure default resilience patterns for common scenarios"""

    # Database service resilience
    db_circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout_ms=30000,  # 30 seconds
        success_threshold=2,
        timeout_ms=5000,
        minimum_calls=5
    )

    db_retry_config = ResilienceRetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay_ms=100,
        max_delay_ms=2000
    )

    resilient_client.configure_circuit_breaker("database", db_circuit_config)
    resilient_client.configure_retry("database", db_retry_config)
    resilient_client.configure_bulkhead("database", 20)

    # External API resilience
    api_circuit_config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout_ms=60000,  # 60 seconds
        success_threshold=3,
        timeout_ms=10000,
        minimum_calls=10
    )

    api_retry_config = ResilienceRetryConfig(
        max_attempts=4,
        strategy=RetryStrategy.JITTERED_BACKOFF,
        base_delay_ms=200,
        max_delay_ms=8000
    )

    resilient_client.configure_circuit_breaker("external_api", api_circuit_config)
    resilient_client.configure_retry("external_api", api_retry_config)
    resilient_client.configure_bulkhead("external_api", 10)

    # Redis service resilience
    redis_circuit_config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout_ms=15000,  # 15 seconds
        success_threshold=2,
        timeout_ms=3000,
        minimum_calls=3
    )

    redis_retry_config = ResilienceRetryConfig(
        max_attempts=2,
        strategy=RetryStrategy.FIXED_DELAY,
        base_delay_ms=50
    )

    resilient_client.configure_circuit_breaker("redis", redis_circuit_config)
    resilient_client.configure_retry("redis", redis_retry_config)
    resilient_client.configure_bulkhead("redis", 15)

    logger.info("Configured default resilience patterns")


# Auto-configure on import
try:
    configure_resilience_defaults()
except Exception as e:
    logger.warning(f"Failed to configure default resilience patterns: {str(e)}")


# Convenience decorators
def circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if config:
                resilient_client.configure_circuit_breaker(service_name, config)

            return await resilient_client.call_service(
                service_name=service_name,
                func=func,
                *args,
                use_retry=False,
                use_bulkhead=False,
                **kwargs
            )
        return wrapper
    return decorator


def retry(service_name: str, config: Optional[ResilienceRetryConfig] = None):
    """Decorator for retry logic"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if config:
                resilient_client.configure_retry(service_name, config)

            return await resilient_client.call_service(
                service_name=service_name,
                func=func,
                *args,
                use_circuit_breaker=False,
                use_bulkhead=False,
                **kwargs
            )
        return wrapper
    return decorator