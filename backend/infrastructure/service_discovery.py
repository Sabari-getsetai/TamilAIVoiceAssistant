"""Service Discovery and Registry

This module provides service discovery mechanisms for microservice architecture,
enabling services to register themselves and discover other services dynamically.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import weakref

from backend.utils.base_service import BaseService


logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInfo:
    """Service registration information"""
    service_name: str
    service_id: str
    host: str
    port: int
    protocol: str = "http"
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.STARTING
    health_check_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    tags: Set[str] = None
    registered_at: float = None
    last_heartbeat: float = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = set()
        if self.registered_at is None:
            self.registered_at = time.time()
        if self.last_heartbeat is None:
            self.last_heartbeat = time.time()
        if self.health_check_url is None:
            self.health_check_url = f"{self.protocol}://{self.host}:{self.port}/health"

    @property
    def base_url(self) -> str:
        """Get the base URL for the service"""
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def is_stale(self) -> bool:
        """Check if service heartbeat is stale (>60 seconds)"""
        return time.time() - self.last_heartbeat > 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['tags'] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create ServiceInfo from dictionary"""
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = set(data['tags'])
        return cls(**data)


class ServiceRegistry(BaseService):
    """Centralized service registry for microservice discovery"""

    def __init__(self):
        super().__init__()
        self.service_name = "ServiceRegistry"

        # Service storage
        self._services: Dict[str, ServiceInfo] = {}  # service_id -> ServiceInfo
        self._services_by_name: Dict[str, Set[str]] = {}  # service_name -> set of service_ids
        self._services_by_tag: Dict[str, Set[str]] = {}  # tag -> set of service_ids

        # Health monitoring
        self._health_check_interval = 30  # seconds
        self._health_timeout = 10  # seconds
        self._health_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # Event callbacks
        self._service_registered_callbacks: List[Callable[[ServiceInfo], None]] = []
        self._service_unregistered_callbacks: List[Callable[[str], None]] = []
        self._service_status_changed_callbacks: List[Callable[[ServiceInfo, ServiceStatus], None]] = []

    async def register_service(self, service_info: ServiceInfo) -> None:
        """Register a service in the registry"""
        try:
            service_id = service_info.service_id
            service_name = service_info.service_name

            # Store service info
            self._services[service_id] = service_info

            # Index by name
            if service_name not in self._services_by_name:
                self._services_by_name[service_name] = set()
            self._services_by_name[service_name].add(service_id)

            # Index by tags
            for tag in service_info.tags:
                if tag not in self._services_by_tag:
                    self._services_by_tag[tag] = set()
                self._services_by_tag[tag].add(service_id)

            self.logger.info(f"Registered service {service_name} with ID {service_id} at {service_info.base_url}")

            # Trigger callbacks
            for callback in self._service_registered_callbacks:
                try:
                    callback(service_info)
                except Exception as e:
                    self.logger.error(f"Error in service registered callback: {str(e)}")

            # Start health monitoring if not already running
            if self._health_task is None or self._health_task.done():
                self._health_task = asyncio.create_task(self._health_monitor_loop())

        except Exception as e:
            self.logger.error(f"Error registering service {service_info.service_name}: {str(e)}")
            raise

    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from the registry"""
        try:
            if service_id not in self._services:
                return False

            service_info = self._services[service_id]
            service_name = service_info.service_name

            # Remove from main storage
            del self._services[service_id]

            # Remove from name index
            if service_name in self._services_by_name:
                self._services_by_name[service_name].discard(service_id)
                if not self._services_by_name[service_name]:
                    del self._services_by_name[service_name]

            # Remove from tag indexes
            for tag in service_info.tags:
                if tag in self._services_by_tag:
                    self._services_by_tag[tag].discard(service_id)
                    if not self._services_by_tag[tag]:
                        del self._services_by_tag[tag]

            self.logger.info(f"Unregistered service {service_name} with ID {service_id}")

            # Trigger callbacks
            for callback in self._service_unregistered_callbacks:
                try:
                    callback(service_id)
                except Exception as e:
                    self.logger.error(f"Error in service unregistered callback: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"Error unregistering service {service_id}: {str(e)}")
            return False

    async def discover_services(self,
                               service_name: Optional[str] = None,
                               tags: Optional[Set[str]] = None,
                               status_filter: Optional[Set[ServiceStatus]] = None) -> List[ServiceInfo]:
        """Discover services based on criteria"""
        try:
            matching_services = []

            # Get candidate service IDs
            candidate_ids = set(self._services.keys())

            # Filter by service name
            if service_name:
                if service_name in self._services_by_name:
                    candidate_ids &= self._services_by_name[service_name]
                else:
                    return []  # No services with this name

            # Filter by tags (all tags must match)
            if tags:
                for tag in tags:
                    if tag in self._services_by_tag:
                        candidate_ids &= self._services_by_tag[tag]
                    else:
                        return []  # Tag not found, no matches

            # Filter by status and collect results
            for service_id in candidate_ids:
                service_info = self._services[service_id]

                if status_filter is None or service_info.status in status_filter:
                    matching_services.append(service_info)

            return matching_services

        except Exception as e:
            self.logger.error(f"Error discovering services: {str(e)}")
            return []

    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get specific service by ID"""
        return self._services.get(service_id)

    async def get_healthy_services(self, service_name: str) -> List[ServiceInfo]:
        """Get all healthy services of a specific type"""
        return await self.discover_services(
            service_name=service_name,
            status_filter={ServiceStatus.HEALTHY}
        )

    async def heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat timestamp"""
        try:
            if service_id in self._services:
                self._services[service_id].last_heartbeat = time.time()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating heartbeat for {service_id}: {str(e)}")
            return False

    async def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update service status"""
        try:
            if service_id not in self._services:
                return False

            service_info = self._services[service_id]
            old_status = service_info.status
            service_info.status = status

            if old_status != status:
                self.logger.info(f"Service {service_info.service_name} status changed from {old_status} to {status}")

                # Trigger callbacks
                for callback in self._service_status_changed_callbacks:
                    try:
                        callback(service_info, old_status)
                    except Exception as e:
                        self.logger.error(f"Error in service status changed callback: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"Error updating service status for {service_id}: {str(e)}")
            return False

    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while not self._shutdown:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _perform_health_checks(self):
        """Perform health checks on all registered services"""
        health_check_tasks = []

        for service_id, service_info in self._services.items():
            if service_info.health_check_url:
                task = asyncio.create_task(self._check_service_health(service_id, service_info))
                health_check_tasks.append(task)

        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)

    async def _check_service_health(self, service_id: str, service_info: ServiceInfo):
        """Check health of a single service"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._health_timeout)) as session:
                async with session.get(service_info.health_check_url) as response:
                    if response.status == 200:
                        await self.update_service_status(service_id, ServiceStatus.HEALTHY)
                    elif response.status == 503:
                        await self.update_service_status(service_id, ServiceStatus.DEGRADED)
                    else:
                        await self.update_service_status(service_id, ServiceStatus.UNHEALTHY)
        except asyncio.TimeoutError:
            self.logger.warning(f"Health check timeout for service {service_info.service_name}")
            await self.update_service_status(service_id, ServiceStatus.UNHEALTHY)
        except Exception as e:
            self.logger.warning(f"Health check failed for service {service_info.service_name}: {str(e)}")
            await self.update_service_status(service_id, ServiceStatus.UNHEALTHY)

        # Remove stale services
        if service_info.is_stale:
            self.logger.warning(f"Removing stale service {service_info.service_name} (last heartbeat: {service_info.last_heartbeat})")
            await self.unregister_service(service_id)

    def add_service_registered_callback(self, callback: Callable[[ServiceInfo], None]):
        """Add callback for service registration events"""
        self._service_registered_callbacks.append(callback)

    def add_service_unregistered_callback(self, callback: Callable[[str], None]):
        """Add callback for service unregistration events"""
        self._service_unregistered_callbacks.append(callback)

    def add_service_status_changed_callback(self, callback: Callable[[ServiceInfo, ServiceStatus], None]):
        """Add callback for service status change events"""
        self._service_status_changed_callbacks.append(callback)

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            "total_services": len(self._services),
            "services_by_name": {name: len(ids) for name, ids in self._services_by_name.items()},
            "services_by_status": {},
            "services_by_tag": {tag: len(ids) for tag, ids in self._services_by_tag.items()},
            "health_monitoring": {
                "enabled": self._health_task is not None and not self._health_task.done(),
                "check_interval": self._health_check_interval,
                "timeout": self._health_timeout
            }
        }

        # Count services by status
        for service_info in self._services.values():
            status = service_info.status.value
            stats["services_by_status"][status] = stats["services_by_status"].get(status, 0) + 1

        return stats

    async def shutdown(self):
        """Shutdown the service registry"""
        self._shutdown = True
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass


# Global service registry instance
service_registry = ServiceRegistry()


class ServiceClient:
    """Client for interacting with registered services"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.logger = logging.getLogger(f"{__name__}.ServiceClient")

    async def call_service(self,
                          service_name: str,
                          endpoint: str,
                          method: str = "GET",
                          data: Any = None,
                          headers: Optional[Dict[str, str]] = None,
                          timeout: int = 30,
                          retry_attempts: int = 2) -> Optional[Any]:
        """Call a service endpoint with load balancing and retry logic"""

        for attempt in range(retry_attempts + 1):
            try:
                # Discover healthy services
                services = await self.registry.get_healthy_services(service_name)

                if not services:
                    self.logger.error(f"No healthy services found for {service_name}")
                    return None

                # Simple round-robin load balancing
                service = services[attempt % len(services)]
                url = f"{service.base_url}{endpoint}"

                # Make the request
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    async with session.request(method, url, json=data, headers=headers) as response:
                        if response.status < 400:
                            if response.content_type == 'application/json':
                                return await response.json()
                            else:
                                return await response.text()
                        else:
                            self.logger.warning(f"Service call failed: {response.status} - {await response.text()}")

            except Exception as e:
                self.logger.warning(f"Service call attempt {attempt + 1} failed: {str(e)}")
                if attempt == retry_attempts:
                    self.logger.error(f"All retry attempts failed for {service_name}{endpoint}")

        return None

    async def broadcast_to_services(self,
                                   service_name: str,
                                   endpoint: str,
                                   method: str = "POST",
                                   data: Any = None,
                                   headers: Optional[Dict[str, str]] = None) -> List[Any]:
        """Broadcast a call to all healthy instances of a service"""
        services = await self.registry.get_healthy_services(service_name)

        if not services:
            self.logger.warning(f"No healthy services found for broadcast to {service_name}")
            return []

        tasks = []
        for service in services:
            url = f"{service.base_url}{endpoint}"
            task = asyncio.create_task(self._single_service_call(url, method, data, headers))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if not isinstance(result, Exception):
                successful_results.append(result)

        return successful_results

    async def _single_service_call(self, url: str, method: str, data: Any, headers: Optional[Dict[str, str]]) -> Any:
        """Make a single service call"""
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data, headers=headers) as response:
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return await response.text()


# Global service client
service_client = ServiceClient(service_registry)