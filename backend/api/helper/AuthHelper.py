"""Authentication and Authorization helper functions"""


from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.database.models import User, Organization, OrganizationMember, UserRole, OrganizationRole
from backend.database import get_db
from backend.settings import settings


# Security scheme
security = HTTPBearer()


# Password utilities
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# JWT utilities
def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": str(uuid4())  # Unique token ID for refresh tokens
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type_claim: str = payload.get("type")

        if user_id is None or token_type_claim != token_type:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    user_id = verify_token(credentials.credentials, "access")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Optional security dependency
optional_security = HTTPBearer(auto_error=False)

# Optional dependency for current user (returns None if not authenticated)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# Admin user dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user has admin privileges"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Organization authentication dependencies
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """
    Get current user's active organization and validate membership.

    CRITICAL: This enforces the "NO APP ACCESS WITHOUT ORG MEMBERSHIP" business rule.
    This dependency should replace get_current_user on ALL protected endpoints.
    """
    # Check if user has an active organization set
    if not current_user.active_organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active organization. Please create or join an organization to access the app.",
            headers={"X-Auth-Error": "NO_ORGANIZATION"}
        )

    # Verify organization exists and user is still a member
    result = await db.execute(
        select(Organization, OrganizationMember)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(
            and_(
                Organization.id == current_user.active_organization_id,
                Organization.is_active == True,
                OrganizationMember.user_id == current_user.id
            )
        )
    )

    org_membership = result.first()

    if not org_membership:
        # User's active organization is invalid (deleted or user removed)
        # Clear the invalid active_organization_id
        current_user.active_organization_id = None
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your organization access has been revoked. Please create or join a new organization.",
            headers={"X-Auth-Error": "ORGANIZATION_ACCESS_REVOKED"}
        )

    organization, membership = org_membership

    # Attach membership info to organization for role-based access
    organization._current_user_membership = membership

    return organization


async def get_current_organization_admin(
    organization: Organization = Depends(get_current_organization)
) -> Organization:
    """Ensure current user has admin privileges in their organization"""
    membership = getattr(organization, '_current_user_membership', None)

    if not membership or membership.role not in [OrganizationRole.ADMIN, OrganizationRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin privileges required"
        )

    return organization


async def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Organization]:
    """Get all organizations user is a member of"""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(
            and_(
                OrganizationMember.user_id == current_user.id,
                Organization.is_active == True
            )
        )
        .order_by(Organization.name)
    )

    return list(result.scalars().all())