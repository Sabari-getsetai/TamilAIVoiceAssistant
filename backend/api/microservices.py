"""Microservice Management API Endpoints

This module provides API endpoints for managing microservice infrastructure,
including service discovery, health monitoring, and resilience patterns.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.infrastructure import (
    service_registry, service_client, resilient_client,
    ServiceInfo, ServiceStatus, create_health_monitor,
    CircuitBreakerConfig, RetryConfig, RetryStrategy, ServiceLifetime,
    container, service_provider
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/microservices", tags=["microservices"])

# Initialize health monitor
health_monitor = create_health_monitor(service_registry)


# Pydantic models for API
class ServiceRegistrationRequest(BaseModel):
    """Service registration request"""
    service_name: str = Field(..., description="Name of the service")
    service_id: str = Field(..., description="Unique ID for the service instance")
    host: str = Field(..., description="Service host")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    protocol: str = Field("http", description="Service protocol")
    version: str = Field("1.0.0", description="Service version")
    health_check_url: Optional[str] = Field(None, description="Custom health check URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Service metadata")
    tags: Optional[List[str]] = Field(None, description="Service tags")


class ServiceDiscoveryQuery(BaseModel):
    """Service discovery query parameters"""
    service_name: Optional[str] = Field(None, description="Filter by service name")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    status: Optional[List[ServiceStatus]] = Field(None, description="Filter by status")


class CircuitBreakerConfigModel(BaseModel):
    """Circuit breaker configuration"""
    failure_threshold: int = Field(5, ge=1, description="Failures before opening")
    recovery_timeout_ms: int = Field(60000, ge=1000, description="Recovery timeout in ms")
    success_threshold: int = Field(3, ge=1, description="Successes to close from half-open")
    timeout_ms: int = Field(5000, ge=100, description="Individual call timeout in ms")
    minimum_calls: int = Field(10, ge=1, description="Minimum calls before considering failure rate")


class RetryConfigModel(BaseModel):
    """Retry configuration"""
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts")
    strategy: RetryStrategy = Field(RetryStrategy.EXPONENTIAL_BACKOFF, description="Retry strategy")
    base_delay_ms: int = Field(100, ge=10, description="Base delay in milliseconds")
    max_delay_ms: int = Field(5000, ge=100, description="Maximum delay in milliseconds")
    backoff_factor: float = Field(2.0, ge=1.0, description="Backoff multiplier")
    jitter: bool = Field(True, description="Enable jitter")


# Service Discovery Endpoints
@router.post("/services/register", response_model=Dict[str, Any])
async def register_service(request: ServiceRegistrationRequest):
    """Register a new service in the service registry"""
    try:
        # Convert request to ServiceInfo
        service_info = ServiceInfo(
            service_name=request.service_name,
            service_id=request.service_id,
            host=request.host,
            port=request.port,
            protocol=request.protocol,
            version=request.version,
            health_check_url=request.health_check_url,
            metadata=request.metadata or {},
            tags=set(request.tags) if request.tags else set()
        )

        # Register service
        await service_registry.register_service(service_info)

        return {
            "message": f"Service {request.service_name} registered successfully",
            "service_id": request.service_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to register service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/services/{service_id}")
async def unregister_service(service_id: str):
    """Unregister a service from the registry"""
    try:
        success = await service_registry.unregister_service(service_id)

        if not success:
            raise HTTPException(status_code=404, detail="Service not found")

        return {
            "message": f"Service {service_id} unregistered successfully",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


@router.get("/services/discover", response_model=List[Dict[str, Any]])
async def discover_services(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    status: Optional[str] = Query(None, description="Comma-separated statuses to filter by")
):
    """Discover services based on criteria"""
    try:
        # Parse query parameters
        tag_set = set(tags.split(',')) if tags else None
        status_set = None
        if status:
            status_list = status.split(',')
            status_set = {ServiceStatus(s.strip()) for s in status_list}

        # Discover services
        services = await service_registry.discover_services(
            service_name=service_name,
            tags=tag_set,
            status_filter=status_set
        )

        # Convert to dict format
        result = []
        for service in services:
            service_dict = service.to_dict()
            result.append(service_dict)

        return result

    except Exception as e:
        logger.error(f"Failed to discover services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.get("/services/{service_id}", response_model=Dict[str, Any])
async def get_service_info(service_id: str):
    """Get detailed information about a specific service"""
    try:
        service = await service_registry.get_service(service_id)

        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        return service.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services/{service_id}/heartbeat")
async def service_heartbeat(service_id: str):
    """Update service heartbeat timestamp"""
    try:
        success = await service_registry.heartbeat(service_id)

        if not success:
            raise HTTPException(status_code=404, detail="Service not found")

        return {
            "message": "Heartbeat updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update heartbeat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/stats", response_model=Dict[str, Any])
async def get_registry_stats():
    """Get service registry statistics"""
    try:
        stats = await service_registry.get_registry_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get registry stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Monitoring Endpoints
@router.get("/health/overview", response_model=Dict[str, Any])
async def get_health_overview():
    """Get system-wide health overview"""
    try:
        overview = await health_monitor.get_system_health_overview()
        return overview
    except Exception as e:
        logger.error(f"Failed to get health overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/services/{service_id}/history", response_model=List[Dict[str, Any]])
async def get_service_health_history(
    service_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records")
):
    """Get health history for a specific service"""
    try:
        history = await health_monitor.get_service_health_history(service_id, limit)

        # Convert to dict format
        result = []
        for report in history:
            report_dict = {
                "service_name": report.service_name,
                "service_id": report.service_id,
                "overall_status": report.overall_status.value,
                "response_time_ms": report.response_time_ms,
                "error_count": report.error_count,
                "warning_count": report.warning_count,
                "generation_time": report.generation_time,
                "metrics": [
                    {
                        "check_name": metric.check_name,
                        "check_type": metric.check_type.value,
                        "level": metric.level.value,
                        "status": metric.status.value,
                        "response_time_ms": metric.response_time_ms,
                        "error_message": metric.error_message,
                        "timestamp": metric.timestamp
                    }
                    for metric in report.metrics
                ]
            }
            result.append(report_dict)

        return result

    except Exception as e:
        logger.error(f"Failed to get health history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check/{service_id}")
async def force_health_check(service_id: str):
    """Force immediate health check for a service"""
    try:
        reports = await health_monitor.force_health_check(service_id)

        if not reports:
            raise HTTPException(status_code=404, detail="Service not found")

        return {
            "message": f"Health check completed for service {service_id}",
            "report_count": len(reports),
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to force health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/unhealthy", response_model=List[Dict[str, Any]])
async def get_unhealthy_services():
    """Get all unhealthy services"""
    try:
        services = await health_monitor.get_unhealthy_services()

        result = []
        for service in services:
            result.append(service.to_dict())

        return result

    except Exception as e:
        logger.error(f"Failed to get unhealthy services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Resilience Pattern Endpoints
@router.post("/resilience/circuit-breaker/{service_name}/configure")
async def configure_circuit_breaker(service_name: str, config: CircuitBreakerConfigModel):
    """Configure circuit breaker for a service"""
    try:
        # Convert to internal config
        cb_config = CircuitBreakerConfig(
            failure_threshold=config.failure_threshold,
            recovery_timeout_ms=config.recovery_timeout_ms,
            success_threshold=config.success_threshold,
            timeout_ms=config.timeout_ms,
            minimum_calls=config.minimum_calls
        )

        # Configure circuit breaker
        resilient_client.configure_circuit_breaker(service_name, cb_config)

        return {
            "message": f"Circuit breaker configured for service {service_name}",
            "config": config.model_dump(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to configure circuit breaker: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resilience/retry/{service_name}/configure")
async def configure_retry(service_name: str, config: RetryConfigModel):
    """Configure retry mechanism for a service"""
    try:
        # Convert to internal config
        retry_config = RetryConfig(
            max_attempts=config.max_attempts,
            strategy=config.strategy,
            base_delay_ms=config.base_delay_ms,
            max_delay_ms=config.max_delay_ms,
            backoff_factor=config.backoff_factor,
            jitter=config.jitter
        )

        # Configure retry
        resilient_client.configure_retry(service_name, retry_config)

        return {
            "message": f"Retry mechanism configured for service {service_name}",
            "config": config.model_dump(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to configure retry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resilience/bulkhead/{service_name}/configure")
async def configure_bulkhead(
    service_name: str,
    max_concurrent: int = Query(..., ge=1, le=1000, description="Maximum concurrent calls")
):
    """Configure bulkhead isolation for a service"""
    try:
        # Configure bulkhead
        resilient_client.configure_bulkhead(service_name, max_concurrent)

        return {
            "message": f"Bulkhead configured for service {service_name}",
            "max_concurrent": max_concurrent,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to configure bulkhead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resilience/metrics", response_model=Dict[str, Dict[str, Any]])
async def get_resilience_metrics():
    """Get resilience metrics for all services"""
    try:
        metrics = await resilient_client.get_all_service_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get resilience metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resilience/{service_name}/health", response_model=Dict[str, Any])
async def get_service_resilience_health(service_name: str):
    """Get resilience health information for a specific service"""
    try:
        health_info = await resilient_client.get_service_health(service_name)
        return health_info
    except Exception as e:
        logger.error(f"Failed to get service resilience health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resilience/circuit-breaker/{service_name}/reset")
async def reset_circuit_breaker(service_name: str):
    """Manually reset circuit breaker for a service"""
    try:
        success = await resilient_client.reset_circuit_breaker(service_name)

        if not success:
            raise HTTPException(status_code=404, detail="Circuit breaker not found for service")

        return {
            "message": f"Circuit breaker reset for service {service_name}",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dependency Injection Endpoints
@router.get("/di/services", response_model=List[str])
async def get_registered_services():
    """Get list of all registered services in DI container"""
    try:
        services = container.get_registered_services()
        return [service.__name__ for service in services]
    except Exception as e:
        logger.error(f"Failed to get registered services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/di/validate", response_model=Dict[str, List[str]])
async def validate_di_configuration():
    """Validate dependency injection configuration"""
    try:
        validation_results = container.validate_configuration()
        return validation_results
    except Exception as e:
        logger.error(f"Failed to validate DI configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/di/container/status", response_model=Dict[str, Any])
async def get_di_container_status():
    """Get dependency injection container status"""
    try:
        registered_services = container.get_registered_services()

        return {
            "total_services": len(registered_services),
            "service_names": [service.__name__ for service in registered_services],
            "container_info": str(container),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get DI container status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# System Management Endpoints
@router.post("/system/start-monitoring")
async def start_health_monitoring():
    """Start the health monitoring system"""
    try:
        await health_monitor.start_monitoring()

        return {
            "message": "Health monitoring started",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to start monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/stop-monitoring")
async def stop_health_monitoring():
    """Stop the health monitoring system"""
    try:
        await health_monitor.stop_monitoring()

        return {
            "message": "Health monitoring stopped",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status", response_model=Dict[str, Any])
async def get_microservice_system_status():
    """Get comprehensive microservice system status"""
    try:
        # Get registry stats
        registry_stats = await service_registry.get_registry_stats()

        # Get health overview
        health_overview = await health_monitor.get_system_health_overview()

        # Get resilience metrics
        resilience_metrics = await resilient_client.get_all_service_metrics()

        # Get DI container status
        di_services = container.get_registered_services()

        return {
            "system_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "service_registry": registry_stats,
            "health_monitoring": health_overview,
            "resilience_patterns": {
                "configured_services": len(resilience_metrics),
                "service_metrics": resilience_metrics
            },
            "dependency_injection": {
                "registered_services": len(di_services),
                "container_status": str(container)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))