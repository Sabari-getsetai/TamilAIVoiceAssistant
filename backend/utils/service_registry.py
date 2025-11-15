"""
Service Registry - Dependency Injection and Service Discovery

This module provides a service registry for managing service dependencies
and enabling dependency injection patterns. Essential for microservice
architecture.
"""

from typing import Dict, Any, Optional, Type, TypeVar, List, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ServiceLifecycle(Enum):
    """Service lifecycle states."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes a service registration."""
    service_type: Type
    implementation_type: Type
    lifecycle: ServiceLifecycle
    factory_func: Optional[Callable] = None
    dependencies: Optional[List[str]] = None
    initialized: bool = False
    instance: Optional[Any] = None


class ServiceRegistry:
    """
    Service registry for dependency injection and service discovery.

    This registry manages service instances, their dependencies,
    and lifecycle. Designed for microservice architecture.
    """

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._initialization_order: List[str] = []

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory_func: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[str]] = None
    ) -> 'ServiceRegistry':
        """
        Register a singleton service.

        Args:
            service_type: The service interface/type
            implementation_type: The concrete implementation type
            factory_func: Optional factory function to create the service
            dependencies: List of service names this service depends on

        Returns:
            Self for method chaining
        """
        service_name = service_type.__name__
        impl_type = implementation_type or service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifecycle=ServiceLifecycle.SINGLETON,
            factory_func=factory_func,
            dependencies=dependencies or []
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered singleton service: {service_name}")
        return self

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory_func: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[str]] = None
    ) -> 'ServiceRegistry':
        """
        Register a transient service (new instance every time).

        Args:
            service_type: The service interface/type
            implementation_type: The concrete implementation type
            factory_func: Optional factory function to create the service
            dependencies: List of service names this service depends on

        Returns:
            Self for method chaining
        """
        service_name = service_type.__name__
        impl_type = implementation_type or service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifecycle=ServiceLifecycle.TRANSIENT,
            factory_func=factory_func,
            dependencies=dependencies or []
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered transient service: {service_name}")
        return self

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory_func: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[str]] = None
    ) -> 'ServiceRegistry':
        """
        Register a scoped service (one instance per scope).

        Args:
            service_type: The service interface/type
            implementation_type: The concrete implementation type
            factory_func: Optional factory function to create the service
            dependencies: List of service names this service depends on

        Returns:
            Self for method chaining
        """
        service_name = service_type.__name__
        impl_type = implementation_type or service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifecycle=ServiceLifecycle.SCOPED,
            factory_func=factory_func,
            dependencies=dependencies or []
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered scoped service: {service_name}")
        return self

    def get_service(self, service_type: Type[T], scope: Optional[str] = None) -> T:
        """
        Get a service instance.

        Args:
            service_type: The service type to retrieve
            scope: Optional scope identifier for scoped services

        Returns:
            Service instance

        Raises:
            ValueError: If service is not registered
            RuntimeError: If circular dependencies are detected
        """
        service_name = service_type.__name__

        if service_name not in self._services:
            raise ValueError(f"Service {service_name} is not registered")

        descriptor = self._services[service_name]

        # Handle different lifecycles
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            return self._get_singleton_instance(service_name, descriptor)

        elif descriptor.lifecycle == ServiceLifecycle.TRANSIENT:
            return self._create_instance(service_name, descriptor)

        elif descriptor.lifecycle == ServiceLifecycle.SCOPED:
            if scope is None:
                raise ValueError(f"Scoped service {service_name} requires a scope identifier")
            return self._get_scoped_instance(service_name, descriptor, scope)

    def _get_singleton_instance(self, service_name: str, descriptor: ServiceDescriptor):
        """Get or create a singleton instance."""
        if service_name not in self._instances:
            self._instances[service_name] = self._create_instance(service_name, descriptor)
        return self._instances[service_name]

    def _get_scoped_instance(self, service_name: str, descriptor: ServiceDescriptor, scope: str):
        """Get or create a scoped instance."""
        if scope not in self._scoped_instances:
            self._scoped_instances[scope] = {}

        if service_name not in self._scoped_instances[scope]:
            self._scoped_instances[scope][service_name] = self._create_instance(service_name, descriptor)

        return self._scoped_instances[scope][service_name]

    def _create_instance(self, service_name: str, descriptor: ServiceDescriptor):
        """Create a new instance of a service."""
        try:
            # Resolve dependencies first
            dependencies = self._resolve_dependencies(descriptor.dependencies)

            # Create instance
            if descriptor.factory_func:
                instance = descriptor.factory_func(**dependencies)
            else:
                if dependencies:
                    # If there are dependencies, pass them as constructor arguments
                    instance = descriptor.implementation_type(**dependencies)
                else:
                    instance = descriptor.implementation_type()

            logger.debug(f"Created instance of service: {service_name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to create instance of service {service_name}: {e}")
            raise

    def _resolve_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """
        Resolve service dependencies.

        Args:
            dependencies: List of dependency service names

        Returns:
            Dictionary mapping dependency names to their instances
        """
        resolved = {}

        for dep_name in dependencies:
            if dep_name not in self._services:
                raise ValueError(f"Dependency {dep_name} is not registered")

            # Get the service type for the dependency
            dep_descriptor = self._services[dep_name]
            dep_instance = self.get_service(dep_descriptor.service_type)
            resolved[dep_name.lower()] = dep_instance

        return resolved

    async def initialize_all_services(self):
        """
        Initialize all registered services in dependency order.
        """
        # Calculate initialization order based on dependencies
        order = self._calculate_initialization_order()

        for service_name in order:
            descriptor = self._services[service_name]

            # Initialize singleton services
            if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
                instance = self._get_singleton_instance(service_name, descriptor)

                # Call initialize method if it exists
                if hasattr(instance, 'initialize'):
                    await instance.initialize()

                descriptor.initialized = True
                logger.info(f"Initialized service: {service_name}")

    def _calculate_initialization_order(self) -> List[str]:
        """
        Calculate the order in which services should be initialized
        based on their dependencies.

        Returns:
            List of service names in initialization order

        Raises:
            RuntimeError: If circular dependencies are detected
        """
        # Topological sort to handle dependencies
        visited = set()
        temp_visited = set()
        order = []

        def visit(service_name: str):
            if service_name in temp_visited:
                raise RuntimeError(f"Circular dependency detected involving {service_name}")

            if service_name in visited:
                return

            temp_visited.add(service_name)

            # Visit dependencies first
            if service_name in self._services:
                for dep in self._services[service_name].dependencies:
                    visit(dep)

            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)

        # Visit all services
        for service_name in self._services.keys():
            if service_name not in visited:
                visit(service_name)

        return order

    async def shutdown_all_services(self):
        """
        Shutdown all services in reverse initialization order.
        """
        # Shutdown in reverse order
        for service_name in reversed(self._initialization_order):
            if service_name in self._instances:
                instance = self._instances[service_name]

                # Call shutdown method if it exists
                if hasattr(instance, 'shutdown'):
                    try:
                        await instance.shutdown()
                        logger.info(f"Shutdown service: {service_name}")
                    except Exception as e:
                        logger.error(f"Error shutting down service {service_name}: {e}")

    def clear_scope(self, scope: str):
        """
        Clear all scoped instances for a given scope.

        Args:
            scope: The scope identifier to clear
        """
        if scope in self._scoped_instances:
            del self._scoped_instances[scope]
            logger.debug(f"Cleared scoped instances for scope: {scope}")

    def get_service_health(self) -> Dict[str, Any]:
        """
        Get health status of all registered services.

        Returns:
            Dictionary containing health information for all services
        """
        health_info = {
            "registry_status": "healthy",
            "total_services": len(self._services),
            "initialized_services": sum(1 for desc in self._services.values() if desc.initialized),
            "services": {}
        }

        for service_name, descriptor in self._services.items():
            service_health = {
                "registered": True,
                "initialized": descriptor.initialized,
                "lifecycle": descriptor.lifecycle.value,
                "has_dependencies": len(descriptor.dependencies) > 0
            }

            # Try to get health from service if it has a health_check method
            if descriptor.initialized and service_name in self._instances:
                instance = self._instances[service_name]
                if hasattr(instance, 'health_check'):
                    try:
                        # Note: This would need to be made async for real health checks
                        service_health["instance_healthy"] = instance.is_healthy if hasattr(instance, 'is_healthy') else True
                    except Exception as e:
                        service_health["health_error"] = str(e)

            health_info["services"][service_name] = service_health

        return health_info


# Global service registry instance
_global_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return _global_registry


def get_service(service_type: Type[T], scope: Optional[str] = None) -> T:
    """Convenience function to get a service from the global registry."""
    return _global_registry.get_service(service_type, scope)