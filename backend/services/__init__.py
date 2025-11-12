"""
Services Package - Business logic layer

Contains service classes that encapsulate business logic and coordinate
between different components like database, storage, and AI models.
"""

from .document_service import DocumentService, get_document_service
from .session_service import DatabaseSessionManager, get_session_manager

__all__ = [
    "DocumentService", "get_document_service",
    "DatabaseSessionManager", "get_session_manager"
]