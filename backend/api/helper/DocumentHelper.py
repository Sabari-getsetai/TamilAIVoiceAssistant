"""Helper functions for document processing operations."""



from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.document_service import get_document_service
from backend.database.models import Document, DocumentStatus
from typing import List
import logging


logger = logging.getLogger(__name__)

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
            result = await session.execute(
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