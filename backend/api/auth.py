"""
Authentication API endpoints for Tamil AI Voice Assistant

Provides JWT-based authentication with:
- User registration and login
- Token refresh mechanism
- Protected endpoints
- Password validation
- User profile management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field, validator
import bcrypt
from jose import jwt, JWTError
from uuid import uuid4

from database.connection import get_db
from database.models import User, UserRole, Organization, OrganizationMember, OrganizationRole, generate_uuid, utc_now
from settings import settings

# Security scheme
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)

    @validator("username")
    def validate_username(cls, v):
        """Validate username format"""
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        return v.lower()

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """User login request schema"""
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds


class UserResponse(BaseModel):
    """User profile response schema"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class OrganizationCreateRequest(BaseModel):
    """Organization creation request schema"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: str = Field("startup", pattern="^(startup|small|medium|large|enterprise)$")
    timezone: str = Field("UTC", max_length=50)

    @validator("name")
    def validate_name(cls, v):
        """Validate organization name format"""
        if not v.strip():
            raise ValueError("Organization name cannot be empty")
        return v.strip()


class OrganizationResponse(BaseModel):
    """Organization response schema"""
    id: str
    name: str
    description: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    size: str
    timezone: str
    creator_id: str
    is_active: bool
    subscription_plan: str
    subscription_status: str
    created_at: datetime
    current_user_role: Optional[OrganizationRole] = None

    class Config:
        from_attributes = True


class SetActiveOrganizationRequest(BaseModel):
    """Set active organization request schema"""
    organization_id: str


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


# Authentication endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new user account"""

    # Check if user already exists
    existing_user = await db.execute(
        select(User).where(
            and_(
                User.email == user_data.email,
                User.username == user_data.username
            )
        )
    )

    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Create new user
    try:
        hashed_password = hash_password(user_data.password)
        new_user = User(
            id=generate_uuid(),
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER,  # Default role
            is_active=True,
            is_verified=False,  # Email verification not implemented yet
            created_at=utc_now(),
            updated_at=utc_now(),
            preferences={}
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return UserResponse.from_orm(new_user)

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT tokens"""

    # Find user by email or username
    user_result = await db.execute(
        select(User).where(
            and_(
                User.is_active == True,
                (User.email == login_data.username_or_email) | (User.username == login_data.username_or_email)
            )
        )
    )
    user = user_result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = utc_now()
    user.updated_at = utc_now()
    await db.commit()

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token"""

    user_id = verify_token(refresh_data.refresh_token, "refresh")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user_result = await db.execute(
        select(User).where(and_(User.id == user_id, User.is_active == True))
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token (optionally new refresh token)
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)  # Issue new refresh token for security

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user's profile information"""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update current user's profile information"""

    # Allow updating specific fields only
    allowed_fields = {"full_name", "preferences"}
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    # Update user fields
    for field, value in update_fields.items():
        setattr(current_user, field, value)

    current_user.updated_at = utc_now()

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should delete tokens)"""
    # In a more sophisticated setup, we would maintain a token blacklist
    # For now, we just return success - client should delete tokens
    return {"message": "Successfully logged out"}


# Organization endpoints
@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrganizationResponse:
    """Create a new organization"""

    # Check if organization name already exists
    existing_org = await db.execute(
        select(Organization).where(Organization.name == org_data.name)
    )

    if existing_org.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )

    try:
        # Create organization
        new_org = Organization(
            id=generate_uuid(),
            name=org_data.name,
            description=org_data.description,
            website=org_data.website,
            industry=org_data.industry,
            size=org_data.size,
            timezone=org_data.timezone,
            creator_id=current_user.id,
            created_at=utc_now(),
            updated_at=utc_now()
        )

        db.add(new_org)
        await db.flush()  # Get the organization ID

        # Add creator as organization owner
        membership = OrganizationMember(
            id=generate_uuid(),
            organization_id=new_org.id,
            user_id=current_user.id,
            role=OrganizationRole.OWNER,
            joined_at=utc_now()
        )

        db.add(membership)

        # Set as user's active organization
        current_user.active_organization_id = new_org.id
        current_user.updated_at = utc_now()

        await db.commit()
        await db.refresh(new_org)

        # Prepare response with user's role
        org_response = OrganizationResponse.from_orm(new_org)
        org_response.current_user_role = OrganizationRole.OWNER

        return org_response

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating organization"
        )


@router.get("/organizations/my", response_model=list[OrganizationResponse])
async def get_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[OrganizationResponse]:
    """Get all organizations user is a member of"""

    result = await db.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(
            and_(
                OrganizationMember.user_id == current_user.id,
                Organization.is_active == True
            )
        )
        .order_by(Organization.name)
    )

    organizations = []
    for org, role in result.all():
        org_response = OrganizationResponse.from_orm(org)
        org_response.current_user_role = role
        organizations.append(org_response)

    return organizations


@router.put("/organizations/set-active", response_model=dict)
async def set_active_organization(
    request: SetActiveOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set user's active organization"""

    # Verify user is member of the organization
    membership = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, OrganizationMember.organization_id == Organization.id)
        .where(
            and_(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == request.organization_id,
                Organization.is_active == True
            )
        )
    )

    membership_result = membership.first()
    if not membership_result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )

    # Update user's active organization
    current_user.active_organization_id = request.organization_id
    current_user.updated_at = utc_now()

    await db.commit()

    return {"message": "Active organization updated successfully"}


@router.get("/organizations/current", response_model=OrganizationResponse)
async def get_current_organization_details(
    organization: Organization = Depends(get_current_organization)
) -> OrganizationResponse:
    """Get current organization details (requires organization membership)"""

    membership = getattr(organization, '_current_user_membership', None)
    org_response = OrganizationResponse.from_orm(organization)

    if membership:
        org_response.current_user_role = membership.role

    return org_response


@router.get("/auth-status")
async def get_auth_status(
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get authentication and organization status for frontend routing"""

    if not current_user:
        return {
            "authenticated": False,
            "has_organization": False,
            "user": None,
            "organization": None
        }

    # Check if user has organizations
    user_orgs = await db.execute(
        select(Organization)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(
            and_(
                OrganizationMember.user_id == current_user.id,
                Organization.is_active == True
            )
        )
    )

    has_orgs = len(list(user_orgs.scalars().all())) > 0

    # Get active organization if any
    active_org = None
    if current_user.active_organization_id and has_orgs:
        org_result = await db.execute(
            select(Organization, OrganizationMember.role)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                and_(
                    Organization.id == current_user.active_organization_id,
                    OrganizationMember.user_id == current_user.id,
                    Organization.is_active == True
                )
            )
        )

        org_membership = org_result.first()
        if org_membership:
            org, role = org_membership
            active_org = OrganizationResponse.from_orm(org)
            active_org.current_user_role = role

    return {
        "authenticated": True,
        "has_organization": has_orgs,
        "has_active_organization": active_org is not None,
        "user": UserResponse.from_orm(current_user),
        "organization": active_org
    }


# Admin endpoints
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> list[UserResponse]:
    """List all users (admin only)"""

    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()

    return [UserResponse.from_orm(user) for user in users]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user role (admin only)"""

    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = new_role
    user.updated_at = utc_now()

    await db.commit()

    return {"message": f"User role updated to {new_role}"}


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate user account (admin only)"""

    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = is_active
    user.updated_at = utc_now()

    await db.commit()

    status_text = "activated" if is_active else "deactivated"
    return {"message": f"User account {status_text}"}