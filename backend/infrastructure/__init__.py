"""
Infrastructure utilities for Tamil AI Voice Assistant.

This package provides comprehensive microservice infrastructure:

**Legacy Components:**
- Retry mechanisms with exponential backoff
- Service health monitoring
- Docker service integration utilities
- Connection resilience patterns

**Microservice Architecture (Phase 5):**
- Service Discovery: Dynamic service registration and discovery
- Health Monitoring: Comprehensive health checks and reporting
- Dependency Injection: Full DI container with lifecycle management
- Resilience Patterns: Circuit breakers, retries, bulkheads, timeouts
"""

# Legacy infrastructure (backward compatibility)
from .retry import RetryManager, retry_with_backoff, wait_for_service, RetryConfig
from .health import ServiceMonitor, HealthChecker, get_service_health, monitor_services

# Microservice infrastructure (Phase 5)
from .service_discovery import (
    ServiceRegistry, ServiceInfo, ServiceStatus, ServiceClient,
    service_registry, service_client
)

from .health_monitor import (
    ServiceHealthMonitor, HealthChecker as NewHealthChecker,
    HealthReport, HealthMetric, HealthLevel, HealthCheckType,
    create_health_monitor
)

from .dependency_injection import (
    DIContainer, ServiceScope, ServiceProvider, ScopedServiceProvider,
    Injectable, ServiceLifetime, ServiceDescriptor,
    DependencyResolutionError, CircularDependencyError,
    injectable, container, service_provider, get_container,
    configure_default_services
)

from .resilience import (
    CircuitBreaker, RetryHandler, BulkheadIsolation, ResilientServiceClient,
    CircuitBreakerState, RetryStrategy, CircuitBreakerConfig, ResilienceRetryConfig,
    CircuitBreakerOpenException, resilient_client,
    circuit_breaker, retry
)

__all__ = [
    # Legacy infrastructure (backward compatibility)
    "RetryManager",
    "retry_with_backoff",
    "wait_for_service",
    "RetryConfig",
    "ServiceMonitor",
    "HealthChecker",
    "get_service_health",
    "monitor_services",

    # Service Discovery
    "ServiceRegistry",
    "ServiceInfo",
    "ServiceStatus",
    "ServiceClient",
    "service_registry",
    "service_client",

    # Health Monitoring
    "ServiceHealthMonitor",
    "NewHealthChecker",
    "HealthReport",
    "HealthMetric",
    "HealthLevel",
    "HealthCheckType",
    "create_health_monitor",

    # Dependency Injection
    "DIContainer",
    "ServiceScope",
    "ServiceProvider",
    "ScopedServiceProvider",
    "Injectable",
    "ServiceLifetime",
    "ServiceDescriptor",
    "DependencyResolutionError",
    "CircularDependencyError",
    "injectable",
    "container",
    "service_provider",
    "get_container",
    "configure_default_services",

    # Resilience Patterns
    "CircuitBreaker",
    "RetryHandler",
    "BulkheadIsolation",
    "ResilientServiceClient",
    "CircuitBreakerState",
    "RetryStrategy",
    "CircuitBreakerConfig",
    "ResilienceRetryConfig",
    "CircuitBreakerOpenException",
    "resilient_client",
    "circuit_breaker",
    "retry",
]
