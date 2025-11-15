"""
Authentication API endpoints for Tamil AI Voice Assistant

Provides JWT-based authentication with:
- User registration and login
- Token refresh mechanism
- Protected endpoints
- Password validation
- User profile management
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from backend.database.connection import get_db
from backend.database.models import User, UserRole, Organization, OrganizationMember, OrganizationRole, generate_uuid, utc_now
from backend.settings import settings

from backend.api.request_response.AuthReqResp import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    SetActiveOrganizationRequest
)

from backend.api.helper.AuthHelper import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_admin_user,
    get_current_user_optional,
    get_current_organization
)


# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])



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