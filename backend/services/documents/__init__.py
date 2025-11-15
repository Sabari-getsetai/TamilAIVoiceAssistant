"""
Documents Service Module - Document Lifecycle and RAG

This module handles document processing and retrieval-augmented generation,
designed to be microservice-ready.

Services:
- document_service: Document upload, processing, lifecycle
- task_service: Background processing and batch operations
- vector_service: Embeddings, vector storage, similarity search
- rag_service: Retrieval-augmented generation pipeline
"""

from .task_service import DocumentTaskService

__all__ = [
    "DocumentTaskService"
]