"""
Services Package - Microservice-Ready Business Logic Layer

Contains service classes that encapsulate business logic and coordinate
between different components. Each service module is designed to be
microservice-ready with clear domain boundaries.

Service Modules:
- auth: Authentication and authorization services
- conversation: Session and turn management services
- media: Audio processing and speech services
- documents: Document lifecycle and RAG services
- organization: Multi-tenant organization services
- infrastructure: Cross-cutting infrastructure services

Legacy Services (maintained for backwards compatibility):
- document_service: Will move to documents/ module
- session_service: Will move to conversation/ module
- organization_service: Will move to organization/ module
- email_service: Will move to infrastructure/ module
- tier_service: Will move to organization/ module
"""

# Legacy service imports (maintained for backwards compatibility)
from .document_service import DocumentService, get_document_service
from .session_service import DatabaseSessionManager, get_session_manager

# New microservice-ready service imports
from .auth import (
    AuthenticationService,
    AuthorizationService,
    get_authorization_service,
    get_current_user_dep,
    get_current_user_optional_dep,
    get_current_admin_user_dep,
    get_current_organization_dep,
    get_current_organization_admin_dep,
    get_user_organizations_dep
)
from .media import AudioService
from .organization import OrganizationPermissionService
from .documents import DocumentTaskService

__all__ = [
    # Legacy services (backwards compatibility)
    "DocumentService", "get_document_service",
    "DatabaseSessionManager", "get_session_manager",

    # Authentication and authorization
    "AuthenticationService",
    "AuthorizationService",
    "get_authorization_service",
    "get_current_user_dep",
    "get_current_user_optional_dep",
    "get_current_admin_user_dep",
    "get_current_organization_dep",
    "get_current_organization_admin_dep",
    "get_user_organizations_dep",

    # Media services
    "AudioService",

    # Organization services
    "OrganizationPermissionService",

    # Document services
    "DocumentTaskService"
]