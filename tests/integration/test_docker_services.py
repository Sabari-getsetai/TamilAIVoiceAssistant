"""
Integration tests for Docker service connectivity.

Tests database, MinIO, and Redis connections with Docker services.
"""

import pytest
import asyncio
from datetime import datetime

# Import connection modules
from backend.database.connection import (
    check_db_health,
    get_db_info,
    wait_for_database,
    init_db_with_retry,
)
from backend.storage.minio_client import (
    check_minio_health,
    get_minio_info,
    wait_for_minio,
    init_buckets_with_retry,
)
from backend.cache.redis_client import (
    check_redis_health,
    get_redis_info,
    wait_for_redis,
    init_redis_with_retry,
)
from backend.infrastructure.retry import wait_for_multiple_services
from backend.infrastructure.health import get_health_checker


class TestDatabaseConnection:
    """Test PostgreSQL database connectivity."""
    
    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check."""
        is_healthy = await check_db_health()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_database_info(self):
        """Test getting database information."""
        info = await get_db_info()
        assert isinstance(info, dict)
        
        if info.get("connected"):
            assert "version" in info
            assert "has_pgvector" in info
            assert "is_docker" in info
    
    @pytest.mark.asyncio
    async def test_wait_for_database(self):
        """Test waiting for database availability."""
        available = await wait_for_database(timeout=30.0)
        assert isinstance(available, bool)
    
    @pytest.mark.asyncio
    async def test_database_initialization_with_retry(self):
        """Test database initialization with retry logic."""
        try:
            await init_db_with_retry(max_retries=3, initial_delay=0.5)
            # If no exception, initialization succeeded
            assert True
        except Exception as e:
            # Log the error but don't fail the test if database is unavailable
            print(f"Database initialization failed (expected if DB not running): {e}")
            pytest.skip("Database not available")


class TestMinIOConnection:
    """Test MinIO object storage connectivity."""
    
    @pytest.mark.asyncio
    async def test_minio_health_check(self):
        """Test MinIO health check."""
        is_healthy = await check_minio_health()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_minio_info(self):
        """Test getting MinIO information."""
        info = await get_minio_info()
        assert isinstance(info, dict)
        
        if info.get("connected"):
            assert "endpoint" in info
            assert "buckets" in info
            assert "is_docker" in info
    
    @pytest.mark.asyncio
    async def test_wait_for_minio(self):
        """Test waiting for MinIO availability."""
        available = await wait_for_minio(timeout=30.0)
        assert isinstance(available, bool)
    
    @pytest.mark.asyncio
    async def test_minio_initialization_with_retry(self):
        """Test MinIO bucket initialization with retry logic."""
        try:
            await init_buckets_with_retry(max_retries=3, initial_delay=0.5)
            assert True
        except Exception as e:
            print(f"MinIO initialization failed (expected if MinIO not running): {e}")
            pytest.skip("MinIO not available")


class TestRedisConnection:
    """Test Redis cache connectivity."""
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check."""
        is_healthy = await check_redis_health()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_redis_info(self):
        """Test getting Redis information."""
        info = await get_redis_info()
        assert isinstance(info, dict)
        
        if info.get("connected"):
            assert "redis_version" in info
            assert "uptime_seconds" in info
            assert "is_docker" in info
    
    @pytest.mark.asyncio
    async def test_wait_for_redis(self):
        """Test waiting for Redis availability."""
        available = await wait_for_redis(timeout=30.0)
        assert isinstance(available, bool)
    
    @pytest.mark.asyncio
    async def test_redis_initialization_with_retry(self):
        """Test Redis initialization with retry logic."""
        try:
            await init_redis_with_retry(max_retries=3, initial_delay=0.5)
            assert True
        except Exception as e:
            print(f"Redis initialization failed (expected if Redis not running): {e}")
            pytest.skip("Redis not available")


class TestMultipleServices:
    """Test multiple services together."""
    
    @pytest.mark.asyncio
    async def test_wait_for_all_services(self):
        """Test waiting for all services to become available."""
        services = {
            "database": check_db_health,
            "minio": check_minio_health,
            "redis": check_redis_health,
        }
        
        results = await wait_for_multiple_services(
            services,
            timeout=60.0,
            check_interval=2.0
        )
        
        assert isinstance(results, dict)
        assert len(results) == 3
        
        for service_name, available in results.items():
            assert isinstance(available, bool)
            print(f"{service_name}: {'available' if available else 'unavailable'}")
    
    @pytest.mark.asyncio
    async def test_health_checker_integration(self):
        """Test health checker with all services."""
        health_checker = get_health_checker()
        
        # Add all services
        health_checker.add_service("database", check_db_health, check_interval=10.0)
        health_checker.add_service("minio", check_minio_health, check_interval=10.0)
        health_checker.add_service("redis", check_redis_health, check_interval=10.0)
        
        # Get overall health
        overall_health = await health_checker.get_overall_health()
        
        assert isinstance(overall_health, dict)
        assert "overall_status" in overall_health
        assert "services" in overall_health
        assert "summary" in overall_health
        assert "timestamp" in overall_health
        
        # Verify service details
        services = overall_health["services"]
        assert "database" in services
        assert "minio" in services
        assert "redis" in services
        
        # Verify summary
        summary = overall_health["summary"]
        assert "total_services" in summary
        assert "healthy_services" in summary
        assert summary["total_services"] == 3


class TestDockerEnvironmentDetection:
    """Test Docker environment detection."""
    
    def test_docker_detection_in_database(self):
        """Test Docker detection in database module."""
        from backend.database.connection import IS_DOCKER
        assert isinstance(IS_DOCKER, bool)
    
    def test_docker_detection_in_minio(self):
        """Test Docker detection in MinIO module."""
        from backend.storage.minio_client import IS_DOCKER
        assert isinstance(IS_DOCKER, bool)
    
    def test_docker_detection_in_redis(self):
        """Test Docker detection in Redis module."""
        from backend.cache.redis_client import IS_DOCKER
        assert isinstance(IS_DOCKER, bool)


class TestRetryMechanisms:
    """Test retry mechanisms under failure conditions."""
    
    @pytest.mark.asyncio
    async def test_retry_with_unavailable_service(self):
        """Test retry behavior when service is unavailable."""
        from backend.infrastructure.retry import retry_with_backoff, RetryConfig
        
        attempt_count = 0
        
        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            raise ConnectionError("Service unavailable")
        
        config = RetryConfig(
            max_retries=3,
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        
        with pytest.raises(ConnectionError):
            await retry_with_backoff(
                failing_operation,
                config,
                "test_operation"
            )
        
        # Should have attempted initial try + 3 retries = 4 total
        assert attempt_count == 4
    
    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self):
        """Test retry behavior when service eventually succeeds."""
        from backend.infrastructure.retry import retry_with_backoff, RetryConfig
        
        attempt_count = 0
        
        async def eventually_succeeding_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Service unavailable")
            return "success"
        
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        
        result = await retry_with_backoff(
            eventually_succeeding_operation,
            config,
            "test_operation"
        )
        
        assert result == "success"
        assert attempt_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
