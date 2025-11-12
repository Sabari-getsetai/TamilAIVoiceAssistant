"""
Enhanced health monitoring system for Tamil AI Voice Assistant.

This module provides:
- Comprehensive service health checking
- Service status monitoring with detailed metadata
- Health aggregation and reporting
- Service dependency tracking
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CONNECTING = "connecting"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ConnectionState(str, Enum):
    """Connection state for services."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RETRYING = "retrying"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Detailed health information for a service."""
    service_name: str
    status: ServiceStatus
    connection_state: ConnectionState
    last_check: str
    error_message: Optional[str] = None
    retry_count: int = 0
    uptime_seconds: Optional[float] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "connection_state": self.connection_state.value,
            "last_check": self.last_check,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "uptime_seconds": self.uptime_seconds,
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata,
        }


class ServiceMonitor:
    """Monitors individual service health with detailed tracking."""
    
    def __init__(
        self,
        service_name: str,
        health_check: Callable[[], Awaitable[bool]],
        check_interval: float = 30.0,
        timeout: float = 10.0
    ):
        """
        Initialize service monitor.
        
        Args:
            service_name: Name of the service
            health_check: Async function that returns True if service is healthy
            check_interval: Time between health checks in seconds
            timeout: Timeout for health check operations
        """
        self.service_name = service_name
        self.health_check = health_check
        self.check_interval = check_interval
        self.timeout = timeout
        
        self._current_health: Optional[ServiceHealth] = None
        self._start_time = time.time()
        self._last_healthy_time: Optional[float] = None
        self._consecutive_failures = 0
        self._total_checks = 0
        self._successful_checks = 0
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    @property
    def current_health(self) -> Optional[ServiceHealth]:
        """Get current health status."""
        return self._current_health
    
    @property
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    async def check_health(self) -> ServiceHealth:
        """
        Perform single health check.
        
        Returns:
            ServiceHealth: Current health status
        """
        start_time = time.time()
        check_timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            # Perform health check with timeout
            is_healthy = await asyncio.wait_for(
                self.health_check(),
                timeout=self.timeout
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            self._total_checks += 1
            
            if is_healthy:
                self._successful_checks += 1
                self._consecutive_failures = 0
                self._last_healthy_time = time.time()
                
                status = ServiceStatus.HEALTHY
                connection_state = ConnectionState.CONNECTED
                error_message = None
                
            else:
                self._consecutive_failures += 1
                status = ServiceStatus.UNHEALTHY
                connection_state = ConnectionState.DISCONNECTED
                error_message = "Health check returned False"
            
            # Calculate uptime
            uptime = None
            if self._last_healthy_time:
                uptime = time.time() - self._start_time
            
            # Build metadata
            metadata = {
                "consecutive_failures": self._consecutive_failures,
                "total_checks": self._total_checks,
                "successful_checks": self._successful_checks,
                "success_rate": self._successful_checks / self._total_checks if self._total_checks > 0 else 0,
                "last_healthy": datetime.fromtimestamp(self._last_healthy_time, timezone.utc).isoformat() if self._last_healthy_time else None,
            }
            
            health = ServiceHealth(
                service_name=self.service_name,
                status=status,
                connection_state=connection_state,
                last_check=check_timestamp,
                error_message=error_message,
                retry_count=self._consecutive_failures,
                uptime_seconds=uptime,
                response_time_ms=response_time,
                metadata=metadata,
            )
            
        except asyncio.TimeoutError:
            self._total_checks += 1
            self._consecutive_failures += 1
            
            health = ServiceHealth(
                service_name=self.service_name,
                status=ServiceStatus.UNHEALTHY,
                connection_state=ConnectionState.FAILED,
                last_check=check_timestamp,
                error_message=f"Health check timeout after {self.timeout}s",
                retry_count=self._consecutive_failures,
                response_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "consecutive_failures": self._consecutive_failures,
                    "total_checks": self._total_checks,
                    "successful_checks": self._successful_checks,
                    "timeout": True,
                },
            )
            
        except Exception as e:
            self._total_checks += 1
            self._consecutive_failures += 1
            
            health = ServiceHealth(
                service_name=self.service_name,
                status=ServiceStatus.FAILED,
                connection_state=ConnectionState.FAILED,
                last_check=check_timestamp,
                error_message=str(e),
                retry_count=self._consecutive_failures,
                response_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "consecutive_failures": self._consecutive_failures,
                    "total_checks": self._total_checks,
                    "successful_checks": self._successful_checks,
                    "exception_type": type(e).__name__,
                },
            )
        
        self._current_health = health
        return health
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring:
            logger.warning(f"Monitoring already started for {self.service_name}")
            return
        
        self._monitoring = True
        logger.info(f"Starting health monitoring for {self.service_name} (interval: {self.check_interval}s)")
        
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        logger.info(f"Stopping health monitoring for {self.service_name}")
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
    
    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        try:
            while self._monitoring:
                await self.check_health()
                
                if self._monitoring:  # Check again in case monitoring was stopped
                    await asyncio.sleep(self.check_interval)
                    
        except asyncio.CancelledError:
            logger.debug(f"Monitoring cancelled for {self.service_name}")
        except Exception as e:
            logger.error(f"Error in monitoring loop for {self.service_name}: {e}")
        finally:
            self._monitoring = False


class HealthChecker:
    """Performs comprehensive health checks across all services."""
    
    def __init__(self):
        """Initialize health checker."""
        self._monitors: Dict[str, ServiceMonitor] = {}
        self._global_start_time = time.time()
    
    def add_service(
        self,
        service_name: str,
        health_check: Callable[[], Awaitable[bool]],
        check_interval: float = 30.0,
        timeout: float = 10.0,
        start_monitoring: bool = False
    ) -> ServiceMonitor:
        """
        Add service to health monitoring.
        
        Args:
            service_name: Name of the service
            health_check: Async function that returns True if service is healthy
            check_interval: Time between health checks in seconds
            timeout: Timeout for health check operations
            start_monitoring: Whether to start monitoring immediately
            
        Returns:
            ServiceMonitor: Created service monitor
        """
        if service_name in self._monitors:
            logger.warning(f"Service {service_name} already exists, replacing")
            asyncio.create_task(self._monitors[service_name].stop_monitoring())
        
        monitor = ServiceMonitor(service_name, health_check, check_interval, timeout)
        self._monitors[service_name] = monitor
        
        if start_monitoring:
            asyncio.create_task(monitor.start_monitoring())
        
        logger.info(f"Added health monitoring for {service_name}")
        return monitor
    
    def remove_service(self, service_name: str):
        """
        Remove service from health monitoring.
        
        Args:
            service_name: Name of the service to remove
        """
        if service_name in self._monitors:
            asyncio.create_task(self._monitors[service_name].stop_monitoring())
            del self._monitors[service_name]
            logger.info(f"Removed health monitoring for {service_name}")
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """
        Check health of all registered services.
        
        Returns:
            Dict mapping service names to health status
        """
        if not self._monitors:
            return {}
        
        # Run all health checks concurrently
        tasks = {
            name: monitor.check_health()
            for name, monitor in self._monitors.items()
        }
        
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Error checking health for {name}: {e}")
                results[name] = ServiceHealth(
                    service_name=name,
                    status=ServiceStatus.FAILED,
                    connection_state=ConnectionState.FAILED,
                    last_check=datetime.now(timezone.utc).isoformat(),
                    error_message=f"Health check error: {e}",
                )
        
        return results
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            Dict with overall health information
        """
        service_health = await self.check_all_services()
        
        if not service_health:
            return {
                "overall_status": "unknown",
                "services": {},
                "summary": {
                    "total_services": 0,
                    "healthy_services": 0,
                    "unhealthy_services": 0,
                    "failed_services": 0,
                },
                "uptime_seconds": time.time() - self._global_start_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        # Count service statuses
        status_counts = {}
        for health in service_health.values():
            status = health.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        healthy_count = status_counts.get("healthy", 0)
        total_count = len(service_health)
        
        # Determine overall status
        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": {name: health.to_dict() for name, health in service_health.items()},
            "summary": {
                "total_services": total_count,
                "healthy_services": healthy_count,
                "unhealthy_services": status_counts.get("unhealthy", 0),
                "failed_services": status_counts.get("failed", 0),
                "degraded_services": status_counts.get("degraded", 0),
                "connecting_services": status_counts.get("connecting", 0),
            },
            "uptime_seconds": time.time() - self._global_start_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def start_all_monitoring(self):
        """Start monitoring for all registered services."""
        for monitor in self._monitors.values():
            if not monitor.is_monitoring:
                await monitor.start_monitoring()
    
    async def stop_all_monitoring(self):
        """Stop monitoring for all registered services."""
        for monitor in self._monitors.values():
            await monitor.stop_monitoring()


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """
    Get global health checker instance.
    
    Returns:
        HealthChecker: Global health checker
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def get_service_health(service_name: str) -> Optional[ServiceHealth]:
    """
    Get health status for specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        ServiceHealth or None if service not found
    """
    health_checker = get_health_checker()
    if service_name in health_checker._monitors:
        return await health_checker._monitors[service_name].check_health()
    return None


async def monitor_services(
    services: Dict[str, Callable[[], Awaitable[bool]]],
    check_interval: float = 30.0,
    start_monitoring: bool = True
) -> HealthChecker:
    """
    Set up monitoring for multiple services.
    
    Args:
        services: Dict mapping service names to health check functions
        check_interval: Time between health checks in seconds
        start_monitoring: Whether to start monitoring immediately
        
    Returns:
        HealthChecker: Configured health checker
    """
    health_checker = get_health_checker()
    
    for service_name, health_check in services.items():
        health_checker.add_service(
            service_name,
            health_check,
            check_interval,
            start_monitoring=start_monitoring
        )
    
    return health_checker
