"""
Organization management API endpoints.

This module provides REST API endpoints for:
- Organization CRUD operations
- Organization membership management
- Organization switching and context
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func

from backend.database.connection import get_db
from backend.database.models import Organization, OrganizationMember, User, OrganizationRole
from backend.services.organization_service import OrganizationService
from backend.api.request_response.OrganizationReqResp import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
    OrganizationResponse,
    OrganizationMemberResponse,
    InviteMemberRequest,
    UpdateMemberRoleRequest)

from backend.services.auth import (
    get_current_user_dep as get_current_user
)

from backend.api.helper.OrganizationHelper import (
    check_organization_permission,
    get_user_organization_role,
    has_org_admin_permission
)


# Router setup
router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new organization."""
    try:
        # Validate tier-based organization creation limits
        org_service = OrganizationService(db)
        validation = await org_service.validate_organization_creation(current_user)

        if not validation['can_create']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=validation['reason']
            )

        # Create organization
        organization = Organization(
            id=str(uuid4()),
            name=request.name,
            description=request.description,
            website=request.website,
            industry=request.industry,
            size=request.size,
            timezone=request.timezone,
            creator_id=current_user.id,
            billing_email=request.billing_email or current_user.email,
            settings={}
        )
        
        db.add(organization)
        await db.flush()  # Get the organization ID
        
        # Add creator as organization owner
        membership = OrganizationMember(
            id=str(uuid4()),
            organization_id=organization.id,
            user_id=current_user.id,
            role=OrganizationRole.OWNER,
            invited_by=current_user.id
        )
        
        db.add(membership)
        
        # Set as user's active organization if they don't have one
        if not current_user.active_organization_id:
            current_user.active_organization_id = organization.id
        
        await db.commit()
        await db.refresh(organization)
        
        # Return organization with user role
        response = OrganizationResponse.model_validate(organization)
        response.member_count = 1
        response.user_role = OrganizationRole.OWNER.value
        
        return response
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List organizations the user has access to."""
    try:
        if current_user.role.value == "admin":
            # System admins can see all organizations
            result = await db.execute(
                select(Organization)
                .options(selectinload(Organization.members))
                .where(Organization.is_active == True)
                .order_by(Organization.name)
            )
            organizations = result.scalars().all()
            user_memberships = {}
        else:
            # Regular users see only their organizations
            result = await db.execute(
                select(Organization, OrganizationMember.role)
                .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
                .options(selectinload(Organization.members))
                .where(
                    and_(
                        OrganizationMember.user_id == current_user.id,
                        Organization.is_active == True
                    )
                )
                .order_by(Organization.name)
            )
            org_role_pairs = result.all()
            organizations = [pair[0] for pair in org_role_pairs]
            user_memberships = {pair[0].id: pair[1] for pair in org_role_pairs}
        
        # Build response with member counts and user roles
        response = []
        for org in organizations:
            org_response = OrganizationResponse.model_validate(org)
            org_response.member_count = len(org.members)
            # Convert enum to string value
            role = user_memberships.get(org.id)
            if role:
                org_response.user_role = role.value if hasattr(role, 'value') else str(role)
            elif current_user.role.value == "admin":
                org_response.user_role = "admin"
            response.append(org_response)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}"
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization details."""
    try:
        # Check permission
        has_permission = await check_organization_permission(db, current_user, organization_id)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Get organization
        result = await db.execute(
            select(Organization)
            .options(selectinload(Organization.members))
            .where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user's role
        user_role = await get_user_organization_role(db, current_user.id, organization_id)
        if not user_role and current_user.role.value == "admin":
            user_role = "admin"
        
        # Build response
        response = OrganizationResponse.model_validate(organization)
        response.member_count = len(organization.members)
        # Convert enum to string value
        if user_role:
            response.user_role = user_role.value if hasattr(user_role, 'value') else str(user_role)
        else:
            response.user_role = "admin"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}"
        )


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    request: UpdateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update organization details."""
    try:
        # Check permission (admin, org_admin, or owner required)
        has_permission = await check_organization_permission(
            db, current_user, organization_id, [OrganizationRole.ADMIN, OrganizationRole.ORG_ADMIN, OrganizationRole.OWNER]
        )
        if not has_permission and current_user.role.value != "admin":
            # Get user's role for detailed permission checking
            user_role = await get_user_organization_role(db, current_user.id, organization_id)
            if not user_role or not has_org_admin_permission(user_role, "update_organization"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update organization"
                )
        
        # Get organization
        result = await db.execute(
            select(Organization)
            .options(selectinload(Organization.members))
            .where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)
        
        organization.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(organization)
        
        # Get user's role
        user_role = await get_user_organization_role(db, current_user.id, organization_id)
        if not user_role and current_user.role.value == "admin":
            user_role = "admin"
        
        # Build response
        response = OrganizationResponse.model_validate(organization)
        response.member_count = len(organization.members)
        # Convert enum to string value
        if user_role:
            response.user_role = user_role.value if hasattr(user_role, 'value') else str(user_role)
        else:
            response.user_role = "admin"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete organization (soft delete)."""
    try:
        # Check permission (owner or system admin required)
        has_permission = await check_organization_permission(
            db, current_user, organization_id, [OrganizationRole.OWNER]
        )
        if not has_permission and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners or system admins can delete organizations"
            )
        
        # Get organization
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Soft delete
        organization.is_active = False
        organization.updated_at = datetime.utcnow()
        
        # Clear active organization for users who had this as active
        await db.execute(
            select(User).where(User.active_organization_id == organization_id)
        )
        users_result = await db.execute(
            select(User).where(User.active_organization_id == organization_id)
        )
        users = users_result.scalars().all()
        for user in users:
            user.active_organization_id = None
        
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )


@router.post("/{organization_id}/switch", status_code=status.HTTP_200_OK)
async def switch_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Switch user's active organization."""
    try:
        # Check permission
        has_permission = await check_organization_permission(db, current_user, organization_id)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Verify organization exists and is active
        result = await db.execute(
            select(Organization).where(
                and_(
                    Organization.id == organization_id,
                    Organization.is_active == True
                )
            )
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or inactive"
            )
        
        # Update user's active organization
        current_user.active_organization_id = organization_id
        await db.commit()
        
        return {"message": "Organization switched successfully", "organization_id": organization_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch organization: {str(e)}"
        )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List organization members."""
    try:
        # Check permission
        has_permission = await check_organization_permission(db, current_user, organization_id)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Get members
        result = await db.execute(
            select(OrganizationMember, User)
            .join(User, OrganizationMember.user_id == User.id)
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.joined_at)
        )
        member_user_pairs = result.all()
        
        # Build response
        response = []
        for member, user in member_user_pairs:
            member_response = OrganizationMemberResponse(
                id=member.id,
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                role=member.role.value,
                joined_at=member.joined_at
            )
            response.append(member_response)
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organization members: {str(e)}"
        )


@router.get("/limits", response_model=dict)
async def get_user_organization_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's organization limits and current usage."""
    try:
        org_service = OrganizationService(db)
        limits = await org_service.get_user_organization_limits(current_user)
        return limits

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization limits: {str(e)}"
        )


@router.post("/{organization_id}/members/invite", response_model=dict, status_code=status.HTTP_201_CREATED)
async def invite_member(
    organization_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new member to the organization."""
    try:
        # Check permission (admin, org_admin, or owner required)
        has_permission = await check_organization_permission(
            db, current_user, organization_id,
            [OrganizationRole.ADMIN, OrganizationRole.ORG_ADMIN, OrganizationRole.OWNER]
        )
        if not has_permission and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite members"
            )

        # Validate role assignment using organization service
        org_service = OrganizationService(db)
        role_validation = await org_service.validate_role_change(
            organization_id, current_user, "new_user", request.role
        )

        # Special handling for new user invitation
        requesting_user_role = await get_user_organization_role(db, current_user.id, organization_id)
        if requesting_user_role == OrganizationRole.ORG_ADMIN:
            # ORG_ADMIN cannot invite users with owner role
            if request.role == OrganizationRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="ORG_ADMIN cannot invite users with owner role"
                )

        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email address not found"
            )

        # Check if user is already a member
        result = await db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.user_id == target_user.id
                )
            )
        )
        existing_membership = result.scalar_one_or_none()

        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization"
            )

        # Create membership
        membership = OrganizationMember(
            id=str(uuid4()),
            organization_id=organization_id,
            user_id=target_user.id,
            role=request.role,
            invited_by=current_user.id
        )

        db.add(membership)
        await db.commit()
        await db.refresh(membership)

        return {
            "message": "Member invited successfully",
            "member_id": membership.id,
            "user_email": request.email,
            "role": request.role.value
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite member: {str(e)}"
        )


@router.put("/{organization_id}/members/{member_id}/role", response_model=dict)
async def update_member_role(
    organization_id: str,
    member_id: str,
    request: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a member's role in the organization."""
    try:
        # Check permission (admin, org_admin, or owner required)
        has_permission = await check_organization_permission(
            db, current_user, organization_id,
            [OrganizationRole.ADMIN, OrganizationRole.ORG_ADMIN, OrganizationRole.OWNER]
        )
        if not has_permission and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update member roles"
            )

        # Get member details
        result = await db.execute(
            select(OrganizationMember, User).join(User, OrganizationMember.user_id == User.id)
            .where(
                and_(
                    OrganizationMember.id == member_id,
                    OrganizationMember.organization_id == organization_id
                )
            )
        )
        member_user = result.first()

        if not member_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        member, target_user = member_user

        # Validate role change using organization service
        org_service = OrganizationService(db)
        validation = await org_service.validate_role_change(
            organization_id, current_user, target_user.id, request.role
        )

        if not validation['can_change']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=validation['reason']
            )

        # Update role
        member.role = request.role
        await db.commit()

        return {
            "message": "Member role updated successfully",
            "member_id": member_id,
            "user_email": target_user.email,
            "old_role": validation['current_role'],
            "new_role": request.role.value
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}"
        )


@router.delete("/{organization_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    organization_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from the organization."""
    try:
        # Check permission (admin, org_admin, or owner required)
        has_permission = await check_organization_permission(
            db, current_user, organization_id,
            [OrganizationRole.ADMIN, OrganizationRole.ORG_ADMIN, OrganizationRole.OWNER]
        )
        if not has_permission and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove members"
            )

        # Get member details
        result = await db.execute(
            select(OrganizationMember, User).join(User, OrganizationMember.user_id == User.id)
            .where(
                and_(
                    OrganizationMember.id == member_id,
                    OrganizationMember.organization_id == organization_id
                )
            )
        )
        member_user = result.first()

        if not member_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        member, target_user = member_user

        # Get requesting user's role
        requesting_role = await get_user_organization_role(db, current_user.id, organization_id)

        # Validate removal permissions
        if requesting_role == OrganizationRole.ORG_ADMIN:
            # ORG_ADMIN cannot remove owners
            if member.role == OrganizationRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="ORG_ADMIN cannot remove organization owners"
                )

        # Users cannot remove themselves (prevents organization lockout)
        if current_user.id == target_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself from the organization"
            )

        # Check if this is the last owner (prevent organization orphaning)
        if member.role == OrganizationRole.OWNER:
            result = await db.execute(
                select(func.count(OrganizationMember.id))
                .where(
                    and_(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.role == OrganizationRole.OWNER
                    )
                )
            )
            owner_count = result.scalar()

            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last owner of the organization"
                )

        # Clear active organization if this user had this org as active
        if target_user.active_organization_id == organization_id:
            target_user.active_organization_id = None

        # Remove membership
        await db.delete(member)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )
