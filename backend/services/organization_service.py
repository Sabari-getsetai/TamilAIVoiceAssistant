"""
Organization service layer for business logic.

This module provides business logic for:
- Tier-based organization ownership validation
- Organization limits and quotas
- Role-based permission validation
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database.models import User, Organization, OrganizationMember, OrganizationRole


class OrganizationService:
    """Service class for organization-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_organization_creation(self, user: User) -> Dict[str, Any]:
        """
        Validate if user can create a new organization based on their tier.

        Returns:
            dict with 'can_create' boolean and 'reason' string
        """
        # Get user's current organization count
        result = await self.db.execute(
            select(func.count(Organization.id))
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.role == OrganizationRole.OWNER,
                Organization.is_active == True
            )
        )
        current_org_count = result.scalar() or 0

        # Check against user's tier limits
        max_allowed = user.max_organizations_allowed

        if current_org_count >= max_allowed:
            return {
                'can_create': False,
                'reason': f'Organization limit reached. Your {user.subscription_tier} tier allows {max_allowed} organization(s). You currently own {current_org_count}.',
                'current_count': current_org_count,
                'max_allowed': max_allowed,
                'subscription_tier': user.subscription_tier
            }

        return {
            'can_create': True,
            'reason': 'Organization creation allowed',
            'current_count': current_org_count,
            'max_allowed': max_allowed,
            'subscription_tier': user.subscription_tier
        }

    async def get_user_organization_limits(self, user: User) -> Dict[str, Any]:
        """Get user's organization limits and current usage."""
        result = await self.db.execute(
            select(func.count(Organization.id))
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.role == OrganizationRole.OWNER,
                Organization.is_active == True
            )
        )
        current_owned_count = result.scalar() or 0

        # Get total memberships
        result = await self.db.execute(
            select(func.count(OrganizationMember.id))
            .where(OrganizationMember.user_id == user.id)
        )
        total_memberships = result.scalar() or 0

        return {
            'subscription_tier': user.subscription_tier,
            'max_organizations_allowed': user.max_organizations_allowed,
            'current_owned_organizations': current_owned_count,
            'total_memberships': total_memberships,
            'can_create_more': current_owned_count < user.max_organizations_allowed
        }

    async def validate_tier_upgrade_benefits(self, user: User, new_tier: str) -> Dict[str, Any]:
        """
        Calculate the benefits of upgrading to a new tier.

        Args:
            user: Current user
            new_tier: Target tier (pro, enterprise)

        Returns:
            dict with upgrade benefits and validation
        """
        tier_limits = {
            'free': {'max_orgs': 1, 'max_members_per_org': 5, 'storage_gb': 1},
            'pro': {'max_orgs': 5, 'max_members_per_org': 25, 'storage_gb': 10},
            'enterprise': {'max_orgs': -1, 'max_members_per_org': -1, 'storage_gb': 100}  # -1 = unlimited
        }

        current_limits = tier_limits.get(user.subscription_tier, tier_limits['free'])
        new_limits = tier_limits.get(new_tier, tier_limits['free'])

        if new_tier not in tier_limits:
            return {'valid': False, 'reason': 'Invalid tier specified'}

        if new_tier == user.subscription_tier:
            return {'valid': False, 'reason': 'User is already on this tier'}

        # Calculate current usage
        current_usage = await self.get_user_organization_limits(user)

        return {
            'valid': True,
            'current_tier': user.subscription_tier,
            'new_tier': new_tier,
            'current_limits': current_limits,
            'new_limits': new_limits,
            'current_usage': current_usage,
            'benefits': {
                'additional_orgs': new_limits['max_orgs'] - current_limits['max_orgs'] if new_limits['max_orgs'] > 0 else 'unlimited',
                'additional_members_per_org': new_limits['max_members_per_org'] - current_limits['max_members_per_org'] if new_limits['max_members_per_org'] > 0 else 'unlimited',
                'additional_storage': new_limits['storage_gb'] - current_limits['storage_gb']
            }
        }

    async def validate_role_change(
        self,
        organization_id: str,
        requesting_user: User,
        target_user_id: str,
        new_role: OrganizationRole
    ) -> Dict[str, Any]:
        """
        Validate if a user can change another user's role.

        Args:
            organization_id: Organization ID
            requesting_user: User making the change
            target_user_id: User whose role is being changed
            new_role: New role to assign

        Returns:
            dict with 'can_change' boolean and 'reason' string
        """
        # Get requesting user's role
        result = await self.db.execute(
            select(OrganizationMember.role)
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == requesting_user.id
            )
        )
        requesting_role = result.scalar_one_or_none()

        if not requesting_role:
            return {'can_change': False, 'reason': 'User is not a member of this organization'}

        # Get target user's current role
        result = await self.db.execute(
            select(OrganizationMember.role)
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == target_user_id
            )
        )
        current_role = result.scalar_one_or_none()

        if not current_role:
            return {'can_change': False, 'reason': 'Target user is not a member of this organization'}

        # Role hierarchy validation
        role_hierarchy = {
            OrganizationRole.MEMBER: 0,
            OrganizationRole.ORG_ADMIN: 1,
            OrganizationRole.ADMIN: 2,  # Legacy role
            OrganizationRole.OWNER: 3
        }

        requesting_level = role_hierarchy.get(requesting_role, 0)
        current_level = role_hierarchy.get(current_role, 0)
        new_level = role_hierarchy.get(new_role, 0)

        # System admin can change any role
        if requesting_user.role.value == "admin":
            return {'can_change': True, 'reason': 'System admin has full permissions'}

        # Users cannot change their own role
        if requesting_user.id == target_user_id:
            return {'can_change': False, 'reason': 'Users cannot change their own role'}

        # Only owners can promote to owner or demote owners
        if new_role == OrganizationRole.OWNER or current_role == OrganizationRole.OWNER:
            if requesting_role != OrganizationRole.OWNER:
                return {
                    'can_change': False,
                    'reason': 'Only organization owners can promote to owner or demote owners'
                }

        # Users can only change roles at or below their level (except for owners)
        if requesting_level <= max(current_level, new_level) and requesting_role != OrganizationRole.OWNER:
            return {
                'can_change': False,
                'reason': f'Insufficient permissions. {requesting_role.value} cannot manage {max(current_role, new_role).value} roles'
            }

        # ORG_ADMIN specific restrictions
        if requesting_role == OrganizationRole.ORG_ADMIN:
            # ORG_ADMIN cannot promote to owner or demote owners
            if new_role == OrganizationRole.OWNER or current_role == OrganizationRole.OWNER:
                return {
                    'can_change': False,
                    'reason': 'ORG_ADMIN cannot promote users to owner or demote owners'
                }

        return {
            'can_change': True,
            'reason': 'Role change permitted',
            'requesting_role': requesting_role.value,
            'current_role': current_role.value,
            'new_role': new_role.value
        }