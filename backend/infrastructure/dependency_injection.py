"""Dependency Injection Container

This module provides a comprehensive dependency injection system for microservice architecture,
enabling loose coupling, testability, and flexible service composition.
"""

import inspect
import logging
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Generic,
    Callable, Protocol, runtime_checkable, get_type_hints
)
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
import asyncio
from contextlib import asynccontextmanager

from backend.utils.base_service import BaseService


logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options"""
    SINGLETON = "singleton"      # Single instance for entire application
    TRANSIENT = "transient"      # New instance every time
    SCOPED = "scoped"           # Single instance per scope/request
    FACTORY = "factory"         # Use factory function


@runtime_checkable
class Injectable(Protocol):
    """Protocol for injectable services"""
    pass


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

        # If no implementation type specified, use service type
        if self.implementation_type is None:
            self.implementation_type = self.service_type


class DependencyResolutionError(Exception):
    """Raised when dependency resolution fails"""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Raised when circular dependencies are detected"""
    pass


class ServiceScope:
    """Manages scoped service instances"""

    def __init__(self, container: 'DIContainer'):
        self.container = container
        self._scoped_instances: Dict[Type, Any] = {}

    def get_scoped_instance(self, service_type: Type) -> Any:
        """Get or create scoped instance"""
        if service_type not in self._scoped_instances:
            descriptor = self.container._get_service_descriptor(service_type)
            instance = self.container._create_instance(descriptor, scope=self)
            self._scoped_instances[service_type] = instance

        return self._scoped_instances[service_type]

    async def dispose(self):
        """Dispose of all scoped instances"""
        for instance in self._scoped_instances.values():
            if hasattr(instance, 'dispose') and callable(instance.dispose):
                if asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
                else:
                    instance.dispose()

        self._scoped_instances.clear()


class DIContainer:
    """Dependency Injection Container for managing service dependencies"""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._resolution_stack: List[Type] = []
        self.logger = logging.getLogger(f"{__name__}.DIContainer")

    def register_singleton(self,
                          service_type: Type[T],
                          implementation_type: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None,
                          instance: Optional[T] = None) -> 'DIContainer':
        """Register a singleton service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )

    def register_transient(self,
                          service_type: Type[T],
                          implementation_type: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None) -> 'DIContainer':
        """Register a transient service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )

    def register_scoped(self,
                       service_type: Type[T],
                       implementation_type: Optional[Type[T]] = None,
                       factory: Optional[Callable[[], T]] = None) -> 'DIContainer':
        """Register a scoped service"""
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )

    def register_factory(self,
                        service_type: Type[T],
                        factory: Callable[[], T]) -> 'DIContainer':
        """Register a factory function for creating services"""
        return self._register_service(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.FACTORY
        )

    def _register_service(self,
                         service_type: Type,
                         implementation_type: Optional[Type] = None,
                         factory: Optional[Callable] = None,
                         instance: Optional[Any] = None,
                         lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DIContainer':
        """Internal service registration method"""

        # Validate registration
        if instance is not None and lifetime != ServiceLifetime.SINGLETON:
            raise ValueError("Instance registration is only allowed for singleton services")

        if factory is not None and implementation_type is not None:
            raise ValueError("Cannot specify both factory and implementation type")

        # Analyze dependencies
        dependencies = []
        if implementation_type:
            dependencies = self._analyze_dependencies(implementation_type)
        elif factory:
            dependencies = self._analyze_dependencies(factory)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=lifetime,
            dependencies=dependencies
        )

        self._services[service_type] = descriptor
        self.logger.debug(f"Registered service {service_type.__name__} as {lifetime.value}")

        # If singleton with instance, store immediately
        if lifetime == ServiceLifetime.SINGLETON and instance is not None:
            self._singletons[service_type] = instance

        return self

    def _analyze_dependencies(self, target: Any) -> List[Type]:
        """Analyze constructor/function dependencies"""
        dependencies = []

        try:
            if inspect.isclass(target):
                # Analyze class constructor
                constructor = target.__init__
                signature = inspect.signature(constructor)
                type_hints = get_type_hints(constructor)
            elif callable(target):
                # Analyze function
                signature = inspect.signature(target)
                type_hints = get_type_hints(target)
            else:
                return dependencies

            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue

                # Get type from type hints
                if param_name in type_hints:
                    param_type = type_hints[param_name]

                    # Handle Optional types
                    if hasattr(param_type, '__origin__') and param_type.__origin__ is type(type(None)):
                        # This is Optional[T], extract T
                        if hasattr(param_type, '__args__'):
                            param_type = param_type.__args__[0]

                    # Only add non-primitive types as dependencies
                    if (inspect.isclass(param_type) and
                        not param_type.__module__ == 'builtins' and
                        param.default is inspect.Parameter.empty):
                        dependencies.append(param_type)

        except Exception as e:
            self.logger.warning(f"Could not analyze dependencies for {target}: {str(e)}")

        return dependencies

    def resolve(self, service_type: Type[T], scope: Optional[ServiceScope] = None) -> T:
        """Resolve a service instance"""
        try:
            # Check for circular dependencies
            if service_type in self._resolution_stack:
                cycle = " -> ".join([t.__name__ for t in self._resolution_stack] + [service_type.__name__])
                raise CircularDependencyError(f"Circular dependency detected: {cycle}")

            self._resolution_stack.append(service_type)

            try:
                return self._resolve_service(service_type, scope)
            finally:
                self._resolution_stack.pop()

        except Exception as e:
            self.logger.error(f"Failed to resolve service {service_type.__name__}: {str(e)}")
            raise DependencyResolutionError(f"Cannot resolve {service_type.__name__}: {str(e)}")

    def _resolve_service(self, service_type: Type[T], scope: Optional[ServiceScope] = None) -> T:
        """Internal service resolution method"""
        descriptor = self._get_service_descriptor(service_type)

        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._get_singleton_instance(descriptor)

        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if scope is None:
                raise DependencyResolutionError(f"Scoped service {service_type.__name__} requires a scope")
            return scope.get_scoped_instance(service_type)

        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(descriptor, scope)

        elif descriptor.lifetime == ServiceLifetime.FACTORY:
            if descriptor.factory is None:
                raise DependencyResolutionError(f"Factory service {service_type.__name__} has no factory function")
            return descriptor.factory()

        else:
            raise DependencyResolutionError(f"Unknown lifetime: {descriptor.lifetime}")

    def _get_service_descriptor(self, service_type: Type) -> ServiceDescriptor:
        """Get service descriptor or raise error"""
        if service_type not in self._services:
            # Try to auto-register concrete classes
            if inspect.isclass(service_type) and not inspect.isabstract(service_type):
                self.register_transient(service_type)
                return self._services[service_type]
            else:
                raise DependencyResolutionError(f"Service {service_type.__name__} is not registered")

        return self._services[service_type]

    def _get_singleton_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Get or create singleton instance"""
        service_type = descriptor.service_type

        if service_type not in self._singletons:
            if descriptor.instance is not None:
                self._singletons[service_type] = descriptor.instance
            else:
                instance = self._create_instance(descriptor)
                self._singletons[service_type] = instance

        return self._singletons[service_type]

    def _create_instance(self, descriptor: ServiceDescriptor, scope: Optional[ServiceScope] = None) -> Any:
        """Create new service instance with dependency injection"""

        if descriptor.factory is not None:
            # Use factory function
            try:
                # Resolve factory dependencies
                factory_dependencies = self._resolve_dependencies(descriptor.dependencies, scope)
                return descriptor.factory(*factory_dependencies)
            except Exception as e:
                raise DependencyResolutionError(f"Factory creation failed for {descriptor.service_type.__name__}: {str(e)}")

        elif descriptor.implementation_type is not None:
            # Create instance using constructor
            try:
                # Resolve constructor dependencies
                constructor_dependencies = self._resolve_dependencies(descriptor.dependencies, scope)
                return descriptor.implementation_type(*constructor_dependencies)
            except Exception as e:
                raise DependencyResolutionError(f"Constructor creation failed for {descriptor.service_type.__name__}: {str(e)}")

        else:
            raise DependencyResolutionError(f"No implementation or factory specified for {descriptor.service_type.__name__}")

    def _resolve_dependencies(self, dependencies: List[Type], scope: Optional[ServiceScope] = None) -> List[Any]:
        """Resolve list of dependencies"""
        resolved = []

        for dep_type in dependencies:
            try:
                resolved_dependency = self._resolve_service(dep_type, scope)
                resolved.append(resolved_dependency)
            except Exception as e:
                self.logger.error(f"Failed to resolve dependency {dep_type.__name__}: {str(e)}")
                raise

        return resolved

    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered"""
        return service_type in self._services

    def get_registered_services(self) -> List[Type]:
        """Get list of all registered services"""
        return list(self._services.keys())

    def create_scope(self) -> ServiceScope:
        """Create new service scope"""
        return ServiceScope(self)

    @asynccontextmanager
    async def scope(self):
        """Create async context manager for scoped services"""
        service_scope = self.create_scope()
        try:
            yield service_scope
        finally:
            await service_scope.dispose()

    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate dependency injection configuration"""
        validation_results = {
            "valid_services": [],
            "missing_dependencies": [],
            "circular_dependencies": [],
            "factory_errors": []
        }

        for service_type, descriptor in self._services.items():
            try:
                # Check if all dependencies are registered or can be auto-registered
                missing_deps = []
                for dep_type in descriptor.dependencies:
                    if not self.is_registered(dep_type) and not self._can_auto_register(dep_type):
                        missing_deps.append(dep_type.__name__)

                if missing_deps:
                    validation_results["missing_dependencies"].append(
                        f"{service_type.__name__}: {', '.join(missing_deps)}"
                    )
                else:
                    validation_results["valid_services"].append(service_type.__name__)

                # Test factory functions
                if descriptor.factory is not None:
                    try:
                        # Try to analyze factory signature
                        inspect.signature(descriptor.factory)
                    except Exception as e:
                        validation_results["factory_errors"].append(
                            f"{service_type.__name__}: {str(e)}"
                        )

            except Exception as e:
                self.logger.error(f"Validation error for {service_type.__name__}: {str(e)}")

        # Check for circular dependencies
        for service_type in self._services:
            try:
                self._resolution_stack.clear()
                self._check_circular_dependencies(service_type, set())
            except CircularDependencyError as e:
                validation_results["circular_dependencies"].append(str(e))

        return validation_results

    def _can_auto_register(self, service_type: Type) -> bool:
        """Check if service can be auto-registered"""
        return (inspect.isclass(service_type) and
                not inspect.isabstract(service_type) and
                hasattr(service_type, '__init__'))

    def _check_circular_dependencies(self, service_type: Type, visited: set):
        """Recursively check for circular dependencies"""
        if service_type in visited:
            raise CircularDependencyError(f"Circular dependency involving {service_type.__name__}")

        if service_type not in self._services:
            return  # External dependency or auto-registered

        visited.add(service_type)
        descriptor = self._services[service_type]

        for dependency in descriptor.dependencies:
            self._check_circular_dependencies(dependency, visited.copy())

    async def dispose(self):
        """Dispose of all singleton instances"""
        for instance in self._singletons.values():
            if hasattr(instance, 'dispose') and callable(instance.dispose):
                if asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
                else:
                    instance.dispose()

        self._singletons.clear()
        self.logger.info("DI container disposed")

    def __str__(self) -> str:
        """String representation of container state"""
        return (f"DIContainer(services={len(self._services)}, "
                f"singletons={len(self._singletons)})")


# Decorator for marking injectable services
def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """Decorator to mark a class as injectable"""
    def decorator(cls):
        cls._injectable_lifetime = lifetime
        return cls
    return decorator


# Global DI container instance
container = DIContainer()


def get_container() -> DIContainer:
    """Get the global DI container"""
    return container


def configure_default_services(di_container: DIContainer):
    """Configure default services in DI container"""
    try:
        # Register infrastructure services
        from backend.infrastructure.service_discovery import ServiceRegistry, service_registry
        from backend.infrastructure.health_monitor import ServiceHealthMonitor, create_health_monitor

        # Register service registry as singleton
        di_container.register_singleton(ServiceRegistry, instance=service_registry)

        # Register health monitor as singleton
        health_monitor = create_health_monitor(service_registry)
        di_container.register_singleton(ServiceHealthMonitor, instance=health_monitor)

        logger.info("Default services configured in DI container")

    except Exception as e:
        logger.error(f"Failed to configure default services: {str(e)}")
        raise


# Auto-configure default services on import
try:
    configure_default_services(container)
except Exception as e:
    logger.warning(f"Failed to auto-configure default services: {str(e)}")


class ServiceProvider:
    """High-level service provider interface"""

    def __init__(self, container: DIContainer):
        self.container = container

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance"""
        return self.container.resolve(service_type)

    def get_required_service(self, service_type: Type[T]) -> T:
        """Get required service instance (throws if not found)"""
        try:
            return self.container.resolve(service_type)
        except DependencyResolutionError:
            raise DependencyResolutionError(f"Required service {service_type.__name__} is not available")

    def create_scope(self) -> ServiceScope:
        """Create new service scope"""
        return self.container.create_scope()

    @asynccontextmanager
    async def scope(self):
        """Create async context manager for scoped services"""
        async with self.container.scope() as scope:
            provider = ScopedServiceProvider(self.container, scope)
            yield provider


class ScopedServiceProvider(ServiceProvider):
    """Service provider for scoped services"""

    def __init__(self, container: DIContainer, scope: ServiceScope):
        super().__init__(container)
        self.scope = scope

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance within scope"""
        return self.container.resolve(service_type, self.scope)


# Global service provider
service_provider = ServiceProvider(container)