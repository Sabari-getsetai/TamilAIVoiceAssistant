"""
Document Service - Database-integrated document management

Handles:
- Document upload to MinIO with database metadata
- Document processing and chunking
- Vector embedding generation and storage
- Document lifecycle management
"""

import uuid
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException

from backend.database.models import (
    Document, DocumentChunk, DocumentStatus, User,
    generate_uuid, utc_now
)
from backend.storage.minio_client import get_minio_client, upload_file, delete_file
from backend.rag.loaders import get_document_loader
from backend.rag.chunking import get_text_chunker
from backend.rag.embeddings import get_embedding_model
from backend.settings import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for database-integrated document management"""

    def __init__(self):
        self.minio_client = None
        self.embedding_model = None

    def _get_minio_client(self):
        """Get MinIO client with lazy initialization"""
        if self.minio_client is None:
            self.minio_client = get_minio_client()
        return self.minio_client

    def _get_embedding_model(self):
        """Get embedding model with lazy initialization"""
        if self.embedding_model is None:
            self.embedding_model = get_embedding_model()
            self.embedding_model.load()
        return self.embedding_model

    @staticmethod
    def _validate_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file"""

        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf'}
        file_ext = Path(filename).suffix.lower()

        if file_ext not in allowed_extensions:
            return False, f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024 * 1024):.1f}MB. Max: 10MB"

        # Check filename
        if not filename or filename.startswith('.'):
            return False, "Invalid filename"

        return True, None

    async def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        organization_id: str,
        session: AsyncSession,
        session_id: Optional[str] = None
    ) -> Document:
        """
        Upload document to MinIO and create database record

        Args:
            file: Uploaded file object
            user_id: ID of user uploading the document
            organization_id: ID of organization the document belongs to
            session: Database session
            session_id: Optional session ID for grouping uploads

        Returns:
            Document database record

        Raises:
            HTTPException: If validation fails or upload fails
        """

        # Read file content
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        # Validate file
        is_valid, error_msg = self._validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Generate document metadata
        doc_id = generate_uuid()
        original_filename = file.filename

        # Create unique filename to avoid conflicts
        file_ext = Path(original_filename).suffix
        safe_filename = f"{doc_id}{file_ext}"

        # Generate MinIO key
        minio_key = f"documents/{user_id}/{safe_filename}"

        # Detect content type
        content_type = file.content_type or mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'

        # Determine file type
        file_type = file_ext.upper().lstrip('.')

        try:
            # Upload to MinIO
            minio_client = self._get_minio_client()
            upload_success = upload_file(
                settings.MINIO_DOCUMENTS_BUCKET,
                minio_key,
                BytesIO(content),
                content_type
            )

            if not upload_success:
                raise Exception("MinIO upload failed")

            # Create database record
            document = Document(
                id=doc_id,
                user_id=user_id,
                organization_id=organization_id,
                filename=safe_filename,
                original_filename=original_filename,
                minio_key=minio_key,
                file_size=file_size,
                file_type=file_type,
                content_type=content_type,
                status=DocumentStatus.PENDING,
                upload_date=utc_now(),
                session_id=session_id,
                document_metadata={
                    "original_size": file_size,
                    "upload_timestamp": datetime.now(timezone.utc).isoformat(),
                    "content_type": content_type
                }
            )

            session.add(document)
            await session.commit()
            await session.refresh(document)

            logger.info(f"Document uploaded successfully: {doc_id} -> {minio_key}")
            return document

        except Exception as e:
            # Rollback database changes
            await session.rollback()

            # Try to clean up MinIO upload if it succeeded
            try:
                delete_file(settings.MINIO_DOCUMENTS_BUCKET, minio_key)
            except:
                pass  # MinIO cleanup failed, but we'll log the original error

            logger.error(f"Document upload failed for {original_filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def process_document(
        self,
        document_id: str,
        session: AsyncSession
    ) -> bool:
        """
        Process document: extract text, chunk, and generate embeddings

        Args:
            document_id: ID of document to process
            session: Database session

        Returns:
            True if processing succeeded, False otherwise
        """

        # Get document
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document not found: {document_id}")
            return False

        if document.status != DocumentStatus.PENDING:
            logger.warning(f"Document {document_id} is not pending, status: {document.status}")
            return False

        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await session.commit()

            # Download file from MinIO
            minio_client = self._get_minio_client()
            try:
                response = minio_client.get_object(settings.MINIO_DOCUMENTS_BUCKET, document.minio_key)
                file_content_bytes = response.read()
                response.close()
            except Exception as e:
                raise ValueError(f"Failed to download file from MinIO: {e}")

            # Create temporary file for processing
            temp_file = Path(f"/tmp/{document.filename}")
            temp_file.write_bytes(file_content_bytes)

            try:
                # Extract text using appropriate loader
                loader = get_document_loader(str(temp_file))
                loaded_document = loader.load()

                if not loaded_document:
                    raise ValueError("No text content extracted from document")

                # Get text content from LoadedDocument
                full_text = loaded_document.content

                # Chunk the text
                chunker = get_text_chunker(
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP
                )

                text_chunks = chunker.split_text(full_text)

                if not text_chunks:
                    raise ValueError("No chunks generated from document")

                # Generate embeddings
                embedding_model = self._get_embedding_model()

                # Clear existing chunks (if any)
                from sqlalchemy import delete
                await session.execute(
                    delete(DocumentChunk).where(
                        DocumentChunk.document_id == document_id
                    )
                )

                # Create chunk records with embeddings
                chunk_records = []
                for idx, chunk_text in enumerate(text_chunks):
                    try:
                        # Generate embedding
                        embedding = embedding_model.encode([chunk_text])[0].tolist()

                        # Create chunk record
                        chunk = DocumentChunk(
                            id=generate_uuid(),
                            document_id=document_id,
                            user_id=document.user_id,
                            chunk_index=idx,
                            text=chunk_text,
                            embedding=embedding,
                            chunk_metadata={
                                "chunk_size": len(chunk_text),
                                "chunk_index": idx,
                                "total_chunks": len(text_chunks),
                                "embedding_model": settings.EMBEDDING_MODEL_NAME,
                                "created_at": datetime.now(timezone.utc).isoformat()
                            },
                            indexed_at=utc_now()
                        )

                        chunk_records.append(chunk)

                    except Exception as e:
                        logger.error(f"Failed to process chunk {idx} for document {document_id}: {e}")
                        continue

                if not chunk_records:
                    raise ValueError("No chunks processed successfully")

                # Add all chunks to session
                session.add_all(chunk_records)

                # Update document status and metadata
                document.status = DocumentStatus.INDEXED
                document.processed_date = utc_now()
                document.document_metadata.update({
                    "processing_completed": datetime.now(timezone.utc).isoformat(),
                    "total_chunks": len(chunk_records),
                    "text_length": len(full_text),
                    "embedding_model": settings.EMBEDDING_MODEL_NAME
                })

                await session.commit()

                logger.info(f"Document processed successfully: {document_id} ({len(chunk_records)} chunks)")
                return True

            finally:
                # Clean up temporary file
                temp_file.unlink(missing_ok=True)

        except Exception as e:
            # Update document status to failed
            await session.rollback()

            try:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                document.processed_date = utc_now()
                await session.commit()
            except:
                pass

            logger.error(f"Document processing failed for {document_id}: {e}")
            return False

    async def delete_document(
        self,
        document_id: str,
        session: AsyncSession
    ) -> bool:
        """
        Delete document and all associated data

        Args:
            document_id: ID of document to delete
            session: Database session

        Returns:
            True if deletion succeeded, False otherwise
        """

        # Get document
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f"Document not found for deletion: {document_id}")
            return False

        try:
            # Delete from MinIO
            delete_success = delete_file(settings.MINIO_DOCUMENTS_BUCKET, document.minio_key)
            if not delete_success:
                logger.warning(f"Failed to delete MinIO object: {document.minio_key}")

            # Delete from database (cascades to chunks)
            await session.delete(document)
            await session.commit()

            logger.info(f"Document deleted successfully: {document_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Document deletion failed for {document_id}: {e}")
            return False

    async def get_user_documents(
        self,
        user_id: Optional[str],
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents for a user or all users if user_id is None"""

        query = select(Document)

        if user_id:
            query = query.where(Document.user_id == user_id)

        result = await session.execute(
            query
            .order_by(Document.upload_date.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_document_stats(
        self,
        user_id: Optional[str],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get document statistics"""

        # Base query
        base_query = select(func.count(Document.id))
        chunks_query = select(func.count(DocumentChunk.id))

        if user_id:
            base_query = base_query.where(Document.user_id == user_id)
            chunks_query = chunks_query.where(DocumentChunk.user_id == user_id)

        # Get total documents
        total_docs = await session.scalar(base_query)

        # Get documents by status
        status_counts = {}
        for status in DocumentStatus:
            query = select(func.count(Document.id)).where(Document.status == status)
            if user_id:
                query = query.where(Document.user_id == user_id)
            count = await session.scalar(query)
            status_counts[status.value] = count

        # Get total chunks
        total_chunks = await session.scalar(chunks_query)

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "documents_by_status": status_counts,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }


# Global document service instance
_document_service = None


def get_document_service() -> DocumentService:
    """Get global document service instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
