"""
Document Repository - RAG Document Data Access Layer

This repository handles all database operations for documents and their
chunks, including vector similarity search, document lifecycle management,
and RAG-related operations.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, asc, and_, or_, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from backend.repositories.base_repository import BaseRepository
from backend.database.models import Document, DocumentChunk, User, Organization
from backend.database.models import DocumentStatus


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations."""

    def __init__(self):
        super().__init__(Document)

    async def create_document(
        self,
        db: AsyncSession,
        filename: str,
        file_path: str,
        file_size: int,
        content_type: str,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a new document."""
        document_data = {
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_type": content_type,
            "user_id": user_id,
            "organization_id": organization_id,
            "status": DocumentStatus.UPLOADED,
            "document_metadata": document_metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return await self.create(db, document_data)

    async def get_document_with_chunks(
        self,
        db: AsyncSession,
        document_id: uuid.UUID
    ) -> Optional[Document]:
        """Get a document with all its chunks loaded."""
        try:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.chunks))
                .where(Document.id == document_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get document with chunks {document_id}: {e}")
            raise

    async def get_documents_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[DocumentStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """Get documents for a user with optional status filter."""
        try:
            query = select(Document).where(Document.user_id == user_id)

            if status:
                query = query.where(Document.status == status)

            query = query.order_by(desc(Document.created_at))
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get documents for user {user_id}: {e}")
            raise

    async def get_documents_for_organization(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        status: Optional[DocumentStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents for an organization with optional status filter."""
        try:
            query = select(Document).where(Document.organization_id == organization_id)

            if status:
                query = query.where(Document.status == status)

            query = query.order_by(desc(Document.created_at))
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get documents for organization {organization_id}: {e}")
            raise

    async def update_document_status(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update document status and optional error message."""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if error_message:
                update_data["document_metadata"] = func.jsonb_set(
                    Document.document_metadata,
                    text("'{error_message}'"),
                    text(f'"{error_message}"')
                )

            result = await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(**update_data)
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update document status {document_id}: {e}")
            raise

    async def mark_processing_complete(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        total_chunks: int
    ) -> bool:
        """Mark document processing as complete and set chunk count."""
        try:
            # Update document metadata with processing info
            result = await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(
                    status=DocumentStatus.PROCESSED,
                    updated_at=datetime.utcnow(),
                    document_metadata=func.jsonb_set(
                        Document.document_metadata,
                        text("'{total_chunks}'"),
                        text(str(total_chunks))
                    )
                )
            )
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to mark processing complete {document_id}: {e}")
            raise

    async def get_processing_queue(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Document]:
        """Get documents waiting to be processed."""
        try:
            result = await db.execute(
                select(Document)
                .where(Document.status == DocumentStatus.UPLOADED)
                .order_by(asc(Document.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error("Failed to get processing queue: {e}")
            raise

    async def get_document_analytics(
        self,
        db: AsyncSession,
        organization_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get document processing analytics."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            base_query = select(Document).where(
                Document.created_at >= since_date
            )

            if organization_id:
                base_query = base_query.where(
                    Document.organization_id == organization_id
                )

            # Total documents
            total_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_documents = total_result.scalar()

            # Documents by status
            status_result = await db.execute(
                select(
                    Document.status,
                    func.count().label('count')
                )
                .select_from(base_query.subquery())
                .group_by(Document.status)
            )
            documents_by_status = {row.status.value: row.count for row in status_result}

            # Documents by content type
            type_result = await db.execute(
                select(
                    Document.content_type,
                    func.count().label('count')
                )
                .select_from(base_query.subquery())
                .group_by(Document.content_type)
            )
            documents_by_type = {row.content_type: row.count for row in type_result}

            # Total file size
            size_result = await db.execute(
                select(func.sum(Document.file_size))
                .select_from(base_query.subquery())
            )
            total_size_bytes = size_result.scalar() or 0

            return {
                "period_days": days,
                "total_documents": total_documents,
                "documents_by_status": documents_by_status,
                "documents_by_type": documents_by_type,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get document analytics: {e}")
            raise

    async def cleanup_failed_documents(
        self,
        db: AsyncSession,
        days_old: int = 7,
        batch_size: int = 50
    ) -> int:
        """Clean up old failed documents."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Find failed documents to delete
            result = await db.execute(
                select(Document.id)
                .where(
                    and_(
                        Document.status == DocumentStatus.FAILED,
                        Document.updated_at < cutoff_date
                    )
                )
                .limit(batch_size)
            )
            document_ids = [row.id for row in result]

            if not document_ids:
                return 0

            # Delete the documents (chunks will cascade delete)
            delete_result = await db.execute(
                delete(Document)
                .where(Document.id.in_(document_ids))
            )

            await db.commit()
            deleted_count = delete_result.rowcount

            self.logger.info(f"Cleaned up {deleted_count} failed documents")
            return deleted_count

        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to cleanup failed documents: {e}")
            raise


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk operations with vector search capabilities."""

    def __init__(self):
        super().__init__(DocumentChunk)

    async def create_chunk(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: List[float],
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
        chunk_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """Create a new document chunk with embedding."""
        chunk_data = {
            "document_id": document_id,
            "chunk_index": chunk_index,
            "content": content,
            "embedding": embedding,
            "start_char": start_char,
            "end_char": end_char,
            "chunk_metadata": chunk_metadata or {},
            "created_at": datetime.utcnow()
        }
        return await self.create(db, chunk_data)

    async def batch_create_chunks(
        self,
        db: AsyncSession,
        chunks_data: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Create multiple chunks in a single transaction."""
        try:
            # Add created_at to all chunks
            for chunk_data in chunks_data:
                chunk_data["created_at"] = datetime.utcnow()

            return await self.bulk_create(db, chunks_data)
        except Exception as e:
            self.logger.error(f"Failed to batch create chunks: {e}")
            raise

    async def get_chunks_for_document(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Get all chunks for a document, ordered by chunk index."""
        try:
            query = select(DocumentChunk).where(
                DocumentChunk.document_id == document_id
            ).order_by(asc(DocumentChunk.chunk_index))

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get chunks for document {document_id}: {e}")
            raise

    async def similarity_search(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        organization_id: Optional[uuid.UUID] = None,
        document_ids: Optional[List[uuid.UUID]] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform vector similarity search on document chunks.

        Returns list of (chunk, similarity_score) tuples.
        """
        try:
            # Base similarity query using pgvector cosine similarity
            query = select(
                DocumentChunk,
                DocumentChunk.embedding.cosine_distance(query_embedding).label('distance')
            ).join(Document)

            # Apply filters
            if organization_id:
                query = query.where(Document.organization_id == organization_id)

            if document_ids:
                query = query.where(DocumentChunk.document_id.in_(document_ids))

            # Only processed documents
            query = query.where(Document.status == DocumentStatus.PROCESSED)

            # Apply similarity threshold (cosine distance < threshold)
            # Note: pgvector cosine_distance returns 0-2, where 0 is identical
            # Convert similarity threshold (0-1) to distance threshold
            distance_threshold = 1 - similarity_threshold
            query = query.where(
                DocumentChunk.embedding.cosine_distance(query_embedding) < distance_threshold
            )

            # Order by similarity (lowest distance = highest similarity)
            query = query.order_by(asc('distance')).limit(limit)

            result = await db.execute(query)
            rows = result.all()

            # Convert distance back to similarity score
            chunks_with_scores = [
                (row.DocumentChunk, 1 - row.distance)
                for row in rows
            ]

            return chunks_with_scores

        except Exception as e:
            self.logger.error(f"Failed to perform similarity search: {e}")
            raise

    async def get_context_chunks(
        self,
        db: AsyncSession,
        chunk_id: uuid.UUID,
        context_size: int = 2
    ) -> List[DocumentChunk]:
        """
        Get surrounding chunks for context (chunk +/- context_size).
        """
        try:
            # Get the target chunk to find its document and index
            target_result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.id == chunk_id)
            )
            target_chunk = target_result.scalar_one_or_none()

            if not target_chunk:
                return []

            # Get surrounding chunks
            min_index = max(0, target_chunk.chunk_index - context_size)
            max_index = target_chunk.chunk_index + context_size

            result = await db.execute(
                select(DocumentChunk)
                .where(
                    and_(
                        DocumentChunk.document_id == target_chunk.document_id,
                        DocumentChunk.chunk_index >= min_index,
                        DocumentChunk.chunk_index <= max_index
                    )
                )
                .order_by(asc(DocumentChunk.chunk_index))
            )

            return result.scalars().all()

        except Exception as e:
            self.logger.error(f"Failed to get context chunks for {chunk_id}: {e}")
            raise

    async def hybrid_search(
        self,
        db: AsyncSession,
        query_text: str,
        query_embedding: List[float],
        organization_id: Optional[uuid.UUID] = None,
        limit: int = 10,
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform hybrid search combining text and vector similarity.
        """
        try:
            # Text similarity using PostgreSQL's full-text search
            text_query = select(
                DocumentChunk,
                func.ts_rank_cd(
                    func.to_tsvector('english', DocumentChunk.content),
                    func.plainto_tsquery('english', query_text)
                ).label('text_score')
            ).join(Document)

            # Vector similarity
            vector_query = select(
                DocumentChunk,
                (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label('vector_score')
            ).join(Document)

            # Apply common filters
            for q in [text_query, vector_query]:
                if organization_id:
                    q = q.where(Document.organization_id == organization_id)
                q = q.where(Document.status == DocumentStatus.PROCESSED)

            # Combine scores using weighted average
            combined_query = select(
                DocumentChunk,
                (
                    (text_weight * func.coalesce(text_query.c.text_score, 0)) +
                    (vector_weight * func.coalesce(vector_query.c.vector_score, 0))
                ).label('combined_score')
            ).select_from(
                DocumentChunk.join(Document)
                .join(text_query.subquery(), DocumentChunk.id == text_query.c.id, isouter=True)
                .join(vector_query.subquery(), DocumentChunk.id == vector_query.c.id, isouter=True)
            )

            if organization_id:
                combined_query = combined_query.where(Document.organization_id == organization_id)

            combined_query = combined_query.where(Document.status == DocumentStatus.PROCESSED)
            combined_query = combined_query.order_by(desc('combined_score')).limit(limit)

            result = await db.execute(combined_query)
            rows = result.all()

            chunks_with_scores = [
                (row.DocumentChunk, row.combined_score)
                for row in rows
            ]

            return chunks_with_scores

        except Exception as e:
            self.logger.error(f"Failed to perform hybrid search: {e}")
            # Fallback to vector search only
            return await self.similarity_search(
                db, query_embedding, organization_id=organization_id, limit=limit
            )

    async def get_chunk_analytics(
        self,
        db: AsyncSession,
        organization_id: Optional[uuid.UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get chunk and embedding analytics."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Base query
            base_query = select(DocumentChunk).join(Document).where(
                DocumentChunk.created_at >= since_date
            )

            if organization_id:
                base_query = base_query.where(Document.organization_id == organization_id)

            # Total chunks
            total_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_chunks = total_result.scalar()

            # Average chunk size
            avg_size_result = await db.execute(
                select(func.avg(func.length(DocumentChunk.content)))
                .select_from(base_query.subquery())
            )
            avg_chunk_size = avg_size_result.scalar() or 0

            # Chunks per document
            chunks_per_doc_result = await db.execute(
                select(func.avg(func.count()))
                .select_from(base_query.subquery())
                .group_by(DocumentChunk.document_id)
            )
            avg_chunks_per_doc = chunks_per_doc_result.scalar() or 0

            return {
                "period_days": days,
                "total_chunks": total_chunks,
                "avg_chunk_size_chars": round(avg_chunk_size, 0),
                "avg_chunks_per_document": round(avg_chunks_per_doc, 1),
                "embedding_dimension": 384,  # Fixed for sentence-transformers
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get chunk analytics: {e}")
            raise