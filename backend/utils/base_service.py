"""
Base Service - Common Service Patterns

This module provides a base service class that implements common
service patterns for business logic components. All specific services
can inherit from this base class.
"""

from abc import ABC
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base service class providing common service patterns.

    This class provides:
    - Consistent logging patterns
    - Error handling utilities
    - Service lifecycle management
    - Health check capabilities
    """

    def __init__(self, service_name: Optional[str] = None):
        """
        Initialize the service with a name for logging and identification.

        Args:
            service_name: Name of the service for logging and monitoring.
                         If None, will use the class name as fallback.
        """
        # Use class name as fallback if no service_name provided
        if service_name is None:
            service_name = self.__class__.__name__

        self.service_name = service_name
        self.logger = logging.getLogger(f"services.{service_name}")
        self._is_healthy = True
        self._last_health_check = datetime.utcnow()

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a service operation with consistent formatting.

        Args:
            operation: Description of the operation
            details: Optional details dictionary
        """
        message = f"[{self.service_name}] {operation}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"
        self.logger.info(message)

    def log_error(self, operation: str, error: Exception, details: Optional[Dict[str, Any]] = None):
        """
        Log a service error with consistent formatting.

        Args:
            operation: Description of the operation that failed
            error: The exception that occurred
            details: Optional details dictionary
        """
        message = f"[{self.service_name}] FAILED {operation}: {str(error)}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"
        self.logger.error(message, exc_info=True)

    async def validate_dependencies(self) -> Dict[str, bool]:
        """
        Validate that service dependencies are available.

        Returns:
            Dictionary mapping dependency names to their health status

        Note:
            Override in subclasses to implement specific dependency checks
        """
        return {"base_service": True}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of this service.

        Returns:
            Dictionary containing health status and metadata
        """
        try:
            # Update last health check time
            self._last_health_check = datetime.utcnow()

            # Validate dependencies
            dependencies = await self.validate_dependencies()
            all_healthy = all(dependencies.values())

            # Update service health status
            self._is_healthy = all_healthy

            return {
                "service": self.service_name,
                "healthy": self._is_healthy,
                "last_check": self._last_health_check.isoformat(),
                "dependencies": dependencies
            }

        except Exception as e:
            self._is_healthy = False
            self.log_error("health_check", e)
            return {
                "service": self.service_name,
                "healthy": False,
                "last_check": self._last_health_check.isoformat(),
                "error": str(e)
            }

    @property
    def is_healthy(self) -> bool:
        """Check if the service is currently healthy."""
        return self._is_healthy

    async def initialize(self):
        """
        Initialize the service.

        Override in subclasses to implement specific initialization logic.
        """
        self.log_operation("initialize", {"service": self.service_name})

    async def shutdown(self):
        """
        Shutdown the service gracefully.

        Override in subclasses to implement specific cleanup logic.
        """
        self.log_operation("shutdown", {"service": self.service_name})

    def handle_database_error(self, operation: str, error: Exception, session: AsyncSession):
        """
        Handle database errors with consistent patterns.

        Args:
            operation: The operation that failed
            error: The database error
            session: The database session (for potential rollback)
        """
        self.log_error(operation, error)
        # Note: Calling code should handle session.rollback() if needed

    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """
        Validate input data against required fields.

        Args:
            data: Input data to validate
            required_fields: List of required field names

        Returns:
            Validated data dictionary

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        return data

    def create_service_response(
        self,
        success: bool,
        data: Optional[Any] = None,
        message: Optional[str] = None,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized service response.

        Args:
            success: Whether the operation was successful
            data: Response data (if any)
            message: Success or informational message
            errors: List of error messages

        Returns:
            Standardized service response dictionary
        """
        response = {
            "success": success,
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }

        if data is not None:
            response["data"] = data

        if message:
            response["message"] = message

        if errors:
            response["errors"] = errors

        return response


class MicroserviceInterface(ABC):
    """
    Interface definition for microservice-ready services.

    Services implementing this interface can be easily extracted
    into separate microservices.
    """

    @property
    def service_name(self) -> str:
        """Get the service name for identification."""
        pass

    @property
    def service_version(self) -> str:
        """Get the service version."""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Perform service health check."""
        pass

    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics and statistics."""
        pass

    async def get_dependencies(self) -> List[str]:
        """Get list of service dependencies."""
        pass