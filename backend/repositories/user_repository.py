"""
User Repository - Authentication and Organization Data Access Layer

This repository handles all database operations for users, organizations,
and organization memberships, including authentication, role management,
and organization administration.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, asc, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from backend.repositories.base_repository import BaseRepository
from backend.database.models import (
    User, Organization, OrganizationMember, OrganizationInvitation,
    UserRole
)


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self):
        super().__init__(User)

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        hashed_password: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user."""
        user_data = {
            "email": email,
            "username": username,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return await self.create(db, user_data)

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get a user by email address."""
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get user by email {email}: {e}")
            raise

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """Get a user by username."""
        try:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get user by username {username}: {e}")
            raise

    async def get_user_with_organizations(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[User]:
        """Get a user with all their organization memberships loaded."""
        try:
            result = await db.execute(
                select(User)
                .options(selectinload(User.organization_memberships))
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get user with organizations {user_id}: {e}")
            raise

    async def update_password(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        new_hashed_password: str
    ) -> bool:
        """Update user password."""
        try:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    hashed_password=new_hashed_password,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update password for user {user_id}: {e}")
            raise

    async def update_last_login(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """Update user's last login timestamp."""
        try:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_login_at=datetime.utcnow())
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise

    async def activate_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """Activate a user account."""
        try:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=True,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to activate user {user_id}: {e}")
            raise

    async def deactivate_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """Deactivate a user account."""
        try:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise

    async def search_users(
        self,
        db: AsyncSession,
        query: str,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        limit: int = 20
    ) -> List[User]:
        """Search users by email, username, or full name."""
        try:
            search_query = select(User).where(
                or_(
                    User.email.ilike(f"%{query}%"),
                    User.username.ilike(f"%{query}%"),
                    User.full_name.ilike(f"%{query}%")
                )
            )

            if role:
                search_query = search_query.where(User.role == role)

            if is_active is not None:
                search_query = search_query.where(User.is_active == is_active)

            search_query = search_query.order_by(asc(User.email)).limit(limit)

            result = await db.execute(search_query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to search users with query '{query}': {e}")
            raise

    async def get_user_analytics(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user registration and activity analytics."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Total users
            total_result = await db.execute(select(func.count()).select_from(User))
            total_users = total_result.scalar()

            # Active users
            active_result = await db.execute(
                select(func.count()).where(User.is_active == True)
            )
            active_users = active_result.scalar()

            # New users in period
            new_users_result = await db.execute(
                select(func.count()).where(User.created_at >= since_date)
            )
            new_users = new_users_result.scalar()

            # Users by role
            role_result = await db.execute(
                select(User.role, func.count().label('count'))
                .group_by(User.role)
            )
            users_by_role = {row.role.value: row.count for row in role_result}

            # Recent logins
            recent_logins_result = await db.execute(
                select(func.count())
                .where(
                    and_(
                        User.last_login_at >= since_date,
                        User.last_login_at.isnot(None)
                    )
                )
            )
            recent_logins = recent_logins_result.scalar()

            return {
                "period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "new_users": new_users,
                "recent_logins": recent_logins,
                "users_by_role": users_by_role,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get user analytics: {e}")
            raise


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization operations."""

    def __init__(self):
        super().__init__(Organization)

    async def create_organization(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None
    ) -> Organization:
        """Create a new organization."""
        org_data = {
            "name": name,
            "description": description,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return await self.create(db, org_data)

    async def get_organization_with_members(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> Optional[Organization]:
        """Get an organization with all members loaded."""
        try:
            result = await db.execute(
                select(Organization)
                .options(selectinload(Organization.members))
                .where(Organization.id == organization_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get organization with members {organization_id}: {e}")
            raise

    async def get_organizations_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> List[Tuple[Organization, OrganizationMember]]:
        """Get all organizations a user is a member of with their membership info."""
        try:
            result = await db.execute(
                select(Organization, OrganizationMember)
                .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
                .where(OrganizationMember.user_id == user_id)
                .order_by(asc(Organization.name))
            )
            return result.all()
        except Exception as e:
            self.logger.error(f"Failed to get organizations for user {user_id}: {e}")
            raise

    async def search_organizations(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20
    ) -> List[Organization]:
        """Search organizations by name or description."""
        try:
            result = await db.execute(
                select(Organization)
                .where(
                    or_(
                        Organization.name.ilike(f"%{query}%"),
                        Organization.description.ilike(f"%{query}%")
                    )
                )
                .order_by(asc(Organization.name))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to search organizations with query '{query}': {e}")
            raise


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """Repository for OrganizationMember operations."""

    def __init__(self):
        super().__init__(OrganizationMember)

    async def add_member(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "member"
    ) -> OrganizationMember:
        """Add a user to an organization."""
        member_data = {
            "organization_id": organization_id,
            "user_id": user_id,
            "role": role,
            "joined_at": datetime.utcnow()
        }
        return await self.create(db, member_data)

    async def get_member(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[OrganizationMember]:
        """Get a specific organization member."""
        try:
            result = await db.execute(
                select(OrganizationMember)
                .where(
                    and_(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.user_id == user_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get member {user_id} in org {organization_id}: {e}")
            raise

    async def get_members_with_users(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        role: Optional[str] = None
    ) -> List[Tuple[OrganizationMember, User]]:
        """Get all members of an organization with user details."""
        try:
            query = select(OrganizationMember, User).join(
                User, OrganizationMember.user_id == User.id
            ).where(OrganizationMember.organization_id == organization_id)

            if role:
                query = query.where(OrganizationMember.role == role)

            query = query.order_by(asc(User.full_name))

            result = await db.execute(query)
            return result.all()
        except Exception as e:
            self.logger.error(f"Failed to get members for organization {organization_id}: {e}")
            raise

    async def update_member_role(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: str
    ) -> bool:
        """Update a member's role in an organization."""
        try:
            result = await db.execute(
                update(OrganizationMember)
                .where(
                    and_(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.user_id == user_id
                    )
                )
                .values(role=new_role)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update member role: {e}")
            raise

    async def remove_member(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Remove a user from an organization."""
        try:
            result = await db.execute(
                delete(OrganizationMember)
                .where(
                    and_(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.user_id == user_id
                    )
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to remove member: {e}")
            raise

    async def is_member(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Check if a user is a member of an organization."""
        try:
            result = await db.execute(
                select(func.count())
                .where(
                    and_(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.user_id == user_id
                    )
                )
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            self.logger.error(f"Failed to check membership: {e}")
            raise

    async def get_member_count(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> int:
        """Get the total number of members in an organization."""
        try:
            result = await db.execute(
                select(func.count())
                .where(OrganizationMember.organization_id == organization_id)
            )
            return result.scalar()
        except Exception as e:
            self.logger.error(f"Failed to get member count for organization {organization_id}: {e}")
            raise


class OrganizationInvitationRepository(BaseRepository[OrganizationInvitation]):
    """Repository for OrganizationInvitation operations."""

    def __init__(self):
        super().__init__(OrganizationInvitation)

    async def create_invitation(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        email: str,
        role: str,
        invited_by: uuid.UUID,
        expires_at: Optional[datetime] = None
    ) -> OrganizationInvitation:
        """Create a new organization invitation."""
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days default

        invitation_data = {
            "organization_id": organization_id,
            "email": email,
            "role": role,
            "invited_by": invited_by,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        return await self.create(db, invitation_data)

    async def get_pending_invitations(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> List[OrganizationInvitation]:
        """Get all pending invitations for an organization."""
        try:
            result = await db.execute(
                select(OrganizationInvitation)
                .where(
                    and_(
                        OrganizationInvitation.organization_id == organization_id,
                        OrganizationInvitation.accepted_at.is_(None),
                        OrganizationInvitation.expires_at > datetime.utcnow()
                    )
                )
                .order_by(desc(OrganizationInvitation.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get pending invitations for organization {organization_id}: {e}")
            raise

    async def get_invitation_by_email(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        email: str
    ) -> Optional[OrganizationInvitation]:
        """Get a pending invitation by email."""
        try:
            result = await db.execute(
                select(OrganizationInvitation)
                .where(
                    and_(
                        OrganizationInvitation.organization_id == organization_id,
                        OrganizationInvitation.email == email,
                        OrganizationInvitation.accepted_at.is_(None),
                        OrganizationInvitation.expires_at > datetime.utcnow()
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get invitation by email {email}: {e}")
            raise

    async def accept_invitation(
        self,
        db: AsyncSession,
        invitation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Mark an invitation as accepted."""
        try:
            result = await db.execute(
                update(OrganizationInvitation)
                .where(OrganizationInvitation.id == invitation_id)
                .values(
                    accepted_at=datetime.utcnow(),
                    accepted_by=user_id
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to accept invitation {invitation_id}: {e}")
            raise

    async def cleanup_expired_invitations(
        self,
        db: AsyncSession,
        batch_size: int = 100
    ) -> int:
        """Clean up expired invitations."""
        try:
            result = await db.execute(
                delete(OrganizationInvitation)
                .where(
                    and_(
                        OrganizationInvitation.expires_at < datetime.utcnow(),
                        OrganizationInvitation.accepted_at.is_(None)
                    )
                )
            )
            await db.commit()
            deleted_count = result.rowcount

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired invitations")

            return deleted_count
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to cleanup expired invitations: {e}")
            raise