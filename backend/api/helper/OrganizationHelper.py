"""Helper functions for organization-related operations."""


from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from sqlalchemy import select, and_
from backend.database.models import OrganizationMember, OrganizationRole, User




async def get_user_organization_role(
    db: AsyncSession, 
    user_id: str, 
    organization_id: str
) -> Optional[OrganizationRole]:
    """Get user's role in a specific organization."""
    result = await db.execute(
        select(OrganizationMember.role)
        .where(
            and_(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id
            )
        )
    )
    role = result.scalar_one_or_none()
    return role


async def check_organization_permission(
    db: AsyncSession,
    user: User,
    organization_id: str,
    required_roles: List[OrganizationRole] = None
) -> bool:
    """Check if user has permission to access organization."""
    # System admins have access to all organizations
    if user.role.value == "admin":
        return True

    # Check organization membership
    user_role = await get_user_organization_role(db, user.id, organization_id)
    if not user_role:
        return False

    # Check specific role requirements
    if required_roles and user_role not in required_roles:
        return False

    return True


def has_org_admin_permission(user_role: OrganizationRole, action: str) -> bool:
    """
    Check if ORG_ADMIN role has permission for specific actions.

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
    """
    if user_role not in [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER]:
        return False

    # Owner has all permissions
    if user_role == OrganizationRole.OWNER:
        return True

    # ADMIN has all permissions (legacy compatibility)
    if user_role == OrganizationRole.ADMIN:
        return True

    # ORG_ADMIN specific permissions
    if user_role == OrganizationRole.ORG_ADMIN:
        allowed_actions = [
            "view_organization", "view_members", "remove_member",
            "update_member_role", "update_organization", "manage_billing"
        ]
        restricted_actions = [
            "delete_organization", "promote_to_owner", "demote_owner"
        ]

        if action in allowed_actions:
            return True
        if action in restricted_actions:
            return False

    return False