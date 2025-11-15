"""Authorization Service - User Dependencies and Access Control

This service handles:
- User authentication dependencies
- Organization membership validation
- Role-based access control
- Admin privilege checking

Replaces: backend.api.helper.AuthHelper (dependency functions)
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.utils.base_service import BaseService
from backend.services.auth.authentication_service import AuthenticationService
from backend.repositories.user_repository import UserRepository, OrganizationRepository, OrganizationMemberRepository
from backend.database.models import User, Organization, OrganizationMember, UserRole, OrganizationRole
from backend.database.connection import get_db


class AuthorizationService(BaseService):
    """Service for authorization and access control operations"""

    def __init__(self):
        super().__init__()
        self.service_name = "AuthorizationService"
        self.auth_service = AuthenticationService()
        self.user_repo = UserRepository()
        self.org_repo = OrganizationRepository()
        self.member_repo = OrganizationMemberRepository()

        # Security schemes
        self.security = HTTPBearer()
        self.optional_security = HTTPBearer(auto_error=False)

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current authenticated user from JWT token

        Args:
            credentials: HTTP Bearer credentials from request
            db: Database session

        Returns:
            User object if authentication successful

        Raises:
            HTTPException: If authentication fails or user not found
        """
        try:
            user_id = self.auth_service.verify_token(credentials.credentials, "access")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get user from database using repository
            user = await self.user_repo.get_by_id(db, user_id)

            if not user:
                self.logger.warning(f"User not found in database: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not user.is_active:
                self.logger.info(f"Inactive user attempted access: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return user

        except HTTPException:
            # Re-raise HTTP exceptions (auth failures)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_current_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    async def get_current_user_optional(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if authenticated, None otherwise

        Args:
            credentials: Optional HTTP Bearer credentials from request
            db: Database session

        Returns:
            User object if authenticated, None if not authenticated or invalid
        """
        if not credentials:
            return None

        try:
            # Use silent verification to avoid exceptions
            user_id = self.auth_service.verify_token_silent(credentials.credentials, "access")

            if not user_id:
                return None

            user = await self.user_repo.get_by_id(db, user_id)

            if not user or not user.is_active:
                return None

            return user

        except Exception as e:
            self.logger.debug(f"Optional authentication failed: {str(e)}")
            return None

    async def get_current_admin_user(
        self,
        current_user: User = Depends("get_current_user")  # Will be resolved by dependency injection
    ) -> User:
        """Ensure current user has admin privileges

        Args:
            current_user: Current authenticated user

        Returns:
            User object if user has admin privileges

        Raises:
            HTTPException: If user lacks admin privileges
        """
        if current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
            self.logger.warning(f"Non-admin user attempted admin access: {current_user.id} ({current_user.role})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        return current_user

    async def get_current_organization(
        self,
        current_user: User = Depends("get_current_user"),  # Will be resolved by dependency injection
        db: AsyncSession = Depends(get_db)
    ) -> Organization:
        """Get current user's active organization and validate membership

        CRITICAL: This enforces the "NO APP ACCESS WITHOUT ORG MEMBERSHIP" business rule.
        This dependency should replace get_current_user on ALL protected endpoints.

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            Organization object with attached membership info

        Raises:
            HTTPException: If user has no organization or membership is invalid
        """
        # Check if user has an active organization set
        if not current_user.active_organization_id:
            self.logger.info(f"User {current_user.id} has no active organization")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active organization. Please create or join an organization to access the app.",
                headers={"X-Auth-Error": "NO_ORGANIZATION"}
            )

        try:
            # Verify organization exists and user is still a member using repositories
            organization = await self.org_repo.get_by_id(db, current_user.active_organization_id)

            if not organization or not organization.is_active:
                # Organization no longer exists or is inactive
                await self._clear_invalid_organization(db, current_user)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your organization is no longer available. Please create or join a new organization.",
                    headers={"X-Auth-Error": "ORGANIZATION_INACTIVE"}
                )

            # Check if user is still a member
            membership = await self.member_repo.get_membership(
                db, current_user.id, current_user.active_organization_id
            )

            if not membership:
                # User no longer has membership
                await self._clear_invalid_organization(db, current_user)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your organization access has been revoked. Please create or join a new organization.",
                    headers={"X-Auth-Error": "ORGANIZATION_ACCESS_REVOKED"}
                )

            # Attach membership info to organization for role-based access
            organization._current_user_membership = membership

            return organization

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            self.logger.error(f"Error validating organization access for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Organization validation failed"
            )

    async def get_current_organization_admin(
        self,
        organization: Organization = Depends("get_current_organization")  # Will be resolved by dependency injection
    ) -> Organization:
        """Ensure current user has admin privileges in their organization

        Args:
            organization: Current organization with attached membership

        Returns:
            Organization object if user has admin privileges

        Raises:
            HTTPException: If user lacks organization admin privileges
        """
        membership = getattr(organization, '_current_user_membership', None)

        if not membership or membership.role not in [OrganizationRole.ADMIN, OrganizationRole.OWNER]:
            self.logger.warning(
                f"Non-admin user attempted org admin access: "
                f"user={getattr(membership, 'user_id', 'unknown')} "
                f"role={getattr(membership, 'role', 'unknown')} "
                f"org={organization.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization admin privileges required"
            )

        return organization

    async def get_user_organizations(
        self,
        current_user: User = Depends("get_current_user"),  # Will be resolved by dependency injection
        db: AsyncSession = Depends(get_db)
    ) -> List[Organization]:
        """Get all organizations user is a member of

        Args:
            current_user: Current authenticated user
            db: Database session

        Returns:
            List of organizations user is a member of
        """
        try:
            return await self.org_repo.get_user_organizations(db, current_user.id)
        except Exception as e:
            self.logger.error(f"Error fetching user organizations for {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user organizations"
            )

    async def check_user_organization_access(
        self,
        user_id: str,
        organization_id: str,
        db: AsyncSession,
        required_role: Optional[OrganizationRole] = None
    ) -> bool:
        """Check if user has access to organization with optional role requirement

        Args:
            user_id: User ID to check
            organization_id: Organization ID to check
            db: Database session
            required_role: Optional minimum role requirement

        Returns:
            True if user has access (and required role if specified)
        """
        try:
            membership = await self.member_repo.get_membership(db, user_id, organization_id)

            if not membership:
                return False

            if required_role:
                # Define role hierarchy for comparison
                role_hierarchy = {
                    OrganizationRole.MEMBER: 1,
                    OrganizationRole.ADMIN: 2,
                    OrganizationRole.OWNER: 3
                }

                user_role_level = role_hierarchy.get(membership.role, 0)
                required_role_level = role_hierarchy.get(required_role, 0)

                return user_role_level >= required_role_level

            return True

        except Exception as e:
            self.logger.error(f"Error checking organization access: {str(e)}")
            return False

    async def _clear_invalid_organization(self, db: AsyncSession, user: User) -> None:
        """Clear user's invalid active organization reference

        Args:
            db: Database session
            user: User object to update
        """
        try:
            user.active_organization_id = None
            await self.user_repo.update(db, user.id, {"active_organization_id": None})
            self.logger.info(f"Cleared invalid organization for user: {user.id}")
        except Exception as e:
            self.logger.error(f"Failed to clear invalid organization for user {user.id}: {str(e)}")


# Dependency factory functions for FastAPI
# These allow the service methods to be used as FastAPI dependencies

def get_authorization_service() -> AuthorizationService:
    """Get authorization service instance"""
    return AuthorizationService()


# Convenience dependency aliases for FastAPI routes
async def get_current_user_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency for current user"""
    return await auth_service.get_current_user(credentials, db)


async def get_current_user_optional_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """FastAPI dependency for optional current user"""
    return await auth_service.get_current_user_optional(credentials, db)


async def get_current_admin_user_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    current_user: User = Depends(get_current_user_dep)
) -> User:
    """FastAPI dependency for admin user"""
    return await auth_service.get_current_admin_user(current_user)


async def get_current_organization_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """FastAPI dependency for current organization"""
    return await auth_service.get_current_organization(current_user, db)


async def get_current_organization_admin_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    organization: Organization = Depends(get_current_organization_dep)
) -> Organization:
    """FastAPI dependency for organization admin"""
    return await auth_service.get_current_organization_admin(organization)


async def get_user_organizations_dep(
    auth_service: AuthorizationService = Depends(get_authorization_service),
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db)
) -> List[Organization]:
    """FastAPI dependency for user organizations"""
    return await auth_service.get_user_organizations(current_user, db)