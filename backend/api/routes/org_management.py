"""
Organization Management API Endpoints - For /org dashboard

Provides organization-level endpoints for:
- Organization-scoped document management
- Member management (invite, remove, change roles)
- Organization audit trail
- Organization settings and configuration

Access: Organization members with appropriate roles (OWNER, ORG_ADMIN, MEMBER)
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import Document, User, Organization, OrganizationMember
from backend.services.document_service import get_document_service
from backend.services.auth.authorization_service import (
    get_current_organization_dep,
    get_current_organization_admin_dep,
    get_current_organization_owner_dep,
    get_current_organization_member_dep
)

from backend.api.request_response.DocumentReqResp import (
    DocumentResponse,
    UploadResponse,
    ProcessingResponse,
    DocumentStatsResponse,
    ProcessingRequest
)

from backend.api.helper.DocumentHelper import process_documents_background

logger = logging.getLogger(__name__)

# Create router with /api/org prefix
router = APIRouter(prefix="/api/org", tags=["organization"])


# Document Management Endpoints (Organization-scoped)

@router.post("/documents/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_org_documents(
    files: List[UploadFile] = File(...),
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
) -> UploadResponse:
    """
    Upload documents to organization's knowledge base

    - Accessible to all organization members
    - Files are scoped to current organization
    - Returns document metadata
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    service = get_document_service()

    uploaded_documents = []
    errors = []

    # Generate session ID for this upload batch
    upload_session_id = f"upload_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Get user information from organization membership
    current_user_membership = getattr(organization, '_current_user_membership', None)
    if not current_user_membership:
        raise HTTPException(status_code=500, detail="Could not determine current user from organization context")

    user_id = current_user_membership.user_id
    organization_id = organization.id

    for file in files:
        try:
            document = await service.upload_document(
                file=file,
                user_id=user_id,
                organization_id=organization_id,
                session=db,
                session_id=upload_session_id
            )

            uploaded_documents.append(DocumentResponse.from_document(document))
            logger.info(f"Document uploaded to org {organization_id}: {document.id} ({file.filename})")

        except HTTPException as e:
            errors.append({
                "filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": f"Upload failed: {str(e)}"
            })

    if not uploaded_documents:
        raise HTTPException(
            status_code=400,
            detail=f"No files uploaded successfully. Errors: {errors}"
        )

    return UploadResponse(
        success=True,
        message=f"Uploaded {len(uploaded_documents)} documents to organization" + (
            f" ({len(errors)} failed)" if errors else ""
        ),
        documents=uploaded_documents,
        errors=errors
    )


@router.post("/documents/process", response_model=ProcessingResponse)
async def process_org_documents(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
) -> ProcessingResponse:
    """
    Process uploaded documents in organization

    - Accessible to all organization members
    - Only processes documents within current organization
    """

    # Validate that all documents belong to current organization
    from sqlalchemy import select, and_
    result = await db.execute(
        select(Document.id).where(
            and_(
                Document.id.in_(request.document_ids),
                Document.organization_id != organization.id
            )
        )
    )
    unauthorized_docs = result.scalars().all()

    if unauthorized_docs:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to documents not in your organization: {unauthorized_docs}"
        )

    # Generate processing session ID
    processing_session_id = f"process_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Start background processing
    background_tasks.add_task(
        process_documents_background,
        request.document_ids,
        db,
        request.force_reprocess
    )

    return ProcessingResponse(
        success=True,
        message=f"Processing started for {len(request.document_ids)} documents",
        session_id=processing_session_id,
        processed_count=0,  # Will be updated in background
        failed_count=0,
        details=[{"status": "Processing started in background"}]
    )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_org_documents(
    skip: int = 0,
    limit: int = 100,
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
) -> List[DocumentResponse]:
    """List documents in current organization"""

    from sqlalchemy import select

    result = await db.execute(
        select(Document)
        .where(Document.organization_id == organization.id)
        .order_by(Document.upload_date.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()

    return [DocumentResponse.from_document(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_org_document(
    document_id: str,
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Get specific document details within organization"""

    from sqlalchemy import select, and_

    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.organization_id == organization.id
            )
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found in your organization")

    return DocumentResponse.from_document(document)


@router.delete("/documents/{document_id}")
async def delete_org_document(
    document_id: str,
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
):
    """Delete document within organization (all members can delete their own docs)"""

    from sqlalchemy import select, and_

    # Get current user from membership
    current_user_membership = getattr(organization, '_current_user_membership', None)
    if not current_user_membership:
        raise HTTPException(status_code=500, detail="Could not determine current user")

    user_id = current_user_membership.user_id

    # Members can only delete their own documents, admins and owners can delete any
    if current_user_membership.role.value == "MEMBER":
        where_clause = and_(
            Document.id == document_id,
            Document.organization_id == organization.id,
            Document.user_id == user_id
        )
    else:
        # ORG_ADMIN and OWNER can delete any document in organization
        where_clause = and_(
            Document.id == document_id,
            Document.organization_id == organization.id
        )

    result = await db.execute(
        select(Document).where(where_clause)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    service = get_document_service()
    success = await service.delete_document(document_id, db)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return {"message": f"Document {document.original_filename} deleted successfully"}


@router.post("/documents/{document_id}/reprocess")
async def reprocess_org_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a specific document within organization"""

    from sqlalchemy import select, and_

    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.organization_id == organization.id
            )
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found in your organization")

    # Start background reprocessing
    background_tasks.add_task(
        process_documents_background,
        [document_id],
        db,
        force_reprocess=True
    )

    return {"message": f"Reprocessing started for document {document_id}"}


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_org_document_stats(
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
) -> DocumentStatsResponse:
    """Get document statistics for current organization"""

    # Get organization-specific stats
    from sqlalchemy import select, func

    # Count documents by status in this organization
    stats_result = await db.execute(
        select(
            Document.status,
            func.count(Document.id)
        )
        .where(Document.organization_id == organization.id)
        .group_by(Document.status)
    )
    status_counts = dict(stats_result.all())

    # Get total counts
    total_docs = await db.scalar(
        select(func.count(Document.id))
        .where(Document.organization_id == organization.id)
    )

    # Get total chunks (approximate)
    from backend.database.models import DocumentChunk
    total_chunks = await db.scalar(
        select(func.count(DocumentChunk.id))
        .join(Document)
        .where(Document.organization_id == organization.id)
    )

    # Get last updated
    last_updated_result = await db.execute(
        select(func.max(Document.processed_date))
        .where(Document.organization_id == organization.id)
    )
    last_updated = last_updated_result.scalar_one_or_none()

    return DocumentStatsResponse(
        total_documents=total_docs or 0,
        total_chunks=total_chunks or 0,
        documents_by_status=status_counts,
        last_updated=last_updated,
        additional_info={"organization_id": organization.id}
    )


# Member Management Endpoints

@router.get("/members", response_model=List[dict])
async def list_org_members(
    organization: Organization = Depends(get_current_organization_member_dep),
    db: AsyncSession = Depends(get_db)
):
    """List all members in current organization"""

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == organization.id)
        .options(selectinload(OrganizationMember.user))
        .order_by(OrganizationMember.joined_at.desc())
    )
    memberships = result.scalars().all()

    return [{
        "id": membership.id,
        "user_id": membership.user_id,
        "email": membership.user.email,
        "username": membership.user.username,
        "full_name": membership.user.full_name,
        "role": membership.role.value,
        "joined_at": membership.joined_at,
        "invited_by": membership.invited_by
    } for membership in memberships]


@router.post("/members/invite")
async def invite_org_member(
    email: str,
    role: str = "MEMBER",
    organization: Organization = Depends(get_current_organization_admin_dep),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new member to organization (ORG_ADMIN and OWNER only)"""

    # TODO: Implement invitation logic
    # This would create an OrganizationInvitation record and send an email

    return {
        "message": f"Invitation sent to {email} with role {role}",
        "invitation_id": "placeholder"  # Would be real invitation ID
    }


@router.post("/members/{member_id}/change-role")
async def change_member_role(
    member_id: str,
    new_role: str,
    organization: Organization = Depends(get_current_organization_owner_dep),
    db: AsyncSession = Depends(get_db)
):
    """Change member role (OWNER only)"""

    from sqlalchemy import select, and_

    # Validate new role
    from backend.database.models import OrganizationRole
    try:
        new_role_enum = OrganizationRole(new_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {new_role}")

    # Find the membership
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == organization.id
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # Update role
    membership.role = new_role_enum
    await db.commit()
    await db.refresh(membership)

    return {"message": f"Member role changed to {new_role}"}


@router.delete("/members/{member_id}")
async def remove_org_member(
    member_id: str,
    organization: Organization = Depends(get_current_organization_admin_dep),
    db: AsyncSession = Depends(get_db)
):
    """Remove member from organization (ORG_ADMIN and OWNER only)"""

    from sqlalchemy import select, and_

    # Find the membership
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == organization.id
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # Don't allow removing the organization owner
    if membership.role.value == "OWNER":
        raise HTTPException(status_code=403, detail="Cannot remove organization owner")

    # Remove membership
    await db.delete(membership)
    await db.commit()

    return {"message": "Member removed from organization"}


# Organization Settings

@router.get("/settings")
async def get_org_settings(
    organization: Organization = Depends(get_current_organization_member_dep)
):
    """Get organization settings and info"""

    return {
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "description": organization.description,
            "website": organization.website,
            "industry": organization.industry,
            "size": organization.size,
            "timezone": organization.timezone,
            "tier_type": organization.tier_type,
            "subscription_plan": organization.subscription_plan,
            "subscription_status": organization.subscription_status,
            "created_at": organization.created_at
        },
        "user_role": getattr(organization, '_current_user_membership', None).role.value if hasattr(organization, '_current_user_membership') else None
    }


@router.put("/settings")
async def update_org_settings(
    name: str = None,
    description: str = None,
    website: str = None,
    industry: str = None,
    timezone: str = None,
    organization: Organization = Depends(get_current_organization_admin_dep),
    db: AsyncSession = Depends(get_db)
):
    """Update organization settings (ORG_ADMIN and OWNER only)"""

    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if website is not None:
        updates["website"] = website
    if industry is not None:
        updates["industry"] = industry
    if timezone is not None:
        updates["timezone"] = timezone

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    # Update organization
    for field, value in updates.items():
        setattr(organization, field, value)

    organization.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(organization)

    return {"message": "Organization settings updated successfully", "updated_fields": list(updates.keys())}