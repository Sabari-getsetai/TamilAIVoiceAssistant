"""
Utils Package - Shared Utilities

This package contains utility functions and classes that are used
across multiple modules and services.

Utilities:
- base_service: Common service patterns and lifecycle management
- service_registry: Dependency injection and service discovery
- validation: Input validation helpers (planned)
- formatters: Data formatting utilities (planned)
- decorators: Common decorators for logging, retry, etc. (planned)
- constants: Shared constants and enums (planned)
"""

from .base_service import BaseService, MicroserviceInterface
from .service_registry import ServiceRegistry, get_service_registry, get_service

__all__ = [
    "BaseService",
    "MicroserviceInterface",
    "ServiceRegistry",
    "get_service_registry",
    "get_service"
]