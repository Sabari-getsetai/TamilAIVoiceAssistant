# Repository Pattern Implementation Roadmap

## Overview

This document outlines the implementation strategy for refactoring the database layer to use the Repository Pattern, improving code maintainability, testability, and scalability.

---

## Phase 1: Foundation & Core Pipeline (Weeks 1-2)

**Goal**: Establish repository pattern base classes and implement for the voice conversation pipeline

### 1.1 Create Base Repository Class
**Files to Create**:
- `backend/repositories/base_repository.py`

**Implementation**:
```python
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model

    async def create(self, obj: T) -> T:
        """Create new record"""
        
    async def read(self, id: str) -> Optional[T]:
        """Read by ID"""
        
    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Update record"""
        
    async def delete(self, id: str) -> bool:
        """Delete record (soft delete pattern for audit)"""
        
    async def list(self, filters: Dict[str, Any], limit: int, offset: int) -> List[T]:
        """List with filtering"""
        
    async def count(self, filters: Dict[str, Any]) -> int:
        """Count with filtering"""
```

**Estimated Effort**: 4-6 hours

### 1.2 Implement ConversationSessionRepository
**Files to Create**:
- `backend/repositories/conversation_session_repository.py`

**Key Methods**:
```python
class ConversationSessionRepository(BaseRepository[ConversationSession]):
    # Core CRUD
    async def create_session(self, user_id, language, rag_enabled, ...) -> ConversationSession
    async def get_session(self, session_id) -> Optional[ConversationSession]
    async def update_session(self, session_id, **fields) -> Optional[ConversationSession]
    
    # Session Lifecycle
    async def get_active_by_user(self, user_id) -> List[ConversationSession]
    async def list_expired_sessions(self, since: datetime) -> List[ConversationSession]
    async def expire_session(self, session_id) -> bool
    async def end_session(self, session_id) -> bool
    
    # History & Analytics
    async def get_with_turns(self, session_id, limit: int) -> Dict[str, Any]
    async def get_session_stats(self, session_id) -> Dict[str, Any]
    async def list_user_sessions(self, user_id, status_filter, limit, offset) -> List[Dict]
    
    # Cleanup & Maintenance
    async def cleanup_expired(self, batch_size: int) -> int
    async def cleanup_user_sessions(self, user_id) -> int
```

**Replaces**: DatabaseSessionManager (partial refactoring)

**Estimated Effort**: 20-24 hours

**Current Code Impact**:
- Refactor `backend/services/session_service.py` → use repository instead of raw queries
- Update `backend/graphs/chat_graph.py` → dependency inject repository
- Update `backend/api/websocket.py` → inject session repository

### 1.3 Implement DocumentRepository
**Files to Create**:
- `backend/repositories/document_repository.py`

**Key Methods**:
```python
class DocumentRepository(BaseRepository[Document]):
    # Core CRUD
    async def create_document(self, user_id, org_id, file_info, ...) -> Document
    async def get_document(self, doc_id) -> Optional[Document]
    async def update_document(self, doc_id, **fields) -> Optional[Document]
    
    # Filtering & Discovery
    async def get_by_user(self, user_id, limit, offset) -> List[Document]
    async def get_by_org(self, org_id, limit, offset) -> List[Document]
    async def get_by_status(self, status: DocumentStatus, limit) -> List[Document]
    async def get_pending_documents(self) -> List[Document]
    async def get_processing_documents(self) -> List[Document]
    
    # Status Management
    async def update_status(self, doc_id, status, error_msg=None) -> bool
    async def mark_indexed(self, doc_id) -> bool
    async def mark_failed(self, doc_id, error_msg) -> bool
    
    # Data Retrieval
    async def get_with_chunks(self, doc_id) -> Dict[str, Any]
    async def get_chunk_count(self, doc_id) -> int
```

**Replaces**: DocumentService raw queries

**Estimated Effort**: 16-20 hours

**Current Code Impact**:
- Refactor `backend/services/document_service.py` → use repository
- Update `backend/graphs/ingest_graph.py` → inject document repository
- Update `backend/api/routes/admin_v2.py` → use repository

### 1.4 Implement DocumentChunkRepository
**Files to Create**:
- `backend/repositories/document_chunk_repository.py`

**Key Methods**:
```python
class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    # Vector Similarity Search (Critical for RAG)
    async def search_by_similarity(
        self, 
        query_vector: List[float], 
        user_id: str, 
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Vector similarity search for RAG context retrieval"""
        
    # Chunk Management
    async def get_by_document(self, document_id) -> List[DocumentChunk]
    async def bulk_create(self, chunks: List[DocumentChunk]) -> int
    async def delete_by_document(self, document_id) -> int
    
    # Analytics
    async def count_by_document(self, document_id) -> int
    async def get_by_user(self, user_id, limit, offset) -> List[DocumentChunk]
    async def get_embedding_stats(self, user_id) -> Dict[str, Any]
```

**Special Considerations**:
- Vector search query: `ORDER BY embedding <-> query_embedding`
- Batch insert optimization for hundreds of chunks
- User-scoped privacy enforcement

**Estimated Effort**: 12-16 hours

**Current Code Impact**:
- Create RAG query abstraction layer
- Update LLM context retrieval logic
- Create vector search optimization strategies

### 1.5 Register Repositories (Dependency Injection)
**Files to Create**:
- `backend/repositories/__init__.py`
- `backend/repositories/repository_factory.py`

**Implementation**:
```python
class RepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._session_repo = None
        self._document_repo = None
        self._chunk_repo = None
    
    def get_session_repository(self) -> ConversationSessionRepository:
        if self._session_repo is None:
            self._session_repo = ConversationSessionRepository(self.db)
        return self._session_repo
    
    # ... other repositories

# Dependency injection in FastAPI
async def get_repositories(db: AsyncSession = Depends(get_db)) -> RepositoryFactory:
    return RepositoryFactory(db)
```

**Estimated Effort**: 4-6 hours

### Phase 1 Summary

| Task | Hours | Status |
|------|-------|--------|
| Base Repository | 5 | Ready |
| ConversationSessionRepository | 22 | Ready |
| DocumentRepository | 18 | Ready |
| DocumentChunkRepository | 14 | Ready |
| Dependency Injection Setup | 5 | Ready |
| **Phase 1 Total** | **64** | |

**Deliverables**:
- Fully functional voice conversation pipeline with repository pattern
- Reduced code duplication in session management
- Improved testability for conversation logic
- RAG vector search abstraction

---

## Phase 2: Multi-Tenancy & Auth (Weeks 3-4)

**Goal**: Implement repositories for user management and organization features

### 2.1 UserRepository
**Files to Create**: `backend/repositories/user_repository.py`

**Key Methods**:
```python
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]
    async def get_by_username(self, username: str) -> Optional[User]
    async def authenticate(self, email: str, password_hash: str) -> Optional[User]
    async def create_user(self, email, username, password_hash, ...) -> User
    async def update_last_login(self, user_id) -> bool
    async def list_by_tier(self, tier: str, limit, offset) -> List[User]
    async def count_organizations(self, user_id) -> int
    async def get_with_organizations(self, user_id) -> Dict[str, Any]
```

**Used By**: AuthService, auth routes

**Estimated Effort**: 12-16 hours

### 2.2 OrganizationRepository
**Files to Create**: `backend/repositories/organization_repository.py`

**Key Methods**:
```python
class OrganizationRepository(BaseRepository[Organization]):
    async def create_organization(self, creator_id, name, ...) -> Organization
    async def get_by_creator(self, user_id, limit, offset) -> List[Organization]
    async def get_user_memberships(self, user_id) -> List[Dict[str, Any]]
    async def get_members(self, org_id, limit, offset) -> List[OrganizationMember]
    async def count_members(self, org_id) -> int
    async def search(self, query: str, limit: int) -> List[Organization]
    async def get_with_billing(self, org_id) -> Dict[str, Any]
```

**Used By**: OrganizationService, organization routes

**Estimated Effort**: 14-18 hours

### 2.3 OrganizationMemberRepository
**Files to Create**: `backend/repositories/organization_member_repository.py`

**Key Methods**:
```python
class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    async def add_member(self, org_id, user_id, role, invited_by) -> OrganizationMember
    async def get_by_org_user(self, org_id, user_id) -> Optional[OrganizationMember]
    async def get_by_org(self, org_id, limit, offset) -> List[OrganizationMember]
    async def get_by_role(self, org_id, role: OrganizationRole) -> List[OrganizationMember]
    async def update_role(self, org_id, user_id, new_role) -> bool
    async def remove_member(self, org_id, user_id) -> bool
    async def check_membership(self, org_id, user_id) -> bool
    async def validate_access(self, org_id, user_id, required_role) -> bool
```

**Special Considerations**:
- Role hierarchy validation (MEMBER < ORG_ADMIN < OWNER)
- Access control enforcement
- Audit trail (invited_by tracking)

**Estimated Effort**: 16-20 hours

### 2.4 AudioFileRepository
**Files to Create**: `backend/repositories/audio_file_repository.py`

**Key Methods**:
```python
class AudioFileRepository(BaseRepository[AudioFile]):
    async def create_audio(self, user_id, org_id, file_info, ...) -> AudioFile
    async def get_by_session(self, session_id) -> List[AudioFile]
    async def get_expired(self, before: datetime, limit: int) -> List[AudioFile]
    async def count_by_type(self, user_id, file_type: AudioFileType) -> int
    async def delete_expired(self, before: datetime, batch_size: int) -> int
    async def get_by_user_type(self, user_id, file_type, limit, offset) -> List[AudioFile]
    async def get_by_org_stats(self, org_id) -> Dict[str, Any]
```

**Used By**: Cleanup jobs, audio management APIs

**Estimated Effort**: 10-14 hours

### Phase 2 Summary

| Task | Hours | Status |
|------|-------|--------|
| UserRepository | 14 | Ready |
| OrganizationRepository | 16 | Ready |
| OrganizationMemberRepository | 18 | Ready |
| AudioFileRepository | 12 | Ready |
| Integration & Testing | 16 | Ready |
| **Phase 2 Total** | **76** | |

**Deliverables**:
- Complete multi-tenant data isolation via repositories
- RBAC enforcement layer
- User & organization management abstraction
- Audio lifecycle management

---

## Phase 3: Secondary Models (Week 5)

**Goal**: Complete repository pattern coverage

### 3.1 ConversationTurnRepository
**Files to Create**: `backend/repositories/conversation_turn_repository.py`

**Key Methods**:
```python
class ConversationTurnRepository(BaseRepository[ConversationTurn]):
    async def add_turn(self, session_id, turn_number, ...) -> ConversationTurn
    async def get_by_session(self, session_id, limit, offset) -> List[ConversationTurn]
    async def get_turn_range(self, session_id, start_turn, end_turn) -> List[ConversationTurn]
    async def get_recent_turns(self, session_id, limit) -> List[ConversationTurn]
    async def count_by_session(self, session_id) -> int
    async def get_turn_with_audio(self, turn_id) -> Dict[str, Any]
```

**Estimated Effort**: 8-12 hours

### 3.2 OrganizationInvitationRepository
**Files to Create**: `backend/repositories/organization_invitation_repository.py`

**Key Methods**:
```python
class OrganizationInvitationRepository(BaseRepository[OrganizationInvitation]):
    async def create_invitation(self, org_id, invited_email, role, invited_by, ...) -> OrganizationInvitation
    async def get_by_token(self, token: str) -> Optional[OrganizationInvitation]
    async def get_pending_by_org(self, org_id) -> List[OrganizationInvitation]
    async def get_pending_by_email(self, email: str) -> List[OrganizationInvitation]
    async def accept_invitation(self, token, user_id) -> bool
    async def cleanup_expired(self, before: datetime) -> int
    async def revoke_invitation(self, token) -> bool
```

**Estimated Effort**: 8-12 hours

### Phase 3 Summary

| Task | Hours | Status |
|------|-------|--------|
| ConversationTurnRepository | 10 | Ready |
| OrganizationInvitationRepository | 10 | Ready |
| **Phase 3 Total** | **20** | |

---

## Total Implementation Summary

### By Phase

| Phase | Focus | Hours | Timeline |
|-------|-------|-------|----------|
| **Phase 1** | Foundation & Voice Pipeline | 64 | Weeks 1-2 |
| **Phase 2** | Multi-Tenancy & Auth | 76 | Weeks 3-4 |
| **Phase 3** | Secondary Models | 20 | Week 5 |
| **Testing & Optimization** | Unit/integration tests | 40-60 | Ongoing |
| **Documentation** | Code docs & migration guides | 16-20 | Ongoing |
| **TOTAL** | | **216-256 hours** | 4-5 weeks |

### By Complexity

| Category | Count | Effort |
|----------|-------|--------|
| Simple (CRUD only) | 2 | 20 hours |
| Moderate (with filtering) | 4 | 60 hours |
| Complex (state machines, vector search) | 3 | 80 hours |
| Base infrastructure | 1 | 16 hours |

---

## Migration Strategy

### Step 1: Parallel Implementation
- Implement repositories alongside existing code
- Keep DatabaseSessionManager for backward compatibility
- Both code paths functional during transition

### Step 2: Gradual Replacement
```
Week 1: Implement repositories
Week 2: Add tests for repositories
Week 3: Replace service layer calls one-by-one
Week 4: Remove old implementations after validation
Week 5: Final integration & performance testing
```

### Step 3: Backward Compatibility
```python
# During transition: Wrapper that uses repository internally
class DatabaseSessionManager:
    def __init__(self, session_repo: ConversationSessionRepository):
        self.repo = session_repo
    
    async def create_session(self, ...):
        return await self.repo.create_session(...)
```

---

## Testing Strategy

### Unit Tests (Per Repository)
```
backend/tests/unit/repositories/
├── test_conversation_session_repository.py
├── test_document_repository.py
├── test_document_chunk_repository.py
├── test_user_repository.py
├── test_organization_repository.py
├── test_organization_member_repository.py
├── test_audio_file_repository.py
├── test_conversation_turn_repository.py
└── test_organization_invitation_repository.py
```

**Test Coverage Target**: >90% for repositories

### Integration Tests
```
backend/tests/integration/
├── test_session_lifecycle.py (full workflow)
├── test_document_rag_pipeline.py (upload → index → search)
├── test_multi_tenancy.py (org isolation)
└── test_auth_flow.py (user auth)
```

### Performance Tests
- Vector search latency benchmarks
- Batch insert performance
- Query optimization validation
- Cache hit rates

---

## Success Criteria

### Code Quality
- All repositories follow BaseRepository interface
- >90% test coverage
- No direct SQLAlchemy queries in services
- Type hints on all methods

### Performance
- ConversationSession queries < 10ms (cached)
- DocumentChunk similarity search < 100ms
- Batch operations 5x faster than individual inserts
- Database query count reduced by 30%

### Maintainability
- Single responsibility per repository
- Testable without database
- Clear dependency injection
- Comprehensive docstrings

### Documentation
- README for each repository
- Migration guide for developers
- Usage examples
- Performance tuning guide

---

## Risk Mitigation

### Risk 1: Database Compatibility
**Issue**: pgVector syntax in DocumentChunkRepository

**Mitigation**:
- Use SQLAlchemy pgVector extension directly
- Test with PostgreSQL 13+ (pgVector 0.3+)
- Fallback: Vector search without pgVector (slower)

### Risk 2: Cache Coherency
**Issue**: Redis cache out of sync with database

**Mitigation**:
- Invalidate cache on every write
- Use short TTL (30 minutes)
- Implement cache warming strategies

### Risk 3: Migration Data Loss
**Issue**: Existing data during repository implementation

**Mitigation**:
- Dual-write during transition (DB + Repository)
- Database snapshots before migration
- Rollback plan with old DatabaseSessionManager

### Risk 4: Performance Degradation
**Issue**: Repository layer adds overhead

**Mitigation**:
- Benchmark before/after
- Optimize N+1 query problems
- Use eager loading with relationships
- Profile hot paths

---

## Next Steps

1. **Immediate** (This Week):
   - Create `backend/repositories/` directory
   - Implement BaseRepository
   - Start ConversationSessionRepository

2. **Short-term** (Next 2 Weeks):
   - Complete Phase 1 implementations
   - Write unit tests
   - Refactor session service

3. **Medium-term** (Weeks 3-4):
   - Implement Phase 2 repositories
   - Integrate with org management
   - RBAC enforcement

4. **Long-term** (Week 5+):
   - Phase 3 repositories
   - Full test coverage
   - Documentation completion
   - Performance optimization

---

## Files to Create/Modify

### New Files
```
backend/repositories/
├── __init__.py
├── base_repository.py
├── repository_factory.py
├── conversation_session_repository.py
├── document_repository.py
├── document_chunk_repository.py
├── user_repository.py
├── organization_repository.py
├── organization_member_repository.py
├── audio_file_repository.py
├── conversation_turn_repository.py
└── organization_invitation_repository.py

backend/tests/unit/repositories/
├── __init__.py
├── conftest.py (shared fixtures)
├── test_conversation_session_repository.py
├── test_document_repository.py
└── ... (one per repository)
```

### Modified Files
```
backend/services/
├── session_service.py (refactor to use repo)
├── document_service.py (refactor to use repo)
└── organization_service.py (refactor to use repo)

backend/graphs/
├── chat_graph.py (inject session repo)
└── ingest_graph.py (inject document repo)

backend/api/routes/
├── chat.py (use session repo)
├── admin_v2.py (use organization repos)
└── audio.py (use audio file repo)
```

---

**Document Created**: November 14, 2025
**Implementation Timeline**: 4-5 weeks
**Total Estimated Effort**: 216-256 development hours

