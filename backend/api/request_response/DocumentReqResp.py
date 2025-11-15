"""Document request/response schemas"""


from pydantic import BaseModel, Field
from backend.database.models import Document, DocumentStatus, User, Organization
from typing import List, Dict
from datetime import datetime



class DocumentResponse(BaseModel):
    """Document information response"""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    upload_date: datetime

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
