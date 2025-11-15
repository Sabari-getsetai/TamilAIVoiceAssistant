"""Organization Permission Service - Role-Based Access Control

This service handles:
- Organization membership validation
- Role-based permission checking
- Organization access control
- Admin privilege validation

Replaces: backend.api.helper.OrganizationHelper
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.utils.base_service import BaseService
from backend.repositories.user_repository import OrganizationMemberRepository, OrganizationRepository
from backend.database.models import (
    User, Organization, OrganizationMember, OrganizationRole, UserRole
)


class OrganizationPermissionService(BaseService):
    """Service for organization-based permission and access control"""

    def __init__(self):
        super().__init__()
        self.service_name = "OrganizationPermissionService"
        self.member_repo = OrganizationMemberRepository()
        self.org_repo = OrganizationRepository()

        # Define role hierarchy for permission checks
        self.role_hierarchy = {
            OrganizationRole.MEMBER: 1,
            OrganizationRole.ORG_ADMIN: 2,
            OrganizationRole.ADMIN: 3,  # Legacy role for backward compatibility
            OrganizationRole.OWNER: 4
        }

        # Define permission matrix for different actions
        self.permission_matrix = {
            # Organization management
            "view_organization": [OrganizationRole.MEMBER, OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "update_organization": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "delete_organization": [OrganizationRole.OWNER],

            # Member management
            "view_members": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "invite_member": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "remove_member": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "update_member_role": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],

            # Special owner actions
            "promote_to_owner": [OrganizationRole.OWNER],
            "demote_owner": [OrganizationRole.OWNER],
            "transfer_ownership": [OrganizationRole.OWNER],

            # Billing and settings
            "manage_billing": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "view_analytics": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],

            # Content management
            "upload_documents": [OrganizationRole.MEMBER, OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "delete_documents": [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
            "manage_conversations": [OrganizationRole.MEMBER, OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER],
        }

    async def get_user_organization_role(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> Optional[OrganizationRole]:
        """Get user's role in a specific organization

        Args:
            db: Database session
            user_id: User ID to check
            organization_id: Organization ID to check

        Returns:
            User's organization role or None if not a member
        """
        try:
            membership = await self.member_repo.get_membership(db, user_id, organization_id)
            return membership.role if membership else None
        except Exception as e:
            self.logger.error(f"Error getting user organization role: {str(e)}")
            return None

    async def check_organization_membership(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> bool:
        """Check if user is a member of organization

        Args:
            db: Database session
            user_id: User ID to check
            organization_id: Organization ID to check

        Returns:
            True if user is a member, False otherwise
        """
        role = await self.get_user_organization_role(db, user_id, organization_id)
        return role is not None

    async def check_organization_permission(
        self,
        db: AsyncSession,
        user: User,
        organization_id: str,
        action: str,
        required_roles: Optional[List[OrganizationRole]] = None
    ) -> bool:
        """Check if user has permission to perform action in organization

        Args:
            db: Database session
            user: User object
            organization_id: Organization ID to check
            action: Action to check permission for
            required_roles: Optional specific roles required (overrides action-based permissions)

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # System admins have access to all organizations
            if user.role == UserRole.ADMIN:
                self.logger.debug(f"System admin {user.id} granted access to org {organization_id}")
                return True

            # Get user's organization role
            user_role = await self.get_user_organization_role(db, user.id, organization_id)
            if not user_role:
                self.logger.debug(f"User {user.id} is not a member of organization {organization_id}")
                return False

            # Check specific role requirements if provided
            if required_roles:
                permission_granted = user_role in required_roles
                self.logger.debug(
                    f"Role-based permission check: user_role={user_role}, "
                    f"required={required_roles}, granted={permission_granted}"
                )
                return permission_granted

            # Check action-based permissions
            return self.has_organization_permission(user_role, action)

        except Exception as e:
            self.logger.error(f"Error checking organization permission: {str(e)}")
            return False

    def has_organization_permission(
        self,
        user_role: OrganizationRole,
        action: str
    ) -> bool:
        """Check if role has permission for specific action

        Args:
            user_role: User's organization role
            action: Action to check permission for

        Returns:
            True if role has permission for action, False otherwise
        """
        if action not in self.permission_matrix:
            self.logger.warning(f"Unknown action requested: {action}")
            return False

        allowed_roles = self.permission_matrix[action]
        permission_granted = user_role in allowed_roles

        self.logger.debug(
            f"Permission check: role={user_role}, action={action}, "
            f"allowed_roles={allowed_roles}, granted={permission_granted}"
        )

        return permission_granted

    def has_admin_permission(
        self,
        user_role: OrganizationRole,
        action: str
    ) -> bool:
        """Check if ORG_ADMIN role has permission for specific actions

        This method provides backward compatibility with the original helper function
        and implements the specific ORG_ADMIN permission model.

        ORG_ADMIN permissions:
        - View organization details and members
        - Remove members (except owners)
        - Change member roles (except to/from owner)
        - Update organization settings
        - Manage billing information

        ORG_ADMIN restrictions:
        - Cannot delete organization
        - Cannot promote/demote owners
        - Cannot change their own role

        Args:
            user_role: User's organization role
            action: Action to check permission for

        Returns:
            True if role has permission for action, False otherwise
        """
        # No permission if not at least ORG_ADMIN
        if user_role not in [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER]:
            return False

        # OWNER has all permissions
        if user_role == OrganizationRole.OWNER:
            return True

        # ADMIN has all permissions (legacy compatibility)
        if user_role == OrganizationRole.ADMIN:
            return True

        # ORG_ADMIN specific permissions
        if user_role == OrganizationRole.ORG_ADMIN:
            allowed_actions = {
                "view_organization", "view_members", "remove_member",
                "update_member_role", "update_organization", "manage_billing",
                "invite_member", "view_analytics", "delete_documents"
            }

            restricted_actions = {
                "delete_organization", "promote_to_owner", "demote_owner",
                "transfer_ownership"
            }

            if action in allowed_actions:
                return True
            if action in restricted_actions:
                return False

            # Use general permission matrix for other actions
            return self.has_organization_permission(user_role, action)

        return False

    async def get_user_organization_permissions(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> Dict[str, bool]:
        """Get all permissions for user in organization

        Args:
            db: Database session
            user_id: User ID to check
            organization_id: Organization ID to check

        Returns:
            Dictionary mapping action names to permission status
        """
        permissions = {}

        try:
            user_role = await self.get_user_organization_role(db, user_id, organization_id)

            if not user_role:
                # No permissions if not a member
                for action in self.permission_matrix:
                    permissions[action] = False
            else:
                # Check each action permission
                for action in self.permission_matrix:
                    permissions[action] = self.has_organization_permission(user_role, action)

            return permissions

        except Exception as e:
            self.logger.error(f"Error getting user organization permissions: {str(e)}")
            # Return all False permissions on error
            return {action: False for action in self.permission_matrix}

    def get_role_hierarchy_level(self, role: OrganizationRole) -> int:
        """Get numeric level for role hierarchy comparison

        Args:
            role: Organization role

        Returns:
            Numeric level (higher = more privileges)
        """
        return self.role_hierarchy.get(role, 0)

    def can_modify_role(
        self,
        current_user_role: OrganizationRole,
        target_role: OrganizationRole,
        new_role: OrganizationRole
    ) -> tuple[bool, Optional[str]]:
        """Check if user can modify another user's role

        Args:
            current_user_role: Role of user making the change
            target_role: Current role of user being modified
            new_role: New role to assign

        Returns:
            Tuple of (can_modify, error_message)
        """
        current_level = self.get_role_hierarchy_level(current_user_role)
        target_level = self.get_role_hierarchy_level(target_role)
        new_level = self.get_role_hierarchy_level(new_role)

        # Only OWNER can modify OWNER roles
        if target_role == OrganizationRole.OWNER and current_user_role != OrganizationRole.OWNER:
            return False, "Only organization owners can modify owner roles"

        # Only OWNER can promote to OWNER
        if new_role == OrganizationRole.OWNER and current_user_role != OrganizationRole.OWNER:
            return False, "Only organization owners can promote users to owner"

        # Users cannot modify roles at their level or higher (except OWNER modifying OWNER)
        if current_user_role != OrganizationRole.OWNER and target_level >= current_level:
            return False, "Cannot modify users with equal or higher privileges"

        # Users cannot promote others to their level or higher
        if current_user_role != OrganizationRole.OWNER and new_level >= current_level:
            return False, "Cannot promote users to equal or higher privileges"

        # ORG_ADMIN specific restrictions
        if current_user_role == OrganizationRole.ORG_ADMIN:
            if new_role == OrganizationRole.ADMIN:
                return False, "ORG_ADMIN cannot promote users to legacy ADMIN role"

        return True, None

    async def validate_organization_access(
        self,
        db: AsyncSession,
        user: User,
        organization_id: str,
        action: str,
        raise_exception: bool = True
    ) -> bool:
        """Validate user access to organization with optional exception raising

        Args:
            db: Database session
            user: User object
            organization_id: Organization ID to check
            action: Action to validate
            raise_exception: Whether to raise HTTPException on failure

        Returns:
            True if access is granted

        Raises:
            HTTPException: If access denied and raise_exception=True
        """
        from fastapi import HTTPException, status

        try:
            # Check if organization exists and is active
            organization = await self.org_repo.get_by_id(db, organization_id)
            if not organization or not organization.is_active:
                if raise_exception:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found or inactive"
                    )
                return False

            # Check user permission
            has_permission = await self.check_organization_permission(
                db, user, organization_id, action
            )

            if not has_permission and raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for action: {action}"
                )

            return has_permission

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error validating organization access: {str(e)}")
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Organization access validation failed"
                )
            return False

    def get_available_actions(self, user_role: OrganizationRole) -> List[str]:
        """Get list of actions available to a specific role

        Args:
            user_role: Organization role to check

        Returns:
            List of action names the role can perform
        """
        available_actions = []

        for action, allowed_roles in self.permission_matrix.items():
            if user_role in allowed_roles:
                available_actions.append(action)

        return sorted(available_actions)