"""
Auth Service Module - Authentication and Authorization

This module handles all authentication and authorization concerns,
designed to be microservice-ready.

Services:
- authentication_service: JWT tokens, password hashing, user login
- authorization_service: Permission checks, role-based access control
"""

from .authentication_service import AuthenticationService
from .authorization_service import (
    AuthorizationService,
    get_authorization_service,
    get_current_user_dep,
    get_current_user_optional_dep,
    get_current_admin_user_dep,
    get_current_organization_dep,
    get_current_organization_admin_dep,
    get_user_organizations_dep
)

__all__ = [
    # Service classes
    "AuthenticationService",
    "AuthorizationService",

    # Dependency factory
    "get_authorization_service",

    # FastAPI dependency functions
    "get_current_user_dep",
    "get_current_user_optional_dep",
    "get_current_admin_user_dep",
    "get_current_organization_dep",
    "get_current_organization_admin_dep",
    "get_user_organizations_dep"
]