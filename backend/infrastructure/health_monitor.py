"""Comprehensive Health Monitoring System

This module provides advanced health monitoring capabilities for microservice architecture,
including circuit breakers, health aggregation, and monitoring dashboards.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, NamedTuple
from enum import Enum
from dataclasses import dataclass, field
import statistics
from collections import defaultdict, deque

from backend.utils.base_service import BaseService
from backend.infrastructure.service_discovery import ServiceRegistry, ServiceStatus, ServiceInfo


logger = logging.getLogger(__name__)


class HealthCheckType(str, Enum):
    """Types of health checks"""
    HTTP_ENDPOINT = "http_endpoint"
    DATABASE = "database"
    REDIS = "redis"
    MINIO = "minio"
    EXTERNAL_API = "external_api"
    CUSTOM = "custom"


class HealthLevel(str, Enum):
    """Health check severity levels"""
    CRITICAL = "critical"      # Service cannot function
    IMPORTANT = "important"    # Degraded functionality
    OPTIONAL = "optional"      # Non-essential features affected


@dataclass
class HealthMetric:
    """Individual health check metric"""
    check_name: str
    check_type: HealthCheckType
    level: HealthLevel
    status: ServiceStatus
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def is_healthy(self) -> bool:
        """Check if this metric represents a healthy state"""
        return self.status == ServiceStatus.HEALTHY


@dataclass
class HealthReport:
    """Comprehensive health report for a service"""
    service_name: str
    service_id: str
    overall_status: ServiceStatus
    metrics: List[HealthMetric]
    generation_time: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    error_count: int = 0
    warning_count: int = 0

    def get_critical_issues(self) -> List[HealthMetric]:
        """Get all critical health issues"""
        return [metric for metric in self.metrics
                if metric.level == HealthLevel.CRITICAL and not metric.is_healthy()]

    def get_degraded_features(self) -> List[HealthMetric]:
        """Get features with degraded performance"""
        return [metric for metric in self.metrics
                if metric.level == HealthLevel.IMPORTANT and not metric.is_healthy()]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues"""
        return len(self.get_critical_issues()) > 0


class HealthChecker:
    """Individual health checker for specific components"""

    def __init__(self, name: str, check_type: HealthCheckType, level: HealthLevel):
        self.name = name
        self.check_type = check_type
        self.level = level
        self.logger = logging.getLogger(f"{__name__}.HealthChecker.{name}")

    async def check(self) -> HealthMetric:
        """Perform health check - to be overridden by specific implementations"""
        start_time = time.time()

        try:
            # Default implementation - override in subclasses
            result = await self._perform_check()
            response_time = (time.time() - start_time) * 1000

            return HealthMetric(
                check_name=self.name,
                check_type=self.check_type,
                level=self.level,
                status=ServiceStatus.HEALTHY if result else ServiceStatus.UNHEALTHY,
                response_time_ms=response_time
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Health check failed for {self.name}: {str(e)}")

            return HealthMetric(
                check_name=self.name,
                check_type=self.check_type,
                level=self.level,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def _perform_check(self) -> bool:
        """Override this method in subclasses"""
        return True


class DatabaseHealthChecker(HealthChecker):
    """Health checker for database connectivity"""

    def __init__(self, db_session_factory):
        super().__init__("database", HealthCheckType.DATABASE, HealthLevel.CRITICAL)
        self.db_session_factory = db_session_factory

    async def _perform_check(self) -> bool:
        """Check database connectivity and basic operations"""
        try:
            from backend.database.connection import get_db_session

            async with get_db_session() as session:
                # Simple query to test connectivity
                result = await session.execute("SELECT 1")
                return result.scalar() == 1

        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return False


class RedisHealthChecker(HealthChecker):
    """Health checker for Redis connectivity"""

    def __init__(self):
        super().__init__("redis", HealthCheckType.REDIS, HealthLevel.IMPORTANT)

    async def _perform_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            from backend.cache.redis_client import redis_client

            # Test Redis connection with ping
            response = await redis_client.ping()
            return response is True

        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
            return False


class MinIOHealthChecker(HealthChecker):
    """Health checker for MinIO connectivity"""

    def __init__(self):
        super().__init__("minio", HealthCheckType.MINIO, HealthLevel.IMPORTANT)

    async def _perform_check(self) -> bool:
        """Check MinIO connectivity"""
        try:
            from backend.storage.file_manager import FileManager

            file_manager = FileManager()
            # Check if MinIO is responsive
            return await file_manager.health_check()

        except Exception as e:
            self.logger.error(f"MinIO health check failed: {str(e)}")
            return False


class ServiceHealthMonitor(BaseService):
    """Comprehensive health monitoring for microservices"""

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()
        self.service_name = "ServiceHealthMonitor"
        self.service_registry = service_registry

        # Health checkers registry
        self._health_checkers: Dict[str, HealthChecker] = {}

        # Health history for trending
        self._health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Monitoring configuration
        self._monitoring_interval = 30  # seconds
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # Health report callbacks
        self._health_report_callbacks: List[Callable[[HealthReport], None]] = []

        # Aggregated health metrics
        self._system_metrics = {
            "total_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "last_check_time": None
        }

    def register_health_checker(self, checker: HealthChecker):
        """Register a health checker"""
        self._health_checkers[checker.name] = checker
        self.logger.info(f"Registered health checker: {checker.name} ({checker.check_type})")

    def unregister_health_checker(self, checker_name: str) -> bool:
        """Unregister a health checker"""
        if checker_name in self._health_checkers:
            del self._health_checkers[checker_name]
            self.logger.info(f"Unregistered health checker: {checker_name}")
            return True
        return False

    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop the health monitoring loop"""
        self._shutdown = True
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self._shutdown:
            try:
                # Perform health checks for registered services
                await self._perform_all_health_checks()

                # Wait for next interval
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _perform_all_health_checks(self):
        """Perform health checks for all registered services"""
        check_tasks = []

        # Check registered services
        services = await self.service_registry.discover_services()
        for service in services:
            task = asyncio.create_task(self._check_service_health(service))
            check_tasks.append(task)

        # Execute all health checks concurrently
        if check_tasks:
            results = await asyncio.gather(*check_tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, HealthReport):
                    await self._process_health_report(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Health check task failed: {str(result)}")

    async def _check_service_health(self, service: ServiceInfo) -> HealthReport:
        """Perform comprehensive health check for a service"""
        start_time = time.time()
        metrics = []

        try:
            # Run all registered health checkers
            checker_tasks = []
            for checker in self._health_checkers.values():
                task = asyncio.create_task(checker.check())
                checker_tasks.append(task)

            if checker_tasks:
                check_results = await asyncio.gather(*checker_tasks, return_exceptions=True)

                for result in check_results:
                    if isinstance(result, HealthMetric):
                        metrics.append(result)
                    elif isinstance(result, Exception):
                        # Create error metric
                        error_metric = HealthMetric(
                            check_name="unknown",
                            check_type=HealthCheckType.CUSTOM,
                            level=HealthLevel.IMPORTANT,
                            status=ServiceStatus.UNHEALTHY,
                            error_message=str(result)
                        )
                        metrics.append(error_metric)

            # Determine overall status
            overall_status = self._calculate_overall_status(metrics)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Count errors and warnings
            error_count = len([m for m in metrics if m.status == ServiceStatus.UNHEALTHY])
            warning_count = len([m for m in metrics if m.status == ServiceStatus.DEGRADED])

            return HealthReport(
                service_name=service.service_name,
                service_id=service.service_id,
                overall_status=overall_status,
                metrics=metrics,
                response_time_ms=response_time,
                error_count=error_count,
                warning_count=warning_count
            )

        except Exception as e:
            self.logger.error(f"Error checking health for service {service.service_name}: {str(e)}")

            # Return unhealthy report
            error_metric = HealthMetric(
                check_name="health_check_error",
                check_type=HealthCheckType.CUSTOM,
                level=HealthLevel.CRITICAL,
                status=ServiceStatus.UNHEALTHY,
                error_message=str(e)
            )

            return HealthReport(
                service_name=service.service_name,
                service_id=service.service_id,
                overall_status=ServiceStatus.UNHEALTHY,
                metrics=[error_metric],
                error_count=1
            )

    def _calculate_overall_status(self, metrics: List[HealthMetric]) -> ServiceStatus:
        """Calculate overall service status from individual metrics"""
        if not metrics:
            return ServiceStatus.UNKNOWN

        critical_issues = [m for m in metrics if m.level == HealthLevel.CRITICAL and not m.is_healthy()]
        important_issues = [m for m in metrics if m.level == HealthLevel.IMPORTANT and not m.is_healthy()]

        if critical_issues:
            return ServiceStatus.UNHEALTHY
        elif important_issues:
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.HEALTHY

    async def _process_health_report(self, report: HealthReport):
        """Process a health report and update monitoring data"""
        try:
            # Update service status in registry
            await self.service_registry.update_service_status(report.service_id, report.overall_status)

            # Store health history
            self._health_history[report.service_id].append(report)

            # Update system metrics
            self._update_system_metrics(report)

            # Trigger callbacks
            for callback in self._health_report_callbacks:
                try:
                    callback(report)
                except Exception as e:
                    self.logger.error(f"Error in health report callback: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error processing health report for {report.service_name}: {str(e)}")

    def _update_system_metrics(self, report: HealthReport):
        """Update aggregated system metrics"""
        self._system_metrics["total_checks"] += len(report.metrics)
        self._system_metrics["failed_checks"] += report.error_count

        # Update average response time (simple moving average)
        current_avg = self._system_metrics["average_response_time"]
        if current_avg == 0:
            self._system_metrics["average_response_time"] = report.response_time_ms
        else:
            self._system_metrics["average_response_time"] = (current_avg + report.response_time_ms) / 2

        self._system_metrics["last_check_time"] = time.time()

    async def get_service_health_history(self, service_id: str, limit: int = 50) -> List[HealthReport]:
        """Get health history for a specific service"""
        if service_id in self._health_history:
            history = list(self._health_history[service_id])
            return history[-limit:] if limit > 0 else history
        return []

    async def get_system_health_overview(self) -> Dict[str, Any]:
        """Get system-wide health overview"""
        services = await self.service_registry.discover_services()

        status_counts = defaultdict(int)
        total_services = len(services)

        for service in services:
            status_counts[service.status.value] += 1

        # Calculate health percentage
        healthy_count = status_counts.get("healthy", 0)
        health_percentage = (healthy_count / total_services * 100) if total_services > 0 else 0

        return {
            "overall_health_percentage": health_percentage,
            "total_services": total_services,
            "services_by_status": dict(status_counts),
            "system_metrics": self._system_metrics.copy(),
            "monitoring": {
                "active": self._monitoring_task is not None and not self._monitoring_task.done(),
                "interval_seconds": self._monitoring_interval,
                "registered_checkers": len(self._health_checkers)
            },
            "timestamp": datetime.now().isoformat()
        }

    async def get_unhealthy_services(self) -> List[ServiceInfo]:
        """Get all unhealthy services"""
        return await self.service_registry.discover_services(
            status_filter={ServiceStatus.UNHEALTHY, ServiceStatus.DEGRADED}
        )

    def add_health_report_callback(self, callback: Callable[[HealthReport], None]):
        """Add callback for health report processing"""
        self._health_report_callbacks.append(callback)

    async def force_health_check(self, service_id: Optional[str] = None) -> List[HealthReport]:
        """Force immediate health check for specific service or all services"""
        if service_id:
            service = await self.service_registry.get_service(service_id)
            if service:
                report = await self._check_service_health(service)
                await self._process_health_report(report)
                return [report]
        else:
            # Check all services
            await self._perform_all_health_checks()

        return []

    def configure_monitoring(self,
                           interval_seconds: Optional[int] = None,
                           history_size: Optional[int] = None):
        """Configure monitoring parameters"""
        if interval_seconds is not None:
            self._monitoring_interval = max(10, interval_seconds)  # Minimum 10 seconds

        if history_size is not None:
            # Update maxlen for all existing deques
            for service_id in self._health_history:
                old_deque = self._health_history[service_id]
                new_deque = deque(old_deque, maxlen=history_size)
                self._health_history[service_id] = new_deque

        self.logger.info(f"Health monitoring configured: interval={self._monitoring_interval}s")


def create_health_monitor(service_registry: ServiceRegistry) -> ServiceHealthMonitor:
    """Factory function to create a configured health monitor"""
    monitor = ServiceHealthMonitor(service_registry)

    # Register standard health checkers
    monitor.register_health_checker(DatabaseHealthChecker(None))  # Will use default session factory
    monitor.register_health_checker(RedisHealthChecker())
    monitor.register_health_checker(MinIOHealthChecker())

    return monitor