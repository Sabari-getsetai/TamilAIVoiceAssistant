"""
SQLAlchemy database models for Tamil AI Voice Assistant.

This module defines all database tables and relationships for:
- User management and authentication
- Organization/team support
- Document storage and metadata
- Vector embeddings with pgVector
- Conversation sessions and history
- Audio file management
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    LargeBinary,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

Base = declarative_base()


# Enums
class UserRole(str, Enum):
    """User roles in the system."""
    USER = "USER"
    ADMIN = "ADMIN"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """Conversation session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    ENDED = "ended"


class AudioFileType(str, Enum):
    """Types of audio files."""
    USER_INPUT = "user_input"
    TTS_OUTPUT = "tts_output"
    REFINED = "refined"


class OrganizationRole(str, Enum):
    """User roles within an organization."""
    MEMBER = "member"
    ORG_ADMIN = "ORG_ADMIN"  # Organization admin with limited privileges
    ADMIN = "admin"
    OWNER = "owner"


# Utility function for UUID generation
def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


# Models
class User(Base):
    """User account information."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_organization_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    max_organizations_allowed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Tier-based organization limit
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False, index=True)  # free, pro, enterprise
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    preferences: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    active_organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", 
        foreign_keys=[active_organization_id], 
        post_update=True,
        lazy="select"
    )
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    conversation_sessions: Mapped[List["ConversationSession"]] = relationship("ConversationSession", back_populates="user", cascade="all, delete-orphan")
    audio_files: Mapped[List["AudioFile"]] = relationship("AudioFile", back_populates="user", cascade="all, delete-orphan")
    organization_memberships: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", 
        back_populates="user", 
        cascade="all, delete-orphan", 
        foreign_keys="[OrganizationMember.user_id]"
    )
    created_organizations: Mapped[List["Organization"]] = relationship(
        "Organization", 
        back_populates="creator", 
        foreign_keys="[Organization.creator_id]"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class Organization(Base):
    """Organization/team information."""
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[str] = mapped_column(String(50), default="startup", nullable=False)  # startup, small, medium, large, enterprise
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    creator_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    billing_email: Mapped[Optional[str]] = mapped_column(String(255))
    subscription_plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    tier_type: Mapped[str] = mapped_column(String(50), default="free", nullable=False, index=True)  # free, pro, enterprise
    max_organizations_per_user: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Tier-based limit
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_organizations", foreign_keys=[creator_id])
    members: Mapped[List["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class OrganizationMember(Base):
    """User membership in organizations."""
    __tablename__ = "organization_members"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    role: Mapped[OrganizationRole] = mapped_column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    invited_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="organization_memberships", foreign_keys="[OrganizationMember.user_id]")
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys="[OrganizationMember.invited_by]")

    # Constraints
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_organization_user"),
    )

    def __repr__(self):
        return f"<OrganizationMember(org={self.organization_id}, user={self.user_id}, role={self.role})>"


class Document(Base):
    """Document metadata and storage information."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO object key
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PDF, DOCX, TXT, etc.
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME type
    status: Mapped[DocumentStatus] = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))  # For grouping during ingestion
    document_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="documents")
    organization: Mapped["Organization"] = relationship("Organization")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_documents_user_status", "user_id", "status"),
        Index("ix_documents_org_status", "organization_id", "status"),
        Index("ix_documents_session", "session_id"),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class DocumentChunk(Base):
    """Document chunks with vector embeddings for RAG."""
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))  # Embedding dimension for sentence-transformers
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    user: Mapped["User"] = relationship("User")

    # Indexes for performance
    __table_args__ = (
        Index("ix_chunks_document_user", "document_id", "user_id"),
        Index("ix_chunks_user_embedding", "user_id"),  # For user-scoped vector search
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document={self.document_id}, index={self.chunk_index})>"


class ConversationSession(Base):
    """Conversation session information."""
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), default="ta", nullable=False)  # Tamil by default
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversation_sessions")
    organization: Mapped["Organization"] = relationship("Organization")
    turns: Mapped[List["ConversationTurn"]] = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_sessions_user_status", "user_id", "status"),
        Index("ix_sessions_org_status", "organization_id", "status"),
        Index("ix_sessions_user_activity", "user_id", "last_activity"),
    )

    def __repr__(self):
        return f"<ConversationSession(id={self.id}, user={self.user_id}, turns={self.total_turns})>"


class ConversationTurn(Base):
    """Individual conversation turns within a session."""
    __tablename__ = "conversation_turns"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("conversation_sessions.id"), nullable=False, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_text: Mapped[Optional[str]] = mapped_column(Text)
    assistant_text: Mapped[Optional[str]] = mapped_column(Text)
    audio_input_key: Mapped[Optional[str]] = mapped_column(String(500))  # MinIO key for user audio
    audio_output_key: Mapped[Optional[str]] = mapped_column(String(500))  # MinIO key for assistant audio
    retrieved_chunks: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of chunk IDs used for RAG
    processing_time: Mapped[Optional[dict]] = mapped_column(JSON)  # Timing information
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    turn_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    session: Mapped["ConversationSession"] = relationship("ConversationSession", back_populates="turns")

    # Indexes
    __table_args__ = (
        Index("ix_turns_session_number", "session_id", "turn_number"),
        Index("ix_turns_session_time", "session_id", "timestamp"),
        UniqueConstraint("session_id", "turn_number", name="uq_session_turn_number"),
    )

    def __repr__(self):
        return f"<ConversationTurn(id={self.id}, session={self.session_id}, turn={self.turn_number})>"


class AudioFile(Base):
    """Audio file metadata and storage information."""
    __tablename__ = "audio_files"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("conversation_sessions.id"), index=True)
    file_type: Mapped[AudioFileType] = mapped_column(SQLEnum(AudioFileType), nullable=False, index=True)
    minio_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float)  # Duration in seconds
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)  # For automatic cleanup
    audio_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audio_files")
    organization: Mapped["Organization"] = relationship("Organization")
    session: Mapped[Optional["ConversationSession"]] = relationship("ConversationSession")

    # Indexes
    __table_args__ = (
        Index("ix_audio_user_session", "user_id", "session_id"),
        Index("ix_audio_user_type", "user_id", "file_type"),
        Index("ix_audio_org_type", "organization_id", "file_type"),
        Index("ix_audio_expires", "expires_at"),  # For cleanup jobs
    )

    def __repr__(self):
        return f"<AudioFile(id={self.id}, type={self.file_type}, user={self.user_id})>"


# System tables for migrations and metadata
class SystemInfo(Base):
    """System information and configuration."""
    __tablename__ = "system_info"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    def __repr__(self):
        return f"<SystemInfo(key={self.key}, value={self.value})>"
