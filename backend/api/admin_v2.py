"""
Admin API Endpoints v2 - Database-integrated version

Provides endpoints for:
- Database-integrated document upload (to MinIO + PostgreSQL)
- Document processing with database chunks
- User-scoped document management
- Document statistics and monitoring
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Document, DocumentStatus, User, Organization
from services.document_service import get_document_service
from api.auth import get_current_user, get_current_admin_user, get_current_organization

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Pydantic models
class DocumentResponse(BaseModel):
    """Document information response"""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    upload_date: datetime
    processed_date: Optional[datetime] = None
    error_message: Optional[str] = None
    total_chunks: Optional[int] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_document(cls, doc: Document) -> "DocumentResponse":
        """Create response from Document model"""
        total_chunks = None
        if doc.document_metadata and "total_chunks" in doc.document_metadata:
            total_chunks = doc.document_metadata["total_chunks"]

        return cls(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            upload_date=doc.upload_date,
            processed_date=doc.processed_date,
            error_message=doc.error_message,
            total_chunks=total_chunks
        )


class UploadResponse(BaseModel):
    """Response for document upload"""
    success: bool
    message: str
    documents: List[DocumentResponse] = []
    errors: List[Dict[str, str]] = []


class ProcessingResponse(BaseModel):
    """Response for document processing"""
    success: bool
    message: str
    session_id: str
    processed_count: int
    failed_count: int
    details: List[Dict[str, str]] = []


class DocumentStatsResponse(BaseModel):
    """Document statistics response"""
    total_documents: int
    total_chunks: int
    documents_by_status: Dict[str, int]
    last_updated: str


class ProcessingRequest(BaseModel):
    """Request to process documents"""
    document_ids: List[str] = Field(..., min_items=1)
    force_reprocess: bool = False


# Utility functions
async def process_documents_background(
    document_ids: List[str],
    session: AsyncSession,
    force_reprocess: bool = False
):
    """Background task for processing documents"""
    service = get_document_service()

    processed_count = 0
    failed_count = 0

    for doc_id in document_ids:
        try:
            # Check if document exists and needs processing
            from sqlalchemy import select
            result = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.warning(f"Document not found for processing: {doc_id}")
                failed_count += 1
                continue

            if document.status == DocumentStatus.INDEXED and not force_reprocess:
                logger.info(f"Document already processed, skipping: {doc_id}")
                continue

            # Reset status if force reprocessing
            if force_reprocess and document.status == DocumentStatus.INDEXED:
                document.status = DocumentStatus.PENDING
                await session.commit()

            # Process the document
            success = await service.process_document(doc_id, session)
            if success:
                processed_count += 1
                logger.info(f"Document processed successfully: {doc_id}")
            else:
                failed_count += 1
                logger.error(f"Document processing failed: {doc_id}")

        except Exception as e:
            failed_count += 1
            logger.error(f"Error processing document {doc_id}: {e}")

    logger.info(f"Background processing completed: {processed_count} processed, {failed_count} failed")


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
        session,
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
    success = await service.delete_document(document_id, session)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return {"message": f"Document {document_id} deleted successfully"}


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
        session,
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