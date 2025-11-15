"""
Repositories Package - Data Access Layer

This package contains repository classes that handle all database operations.
Each repository follows the Repository pattern for clean separation between
business logic and data access.

Repositories:
- base_repository: Generic CRUD operations and common patterns
- conversation_repository: Conversation session and turn data access
- document_repository: Document and chunk data access with vector search
- user_repository: User, organization, and membership data access
- audio_repository: Audio file metadata and analytics data access
"""

from .base_repository import BaseRepository
from .conversation_repository import ConversationSessionRepository, ConversationTurnRepository
from .document_repository import DocumentRepository, DocumentChunkRepository
from .user_repository import (
    UserRepository,
    OrganizationRepository,
    OrganizationMemberRepository,
    OrganizationInvitationRepository
)
from .audio_repository import AudioFileRepository

__all__ = [
    # Base repository
    "BaseRepository",

    # Conversation repositories
    "ConversationSessionRepository",
    "ConversationTurnRepository",

    # Document repositories
    "DocumentRepository",
    "DocumentChunkRepository",

    # User and organization repositories
    "UserRepository",
    "OrganizationRepository",
    "OrganizationMemberRepository",
    "OrganizationInvitationRepository",

    # Media repositories
    "AudioFileRepository"
]