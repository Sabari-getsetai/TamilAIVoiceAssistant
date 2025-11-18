"""
System Admin API Endpoints - For /admin dashboard

Provides system-wide administration endpoints for:
- System-wide document management
- User management across all organizations
- System configuration and monitoring
- Global audit trail access
- Infrastructure health monitoring

Access: ADMIN and SUPERADMIN roles only
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import Document, User, Organization
from backend.services.document_service import get_document_service
from backend.services.auth.authorization_service import get_current_system_admin_user_dep

from backend.api.request_response.DocumentReqResp import (
    DocumentResponse,
    DocumentStatsResponse
)

logger = logging.getLogger(__name__)

# Create router with /api/admin prefix
router = APIRouter(prefix="/api/admin", tags=["system-admin"])


@router.get("/documents", response_model=List[DocumentResponse])
async def list_all_system_documents(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
) -> List[DocumentResponse]:
    """List all documents across all organizations (system admin only)"""

    service = get_document_service()
    documents = await service.get_user_documents(
        user_id=None,  # Get all documents
        session=db,
        skip=skip,
        limit=limit
    )

    return [DocumentResponse.from_document(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_any_document(
    document_id: str,
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Get any document details (system admin only)"""

    from sqlalchemy import select

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.from_document(document)


@router.delete("/documents/{document_id}")
async def delete_any_document(
    document_id: str,
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
):
    """Delete any document (system admin only)"""

    from sqlalchemy import select

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    service = get_document_service()
    success = await service.delete_document(document_id, db)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return {"message": f"Document {document.original_filename} deleted successfully"}


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_system_document_stats(
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
) -> DocumentStatsResponse:
    """Get document statistics for entire system (system admin only)"""

    service = get_document_service()
    stats = await service.get_document_stats(
        user_id=None,  # All users
        session=db
    )

    return DocumentStatsResponse(**stats)


@router.get("/users", response_model=List[dict])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
):
    """List all users in the system (system admin only)"""

    from sqlalchemy import select

    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()

    return [{
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "subscription_tier": user.subscription_tier,
        "created_at": user.created_at,
        "last_login": user.last_login
    } for user in users]


@router.get("/organizations", response_model=List[dict])
async def list_all_organizations(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
):
    """List all organizations in the system (system admin only)"""

    from sqlalchemy import select

    result = await db.execute(
        select(Organization)
        .order_by(Organization.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    organizations = result.scalars().all()

    return [{
        "id": org.id,
        "name": org.name,
        "description": org.description,
        "size": org.size,
        "tier_type": org.tier_type,
        "subscription_plan": org.subscription_plan,
        "subscription_status": org.subscription_status,
        "is_active": org.is_active,
        "created_at": org.created_at,
        "creator_id": org.creator_id
    } for org in organizations]


@router.get("/system-info")
async def get_system_info(
    current_admin: User = Depends(get_current_system_admin_user_dep),
    db: AsyncSession = Depends(get_db)
):
    """Get system information and statistics (system admin only)"""

    from sqlalchemy import select, func

    # Get counts for various entities
    users_count = await db.scalar(select(func.count(User.id)))
    orgs_count = await db.scalar(select(func.count(Organization.id)))
    docs_count = await db.scalar(select(func.count(Document.id)))

    # Get active users count
    active_users_count = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )

    # Get active organizations count
    active_orgs_count = await db.scalar(
        select(func.count(Organization.id)).where(Organization.is_active == True)
    )

    return {
        "system_statistics": {
            "total_users": users_count,
            "active_users": active_users_count,
            "total_organizations": orgs_count,
            "active_organizations": active_orgs_count,
            "total_documents": docs_count
        },
        "admin_info": {
            "admin_user_id": current_admin.id,
            "admin_email": current_admin.email,
            "admin_role": current_admin.role.value
        },
        "timestamp": datetime.utcnow().isoformat()
    }