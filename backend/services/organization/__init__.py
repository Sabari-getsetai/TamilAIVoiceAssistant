"""
Organization Service Module - Multi-Tenant Management

This module handles organization and member management,
designed to be microservice-ready.

Services:
- organization_service: Organization lifecycle, settings
- member_service: Member management, invitations, roles
- permission_service: Role-based access control and permissions
- tier_service: User tier detection, feature access control
"""

from .permission_service import OrganizationPermissionService

__all__ = [
    "OrganizationPermissionService"
]