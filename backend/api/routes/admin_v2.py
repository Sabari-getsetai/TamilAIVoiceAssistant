"""
Admin API Endpoints v2 - Database-integrated version

Provides endpoints for:
- Database-integrated document upload (to MinIO + PostgreSQL)
- Document processing with database chunks
- User-scoped document management
- Document statistics and monitoring
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import Document, User, Organization
from backend.services.document_service import get_document_service

from backend.services.auth import (
    get_current_user_dep as get_current_user,
    get_current_admin_user_dep as get_current_admin_user,
    get_current_organization_dep as get_current_organization
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

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])




# API Endpoints

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    organization: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> UploadResponse:
    """
    Upload documents with database integration

    - Saves files to MinIO object storage
    - Creates document records in PostgreSQL
    - Returns document metadata
    - Associates documents with authenticated user
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
            logger.info(f"Document uploaded: {document.id} ({file.filename})")

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
        message=f"Uploaded {len(uploaded_documents)} documents" + (
            f" ({len(errors)} failed)" if errors else ""
        ),
        documents=uploaded_documents,
        errors=errors
    )


@router.post("/process", response_model=ProcessingResponse)
async def process_documents(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProcessingResponse:
    """
    Process uploaded documents

    - Extracts text content
    - Generates text chunks
    - Computes embeddings
    - Stores in database with pgVector
    """

    # Validate that user owns all documents or is admin
    if current_user.role.value != "ADMIN":
        from sqlalchemy import select, and_
        result = await db.execute(
            select(Document.id).where(
                and_(
                    Document.id.in_(request.document_ids),
                    Document.user_id != current_user.id
                )
            )
        )
        unauthorized_docs = result.scalars().all()

        if unauthorized_docs:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to documents: {unauthorized_docs}"
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
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[DocumentResponse]:
    """List documents for current user"""

    service = get_document_service()
    documents = await service.get_user_documents(
        user_id=current_user.id,
        session=db,
        skip=skip,
        limit=limit
    )

    return [DocumentResponse.from_document(doc) for doc in documents]


@router.get("/documents/all", response_model=List[DocumentResponse])
async def list_all_documents(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> List[DocumentResponse]:
    """List all documents (admin only)"""

    service = get_document_service()
    documents = await service.get_user_documents(
        user_id=None,  # Get all documents
        session=db,
        skip=skip,
        limit=limit
    )

    return [DocumentResponse.from_document(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Get specific document details"""

    from sqlalchemy import select, and_

    # Check if user owns document or is admin
    where_clause = Document.id == document_id
    if current_user.role.value != "ADMIN":
        where_clause = and_(where_clause, Document.user_id == current_user.id)

    result = await db.execute(
        select(Document).where(where_clause)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.from_document(document)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete document and all associated data"""

    from sqlalchemy import select, and_

    # Check if user owns document or is admin
    where_clause = Document.id == document_id
    if current_user.role.value != "ADMIN":
        where_clause = and_(where_clause, Document.user_id == current_user.id)

    result = await db.execute(
        select(Document).where(where_clause)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    service = get_document_service()
    success = await service.delete_document(document_id, db)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return {"message": f"Document {document.original_filename} deleted successfully"}


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a specific document"""

    from sqlalchemy import select, and_

    # Check if user owns document or is admin
    where_clause = Document.id == document_id
    if current_user.role.value != "ADMIN":
        where_clause = and_(where_clause, Document.user_id == current_user.id)

    result = await db.execute(
        select(Document).where(where_clause)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Start background reprocessing
    background_tasks.add_task(
        process_documents_background,
        [document_id],
        db,
        force_reprocess=True
    )

    return {"message": f"Reprocessing started for document {document_id}"}


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentStatsResponse:
    """Get document statistics for current user"""

    service = get_document_service()
    stats = await service.get_document_stats(
        user_id=current_user.id,
        session=db
    )

    return DocumentStatsResponse(**stats)


@router.get("/stats/all", response_model=DocumentStatsResponse)
async def get_all_document_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentStatsResponse:
    """Get document statistics for all users (admin only)"""

    service = get_document_service()
    stats = await service.get_document_stats(
        user_id=None,  # All users
        session=db
    )

    return DocumentStatsResponse(**stats)




# Legacy compatibility endpoints (optional)
@router.post("/ingest", deprecated=True)
async def legacy_ingest(
    current_user: User = Depends(get_current_user)
):
    """Legacy ingest endpoint - deprecated, use /upload + /process instead"""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /admin/upload followed by POST /admin/process"
    )


@router.get("/status", deprecated=True)
async def legacy_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Legacy status endpoint - deprecated, use /stats instead"""
    # Redirect to new stats endpoint
    service = get_document_service()
    stats = await service.get_document_stats(
        user_id=current_user.id,
        session=db
    )

    # Convert to legacy format
    return {
        "vector_store_status": "ready" if stats["total_chunks"] > 0 else "empty",
        "total_documents": stats["total_documents"],
        "total_chunks": stats["total_chunks"],
        "documents_by_status": stats["documents_by_status"],
        "last_updated": stats["last_updated"],
        "message": "Migrated to database-integrated document management"
    }