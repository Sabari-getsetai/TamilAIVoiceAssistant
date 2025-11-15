"""
Audit Middleware for Enterprise Compliance

Automatically logs all API requests and responses for audit trail purposes.
Supports GDPR, SOC2, and other compliance requirements.
"""

import time
import uuid
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from backend.services.audit_service import audit_service
from backend.database.models import ActionType, ResourceType
from backend.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit all API requests and responses.

    Features:
    - Logs all HTTP requests and responses
    - Captures user context from JWT tokens
    - Records timing and performance metrics
    - Handles sensitive data filtering
    - Supports async operations
    """

    def __init__(
        self,
        app,
        exclude_paths: Optional[list] = None,
        exclude_methods: Optional[list] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_fields: Optional[list] = None
    ):
        super().__init__(app)

        # Default excluded paths (health checks, static files, etc.)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static",
            "/metrics"
        ]

        # Default excluded methods
        self.exclude_methods = exclude_methods or ["OPTIONS"]

        # Logging configuration
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

        # Sensitive fields to filter from logs
        self.sensitive_fields = sensitive_fields or [
            "password",
            "token",
            "secret",
            "key",
            "authorization",
            "api_key",
            "credit_card",
            "ssn",
            "phone",
            "email"  # Can be configured based on privacy requirements
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main middleware dispatch method.
        """
        # Check if request should be excluded
        if self._should_exclude_request(request):
            return await call_next(request)

        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Extract user information from request
        user_context = await self._extract_user_context(request)

        # Capture request information
        request_info = await self._capture_request_info(request, request_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Capture response information
            response_info = self._capture_response_info(response, process_time)

            # Log the audit event
            await self._log_audit_event(
                request=request,
                request_info=request_info,
                response_info=response_info,
                user_context=user_context,
                request_id=request_id
            )

            # Add request ID to response headers for tracking
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time

            # Log error audit event
            await self._log_error_audit_event(
                request=request,
                request_info=request_info,
                error=e,
                user_context=user_context,
                request_id=request_id,
                process_time=process_time
            )

            # Re-raise the exception
            raise

    def _should_exclude_request(self, request: Request) -> bool:
        """
        Determine if request should be excluded from auditing.
        """
        # Check path exclusions
        request_path = request.url.path
        for excluded_path in self.exclude_paths:
            if request_path.startswith(excluded_path):
                return True

        # Check method exclusions
        if request.method in self.exclude_methods:
            return True

        return False

    async def _extract_user_context(self, request: Request) -> Dict[str, Any]:
        """
        Extract user information from JWT token or session.
        """
        user_context = {
            "user_id": None,
            "organization_id": None,
            "roles": [],
            "session_id": None
        }

        try:
            # Try to get user from JWT token
            authorization = request.headers.get("authorization")
            if authorization and authorization.startswith("Bearer "):
                # This would integrate with your JWT service
                # For now, we'll check if user info is available in request state
                if hasattr(request.state, 'user'):
                    user = request.state.user
                    user_context["user_id"] = getattr(user, 'id', None)
                    user_context["organization_id"] = getattr(user, 'organization_id', None)
                    user_context["roles"] = getattr(user, 'roles', [])

            # Try to get session ID from cookies or headers
            session_id = request.cookies.get("session_id") or request.headers.get("x-session-id")
            if session_id:
                user_context["session_id"] = session_id

        except Exception as e:
            logger.warning(f"Failed to extract user context: {e}")

        return user_context

    async def _capture_request_info(self, request: Request, request_id: str) -> Dict[str, Any]:
        """
        Capture relevant information from the request.
        """
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._filter_sensitive_data(dict(request.headers)),
            "client_ip": None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
            "body": None
        }

        # Extract client IP
        if request.client:
            request_info["client_ip"] = request.client.host

        # Capture request body if configured
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read and store body, then recreate for downstream processing
                body = await request.body()
                if body:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            body_json = json.loads(body.decode('utf-8'))
                            request_info["body"] = self._filter_sensitive_data(body_json)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            request_info["body"] = {"size": len(body), "type": "binary"}
                    else:
                        request_info["body"] = {"size": len(body), "type": content_type}
            except Exception as e:
                logger.warning(f"Failed to capture request body: {e}")

        return request_info

    def _capture_response_info(self, response: Response, process_time: float) -> Dict[str, Any]:
        """
        Capture relevant information from the response.
        """
        response_info = {
            "status_code": response.status_code,
            "headers": self._filter_sensitive_data(dict(response.headers)),
            "content_type": response.headers.get("content-type"),
            "content_length": response.headers.get("content-length"),
            "process_time_ms": round(process_time * 1000, 2),
            "body": None
        }

        # Capture response body if configured and it's a JSON response
        if self.log_response_body:
            try:
                if isinstance(response, JSONResponse) and hasattr(response, 'body'):
                    try:
                        body_json = json.loads(response.body.decode('utf-8'))
                        response_info["body"] = self._filter_sensitive_data(body_json)
                    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                        pass
            except Exception as e:
                logger.warning(f"Failed to capture response body: {e}")

        return response_info

    async def _log_audit_event(
        self,
        request: Request,
        request_info: Dict[str, Any],
        response_info: Dict[str, Any],
        user_context: Dict[str, Any],
        request_id: str
    ):
        """
        Log the audit event to the database.
        """
        try:
            # Determine action type based on the request
            action_type = self._determine_action_type(request_info)

            # Determine resource information
            resource_info = self._extract_resource_info(request_info)

            # Create audit metadata
            audit_metadata = {
                "request": {
                    "method": request_info["method"],
                    "path": request_info["path"],
                    "query_params": request_info["query_params"],
                    "content_type": request_info["content_type"],
                    "user_agent": request_info["user_agent"]
                },
                "response": {
                    "status_code": response_info["status_code"],
                    "content_type": response_info["content_type"],
                    "process_time_ms": response_info["process_time_ms"]
                },
                "request_id": request_id
            }

            # Add request/response bodies if configured
            if self.log_request_body and request_info.get("body"):
                audit_metadata["request"]["body"] = request_info["body"]

            if self.log_response_body and response_info.get("body"):
                audit_metadata["response"]["body"] = response_info["body"]

            # Log the audit event
            await audit_service.log_action(
                action_type=action_type,
                user_id=user_context.get("user_id"),
                organization_id=user_context.get("organization_id"),
                resource_type=resource_info.get("type"),
                resource_id=resource_info.get("id"),
                ip_address=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                session_id=user_context.get("session_id"),
                request_id=request_id,
                endpoint=request_info["path"],
                http_method=request_info["method"],
                request_metadata=audit_metadata,
                response_status=str(response_info["status_code"]),
                description=f"{request_info['method']} {request_info['path']} -> {response_info['status_code']}"
            )

        except Exception as e:
            # Don't let audit failures break the application
            logger.error(f"Failed to log audit event: {e}")

    async def _log_error_audit_event(
        self,
        request: Request,
        request_info: Dict[str, Any],
        error: Exception,
        user_context: Dict[str, Any],
        request_id: str,
        process_time: float
    ):
        """
        Log audit event for request errors.
        """
        try:
            action_type = ActionType.API_REQUEST

            audit_metadata = {
                "request": {
                    "method": request_info["method"],
                    "path": request_info["path"],
                    "user_agent": request_info["user_agent"]
                },
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "process_time_ms": round(process_time * 1000, 2)
                },
                "request_id": request_id
            }

            await audit_service.log_action(
                action_type=action_type,
                user_id=user_context.get("user_id"),
                organization_id=user_context.get("organization_id"),
                ip_address=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                session_id=user_context.get("session_id"),
                request_id=request_id,
                endpoint=request_info["path"],
                http_method=request_info["method"],
                request_metadata=audit_metadata,
                response_status="500",
                description=f"{request_info['method']} {request_info['path']} -> ERROR: {str(error)}",
                severity="critical"
            )

        except Exception as audit_error:
            logger.error(f"Failed to log error audit event: {audit_error}")

    def _determine_action_type(self, request_info: Dict[str, Any]) -> str:
        """
        Determine the appropriate action type based on the request.
        """
        method = request_info["method"]
        path = request_info["path"]

        # Map specific endpoints to actions
        if "/auth/login" in path:
            return ActionType.LOGIN.value
        elif "/auth/logout" in path:
            return ActionType.LOGOUT.value
        elif "/documents" in path and method == "POST":
            return ActionType.DOCUMENT_UPLOADED.value
        elif "/documents" in path and method == "GET":
            return ActionType.DOCUMENT_VIEWED.value
        elif "/sessions" in path and method == "POST":
            return ActionType.SESSION_STARTED.value
        elif "/conversations" in path:
            return ActionType.CONVERSATION_TURN.value
        elif "/users" in path and method == "POST":
            return ActionType.USER_CREATED.value
        elif "/users" in path and method in ["PUT", "PATCH"]:
            return ActionType.USER_UPDATED.value
        elif "/organizations" in path and method == "POST":
            return ActionType.ORGANIZATION_CREATED.value

        # Default to generic API request
        return ActionType.API_REQUEST.value

    def _extract_resource_info(self, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract resource type and ID from the request path.
        """
        path = request_info["path"]
        resource_info = {"type": None, "id": None}

        # Extract resource information from path patterns
        if "/documents/" in path:
            resource_info["type"] = ResourceType.DOCUMENT.value
            # Extract document ID if present in path
            path_parts = path.split("/documents/")
            if len(path_parts) > 1 and path_parts[1]:
                try:
                    resource_id = path_parts[1].split("/")[0]
                    if resource_id:
                        resource_info["id"] = uuid.UUID(resource_id)
                except (ValueError, IndexError):
                    pass

        elif "/sessions/" in path:
            resource_info["type"] = ResourceType.SESSION.value
            # Extract session ID if present
            path_parts = path.split("/sessions/")
            if len(path_parts) > 1 and path_parts[1]:
                try:
                    resource_id = path_parts[1].split("/")[0]
                    if resource_id:
                        resource_info["id"] = uuid.UUID(resource_id)
                except (ValueError, IndexError):
                    pass

        elif "/users/" in path:
            resource_info["type"] = ResourceType.USER.value

        elif "/organizations/" in path:
            resource_info["type"] = ResourceType.ORGANIZATION.value

        return resource_info

    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        Recursively filter sensitive data from request/response data.
        """
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if any(sensitive_field.lower() in key.lower() for sensitive_field in self.sensitive_fields):
                    filtered[key] = "[REDACTED]"
                else:
                    filtered[key] = self._filter_sensitive_data(value)
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data


def create_audit_middleware(
    exclude_paths: Optional[list] = None,
    log_request_body: bool = False,
    log_response_body: bool = False,
    sensitive_fields: Optional[list] = None
) -> AuditMiddleware:
    """
    Factory function to create audit middleware with custom configuration.

    Args:
        exclude_paths: List of paths to exclude from auditing
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        sensitive_fields: Additional sensitive fields to filter

    Returns:
        Configured AuditMiddleware instance
    """
    return lambda app: AuditMiddleware(
        app,
        exclude_paths=exclude_paths,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        sensitive_fields=sensitive_fields
    )