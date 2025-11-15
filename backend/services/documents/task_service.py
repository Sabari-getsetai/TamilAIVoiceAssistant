"""Document Task Service - Background Processing Management

This service handles:
- Document background processing coordination
- Batch document processing
- Processing status tracking
- Error handling and retry logic

Replaces: backend.api.helper.DocumentHelper
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.utils.base_service import BaseService
from backend.repositories.document_repository import DocumentRepository
from backend.database.models import Document, DocumentStatus


class DocumentTaskService(BaseService):
    """Service for document background task management"""

    def __init__(self):
        super().__init__()
        self.service_name = "DocumentTaskService"
        self.document_repo = DocumentRepository()

        # Processing configuration
        self.max_concurrent_documents = 3
        self.processing_timeout_seconds = 300  # 5 minutes per document
        self.max_retries = 2

    async def process_documents_background(
        self,
        document_ids: List[str],
        db: AsyncSession,
        force_reprocess: bool = False,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """Background task for processing multiple documents

        Args:
            document_ids: List of document IDs to process
            db: Database session
            force_reprocess: Whether to reprocess already indexed documents
            max_concurrent: Maximum concurrent processing (overrides default)

        Returns:
            Dictionary with processing statistics and results
        """
        if max_concurrent is None:
            max_concurrent = self.max_concurrent_documents

        self.logger.info(f"Starting background processing for {len(document_ids)} documents")

        results = {
            "total_documents": len(document_ids),
            "processed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "processing_errors": [],
            "processing_details": {},
            "start_time": None,
            "end_time": None
        }

        import time
        start_time = time.time()
        results["start_time"] = start_time

        try:
            # Create semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(max_concurrent)

            # Create processing tasks
            tasks = []
            for doc_id in document_ids:
                task = self._process_single_document_task(
                    doc_id, db, force_reprocess, semaphore, results
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            results["end_time"] = end_time
            results["total_time_seconds"] = end_time - start_time

            self.logger.info(
                f"Background processing completed: "
                f"{results['processed_count']} processed, "
                f"{results['failed_count']} failed, "
                f"{results['skipped_count']} skipped "
                f"in {results['total_time_seconds']:.2f} seconds"
            )

            return results

        except Exception as e:
            self.logger.error(f"Critical error in background document processing: {str(e)}")
            results["processing_errors"].append(f"Critical error: {str(e)}")
            return results

    async def _process_single_document_task(
        self,
        doc_id: str,
        db: AsyncSession,
        force_reprocess: bool,
        semaphore: asyncio.Semaphore,
        results: Dict[str, Any]
    ) -> None:
        """Process a single document with concurrency control

        Args:
            doc_id: Document ID to process
            db: Database session
            force_reprocess: Whether to reprocess already indexed documents
            semaphore: Semaphore for concurrency control
            results: Shared results dictionary to update
        """
        async with semaphore:
            try:
                await self._process_single_document(doc_id, db, force_reprocess, results)
            except Exception as e:
                self.logger.error(f"Error in document task for {doc_id}: {str(e)}")
                results["failed_count"] += 1
                results["processing_errors"].append(f"Document {doc_id}: {str(e)}")
                results["processing_details"][doc_id] = {
                    "status": "error",
                    "error": str(e),
                    "retries": 0
                }

    async def _process_single_document(
        self,
        doc_id: str,
        db: AsyncSession,
        force_reprocess: bool,
        results: Dict[str, Any]
    ) -> None:
        """Process a single document with error handling

        Args:
            doc_id: Document ID to process
            db: Database session
            force_reprocess: Whether to reprocess already indexed documents
            results: Shared results dictionary to update
        """
        try:
            # Get document from database
            document = await self.document_repo.get_by_id(db, doc_id)

            if not document:
                self.logger.warning(f"Document not found for processing: {doc_id}")
                results["failed_count"] += 1
                results["processing_errors"].append(f"Document not found: {doc_id}")
                results["processing_details"][doc_id] = {
                    "status": "not_found",
                    "error": "Document not found in database"
                }
                return

            # Check if document needs processing
            if document.status == DocumentStatus.INDEXED and not force_reprocess:
                self.logger.info(f"Document already processed, skipping: {doc_id}")
                results["skipped_count"] += 1
                results["processing_details"][doc_id] = {
                    "status": "skipped",
                    "reason": "Already processed"
                }
                return

            # Reset status if force reprocessing
            if force_reprocess and document.status == DocumentStatus.INDEXED:
                await self.document_repo.update_status(db, doc_id, DocumentStatus.PENDING)
                self.logger.info(f"Reset document status for reprocessing: {doc_id}")

            # Process the document
            success = await self._execute_document_processing(doc_id, db)

            if success:
                results["processed_count"] += 1
                results["processing_details"][doc_id] = {
                    "status": "processed",
                    "message": "Successfully processed"
                }
                self.logger.info(f"Document processed successfully: {doc_id}")
            else:
                results["failed_count"] += 1
                results["processing_details"][doc_id] = {
                    "status": "failed",
                    "error": "Processing returned false"
                }
                self.logger.error(f"Document processing failed: {doc_id}")

        except Exception as e:
            self.logger.error(f"Error processing document {doc_id}: {str(e)}")
            results["failed_count"] += 1
            results["processing_errors"].append(f"Document {doc_id}: {str(e)}")
            results["processing_details"][doc_id] = {
                "status": "error",
                "error": str(e)
            }

    async def _execute_document_processing(
        self,
        doc_id: str,
        db: AsyncSession,
        retry_count: int = 0
    ) -> bool:
        """Execute the actual document processing with retry logic

        Args:
            doc_id: Document ID to process
            db: Database session
            retry_count: Current retry attempt

        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Import here to avoid circular dependencies
            from backend.services.document_service import get_document_service

            # Get the document service and process
            service = get_document_service()

            # Set processing timeout
            try:
                success = await asyncio.wait_for(
                    service.process_document(doc_id, db),
                    timeout=self.processing_timeout_seconds
                )
                return success

            except asyncio.TimeoutError:
                self.logger.error(f"Document processing timed out: {doc_id}")

                # Update document status to failed
                await self.document_repo.update_status(
                    db, doc_id, DocumentStatus.ERROR,
                    error_message="Processing timeout"
                )

                # Retry if we haven't exceeded max retries
                if retry_count < self.max_retries:
                    self.logger.info(f"Retrying document processing: {doc_id} (attempt {retry_count + 1})")
                    return await self._execute_document_processing(doc_id, db, retry_count + 1)

                return False

        except Exception as e:
            self.logger.error(f"Error executing document processing for {doc_id}: {str(e)}")

            # Update document status to failed
            try:
                await self.document_repo.update_status(
                    db, doc_id, DocumentStatus.ERROR,
                    error_message=str(e)
                )
            except Exception as update_error:
                self.logger.error(f"Failed to update document status: {update_error}")

            # Retry if we haven't exceeded max retries
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying document processing: {doc_id} (attempt {retry_count + 1})")
                return await self._execute_document_processing(doc_id, db, retry_count + 1)

            return False

    async def get_processing_status(
        self,
        document_ids: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get processing status for multiple documents

        Args:
            document_ids: List of document IDs to check
            db: Database session

        Returns:
            Dictionary with status information for each document
        """
        status_info = {
            "documents": {},
            "summary": {
                "total": len(document_ids),
                "pending": 0,
                "processing": 0,
                "indexed": 0,
                "error": 0,
                "not_found": 0
            }
        }

        for doc_id in document_ids:
            try:
                document = await self.document_repo.get_by_id(db, doc_id)

                if not document:
                    status_info["documents"][doc_id] = {
                        "status": "not_found",
                        "error": "Document not found"
                    }
                    status_info["summary"]["not_found"] += 1
                    continue

                status_info["documents"][doc_id] = {
                    "status": document.status.value,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                    "file_path": document.file_path,
                    "error_message": getattr(document, 'error_message', None)
                }

                # Update summary counts
                if document.status == DocumentStatus.PENDING:
                    status_info["summary"]["pending"] += 1
                elif document.status == DocumentStatus.PROCESSING:
                    status_info["summary"]["processing"] += 1
                elif document.status == DocumentStatus.INDEXED:
                    status_info["summary"]["indexed"] += 1
                elif document.status == DocumentStatus.ERROR:
                    status_info["summary"]["error"] += 1

            except Exception as e:
                self.logger.error(f"Error getting status for document {doc_id}: {str(e)}")
                status_info["documents"][doc_id] = {
                    "status": "error",
                    "error": f"Status check failed: {str(e)}"
                }

        return status_info

    async def retry_failed_documents(
        self,
        organization_id: str,
        db: AsyncSession,
        max_age_hours: Optional[int] = 24
    ) -> Dict[str, Any]:
        """Retry processing for failed documents

        Args:
            organization_id: Organization ID to filter documents
            db: Database session
            max_age_hours: Only retry documents failed within this time period

        Returns:
            Dictionary with retry results
        """
        try:
            # Get failed documents for the organization
            failed_documents = await self.document_repo.get_by_status_and_organization(
                db, DocumentStatus.ERROR, organization_id
            )

            # Filter by age if specified
            if max_age_hours is not None:
                from datetime import datetime, timedelta
                cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
                failed_documents = [
                    doc for doc in failed_documents
                    if doc.updated_at >= cutoff_time
                ]

            if not failed_documents:
                return {
                    "message": "No failed documents found for retry",
                    "retry_count": 0
                }

            # Reset document statuses to pending
            document_ids = []
            for document in failed_documents:
                await self.document_repo.update_status(db, document.id, DocumentStatus.PENDING)
                document_ids.append(document.id)

            self.logger.info(f"Reset {len(document_ids)} failed documents for retry")

            # Process the documents
            return await self.process_documents_background(
                document_ids, db, force_reprocess=False
            )

        except Exception as e:
            self.logger.error(f"Error retrying failed documents: {str(e)}")
            return {
                "error": f"Failed to retry documents: {str(e)}",
                "retry_count": 0
            }

    def get_processing_configuration(self) -> Dict[str, Any]:
        """Get current processing configuration

        Returns:
            Dictionary with configuration settings
        """
        return {
            "max_concurrent_documents": self.max_concurrent_documents,
            "processing_timeout_seconds": self.processing_timeout_seconds,
            "max_retries": self.max_retries
        }

    def update_processing_configuration(
        self,
        max_concurrent: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update processing configuration

        Args:
            max_concurrent: Maximum concurrent document processing
            timeout_seconds: Processing timeout per document
            max_retries: Maximum retry attempts

        Returns:
            Updated configuration dictionary
        """
        if max_concurrent is not None and max_concurrent > 0:
            self.max_concurrent_documents = max_concurrent

        if timeout_seconds is not None and timeout_seconds > 0:
            self.processing_timeout_seconds = timeout_seconds

        if max_retries is not None and max_retries >= 0:
            self.max_retries = max_retries

        self.logger.info(f"Updated processing configuration: {self.get_processing_configuration()}")
        return self.get_processing_configuration()