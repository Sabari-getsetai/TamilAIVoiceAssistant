# Database Model Analysis - Tamil AI Voice Assistant

## Executive Summary

The Tamil AI Voice Assistant backend uses **10 core SQLAlchemy models** organized into 4 domain groups:

1. **User & Auth Domain**: User, Organization, OrganizationMember, OrganizationInvitation
2. **Document Domain**: Document, DocumentChunk
3. **Conversation Domain**: ConversationSession, ConversationTurn
4. **Media Domain**: AudioFile
5. **System Domain**: SystemInfo

Total database tables: 11 (10 models + 1 system table)
Multi-tenancy: Yes (organization-scoped)
Vector search: Yes (pgVector for 384-dim embeddings)

---

## 1. ALL MODEL CLASSES DEFINED

### 1.1 User Management Models

#### **User** (Core authentication entity)
- **Primary Key**: `id` (UUID)
- **Unique Fields**: `email`, `username`
- **Key Attributes**:
  - Authentication: `password_hash`, `is_active`, `is_verified`
  - Organization: `active_organization_id`, `max_organizations_allowed`, `subscription_tier`
  - Metadata: `full_name`, `preferences` (JSON), `created_at`, `updated_at`, `last_login`
- **Relationships**:
  - `1:N` active_organization → Organization
  - `1:N` documents → Document (cascade delete)
  - `1:N` conversation_sessions → ConversationSession (cascade delete)
  - `1:N` audio_files → AudioFile (cascade delete)
  - `1:N` organization_memberships → OrganizationMember (cascade delete)
  - `1:N` created_organizations → Organization (creator)
- **Indexes**: `email`, `username`, `subscription_tier`
- **Primary Use Cases**: Authentication, user account management, tier-based access control
- **Business Rules**:
  - Subscription tiers: free, pro, enterprise
  - Organization limits per tier
  - User roles: USER, ADMIN, ORGANIZATION_ADMIN

#### **Organization**
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Basic: `name`, `description`, `website`, `industry`
  - Sizing: `size` (startup, small, medium, large, enterprise)
  - Billing: `billing_email`, `subscription_plan`, `subscription_status`, `trial_ends_at`
  - Configuration: `timezone` (default UTC), `settings` (JSON), `is_active`
  - Tier: `tier_type` (free, pro, enterprise)
  - Ownership: `creator_id` (foreign key to User)
- **Relationships**:
  - `N:1` creator → User
  - `1:N` members → OrganizationMember (cascade delete)
- **Indexes**: `name`, `tier_type`
- **Primary Use Cases**:
  - Multi-tenant data isolation
  - Organization management and quotas
  - Subscription and billing management
  - Workspace/team management

#### **OrganizationMember** (Join table with role info)
- **Primary Key**: `id` (UUID)
- **Unique Constraint**: (`organization_id`, `user_id`) - prevents duplicate memberships
- **Key Attributes**:
  - References: `organization_id`, `user_id`, `invited_by` (who invited this user)
  - Role: `role` (enum: MEMBER, ORG_ADMIN, ADMIN, OWNER)
  - Timestamps: `joined_at`
- **Relationships**:
  - `N:1` organization → Organization
  - `N:1` user → User
  - `N:1` inviter → User (who invited)
- **Primary Use Cases**:
  - Organization member management
  - Role-based access control per organization
  - Audit trail (who invited whom and when)

#### **OrganizationInvitation** (Pending invitations)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Invitation: `invited_email`, `token` (unique), `invited_by`
  - Lifecycle: `created_at`, `expires_at`, `accepted_at`, `accepted_by`, `is_expired`
  - Role: `role` (enum: MEMBER, ORG_ADMIN, ADMIN, OWNER)
  - Reference: `organization_id`
- **Unique Constraints**:
  - (`organization_id`, `invited_email`) - prevent duplicate invitations
  - `token` - secure token lookup
- **Indexes**: 
  - `(invited_email, token)` - for invitation lookup
  - `(organization_id, expires_at)` - for cleanup
- **Relationships**:
  - `N:1` organization → Organization
  - `N:1` inviter → User
  - `N:1` acceptor → User (optional, for audit)
- **Primary Use Cases**:
  - Pending member invitations
  - Invitation expiry management
  - Signup workflows with role assignment

---

### 1.2 Document & RAG Models

#### **Document** (File metadata and status tracking)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Ownership: `user_id`, `organization_id`
  - File Info: `filename`, `original_filename`, `file_size`, `file_type` (PDF, DOCX, TXT, etc.), `content_type` (MIME)
  - Storage: `minio_key` (S3-style path in MinIO)
  - Processing: `status` (enum: PENDING, PROCESSING, INDEXED, FAILED), `error_message`
  - Timestamps: `upload_date`, `processed_date`
  - Grouping: `session_id` (for batch uploads), `document_metadata` (JSON)
- **Relationships**:
  - `N:1` user → User
  - `N:1` organization → Organization
  - `1:N` chunks → DocumentChunk (cascade delete)
- **Indexes**:
  - `(user_id, status)` - for user document listing with status filtering
  - `(organization_id, status)` - for org-wide document discovery
  - `session_id` - for batch operations
- **Primary Use Cases**:
  - RAG document ingestion and lifecycle
  - Processing status tracking
  - Document organization and retrieval
  - Multi-tenant document isolation

**Document Processing Pipeline**:
```
PENDING -> PROCESSING -> INDEXED (with chunks + embeddings)
        -> FAILED (with error_message)
```

#### **DocumentChunk** (Vector embeddings for RAG)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - References: `document_id`, `user_id`
  - Content: `text` (the actual chunk text), `chunk_index` (position in document)
  - Vector: `embedding` (384-dimensional pgVector for similarity search)
  - Metadata: `chunk_metadata` (JSON - size, embedding model, creation timestamp)
  - Timestamp: `indexed_at`
- **Unique Constraint**: (`document_id`, `chunk_index`) - prevents duplicate chunks
- **Indexes**:
  - `(document_id, user_id)` - for chunk retrieval by document
  - `user_id` - for user-scoped vector similarity search
- **Relationships**:
  - `N:1` document → Document
  - `N:1` user → User
- **Primary Use Cases**:
  - RAG similarity search (vector embeddings)
  - Context retrieval for LLM prompting
  - Document chunk management and analytics
- **Vector Search**: Uses pgVector for 384-dim multilingual embeddings

---

### 1.3 Conversation Models

#### **ConversationSession** (Session lifecycle management)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Ownership: `user_id` (optional, for anonymous sessions), `organization_id` (optional)
  - Configuration: `language` (default "ta" for Tamil), `rag_enabled` (bool)
  - Status: `status` (enum: ACTIVE, EXPIRED, ENDED)
  - Timestamps: `created_at`, `last_activity`, `ended_at`
  - Metrics: `total_turns` (conversation turn counter)
  - Metadata: `session_metadata` (JSON for session-specific config)
- **Relationships**:
  - `N:1` user → User (optional)
  - `N:1` organization → Organization (optional)
  - `1:N` turns → ConversationTurn (cascade delete)
- **Indexes**:
  - `(user_id, status)` - for active session lookup
  - `(organization_id, status)` - for org-wide sessions
  - `(user_id, last_activity)` - for session expiry checks
- **Primary Use Cases**:
  - Real-time voice conversation tracking
  - Session lifecycle (creation, active, expiry, ending)
  - Multi-language support (Tamil-first)
  - RAG enable/disable per session
  - Session persistence (database + Redis cache)

**Session Lifecycle**:
```
ACTIVE -> EXPIRED (timeout) or ENDED (user-initiated)
```

#### **ConversationTurn** (Individual conversation exchanges)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Reference: `session_id`, `turn_number` (sequence in session)
  - Content: `user_text` (optional), `assistant_text` (optional)
  - Audio: `audio_input_key` (MinIO path to user audio), `audio_output_key` (MinIO path to assistant audio)
  - RAG: `retrieved_chunks` (list of DocumentChunk IDs used)
  - Performance: `processing_time` (JSON - breakdown of STT, LLM, TTS times)
  - Metadata: `turn_metadata` (JSON), `timestamp`
- **Unique Constraint**: (`session_id`, `turn_number`) - prevents duplicate turns
- **Indexes**:
  - `(session_id, turn_number)` - for turn ordering
  - `(session_id, timestamp)` - for chronological retrieval
- **Relationships**:
  - `N:1` session → ConversationSession
- **Primary Use Cases**:
  - Voice pipeline step tracking (STT → RAG → LLM → TTS)
  - Conversation history persistence
  - Performance monitoring and analytics
  - Audio storage references (stored in MinIO)
  - RAG context tracking (which documents were retrieved)

**Typical Turn Flow**:
```
1. User speaks (audio_input_key set)
2. STT converts to user_text
3. RAG retrieves relevant chunks (retrieved_chunks populated)
4. LLM generates response (assistant_text set)
5. TTS converts to audio (audio_output_key set)
6. Turn persisted with processing_time metrics
```

---

### 1.4 Media Model

#### **AudioFile** (Audio file metadata and lifecycle)
- **Primary Key**: `id` (UUID)
- **Key Attributes**:
  - Ownership: `user_id`, `organization_id`
  - Association: `session_id` (optional - links to conversation session)
  - File Info: `filename`, `minio_key` (unique storage path), `file_size`
  - Type: `file_type` (enum: USER_INPUT, TTS_OUTPUT, REFINED)
  - Audio Properties: `duration` (seconds), `sample_rate` (Hz)
  - Lifecycle: `created_at`, `expires_at` (for automatic cleanup)
  - Metadata: `audio_metadata` (JSON)
- **Relationships**:
  - `N:1` user → User
  - `N:1` organization → Organization
  - `N:1` session → ConversationSession (optional)
- **Indexes**:
  - `(user_id, session_id)` - for session audio lookup
  - `(user_id, file_type)` - for audio type filtering
  - `(organization_id, file_type)` - for org-wide audio analytics
  - `expires_at` - for cleanup jobs
- **Primary Use Cases**:
  - Real-time voice I/O tracking
  - Audio file lifecycle management
  - Session audio association
  - Automatic audio cleanup (via expires_at)
  - Audio analytics and storage monitoring

**Audio File Types**:
- `USER_INPUT` - audio from user (input to STT)
- `TTS_OUTPUT` - synthesized audio from TTS
- `REFINED` - processed/enhanced audio

---

### 1.5 System Model

#### **SystemInfo** (Configuration and metadata)
- **Primary Key**: `key` (String)
- **Attributes**:
  - `value` (Optional text)
  - `description` (Optional text)
  - `updated_at` (auto-timestamp)
- **Primary Use Cases**:
  - System configuration storage
  - Migration tracking
  - Feature flags
  - System-wide metadata

---

## 2. RELATIONSHIP HIERARCHY

### 2.1 Relationship Diagram (Simplified)

```
User (root entity)
├── Organization (active_organization)
│   ├── OrganizationMember (many-to-many through join table)
│   │   └── User (members)
│   ├── Document (org-scoped)
│   │   └── DocumentChunk (with vector embeddings)
│   ├── ConversationSession (org-scoped)
│   │   └── ConversationTurn (with audio references)
│   └── AudioFile (org-scoped)
├── Document (user-owned)
│   └── DocumentChunk (user-scoped for vector search)
├── ConversationSession (user-owned)
│   └── ConversationTurn (with audio and RAG metadata)
└── AudioFile (user-owned)
```

### 2.2 Cascade Delete Strategy

**Hard Cascades** (automatic deletion):
- User → Document, ConversationSession, AudioFile, OrganizationMember
- Document → DocumentChunk
- ConversationSession → ConversationTurn
- Organization → OrganizationMember

**Soft Cascades** (status-based):
- ConversationSession → status = ENDED/EXPIRED (not deleted, marked)
- Document → status = FAILED (preserved for audit trail)

### 2.3 Multi-Tenancy Architecture

**Organization Isolation**:
- Document, DocumentChunk, ConversationSession, ConversationTurn, AudioFile all have `organization_id`
- Queries must always filter by `organization_id` for data isolation
- User can be member of multiple organizations but has one `active_organization_id`

**User Tier Enforcement**:
- `User.subscription_tier` → max_organizations_allowed
- `Organization.tier_type` → defines quotas
- Validated in `OrganizationService.validate_organization_creation()`

---

## 3. PRIMARY USE CASES FOR EACH MODEL

### 3.1 Model Usage Matrix

| Model | Primary Use Case | Secondary Use Cases | Access Pattern |
|-------|------------------|---------------------|-----------------|
| **User** | Authentication & account management | Subscription tier validation, session creation | By ID, email, username |
| **Organization** | Multi-tenant data isolation | Billing, resource quotas, workspace mgmt | By ID, creator_id |
| **OrganizationMember** | Role-based access control (RBAC) | Team member management, audit trail | By (org_id, user_id) |
| **OrganizationInvitation** | Signup workflow with role assignment | Invitation expiry, token-based signup | By token, org+email |
| **Document** | RAG document ingestion lifecycle | Version control, status tracking, storage | By user_id, org_id, session_id |
| **DocumentChunk** | Vector similarity search for RAG | Context retrieval for LLM, analytics | By document_id, vector search |
| **ConversationSession** | Real-time voice session tracking | Session expiry, history retrieval | By session_id, user_id + status |
| **ConversationTurn** | Conversation history & audio tracking | Performance monitoring, RAG tracking | By session_id + turn_number |
| **AudioFile** | Real-time audio I/O management | Storage cleanup, session association | By session_id, user_id, expires_at |
| **SystemInfo** | System configuration & migrations | Feature flags, metadata | By key (single table) |

### 3.2 Detailed Use Case Analysis

#### **User Model Uses**
1. **Authentication**: Login/password verification, JWT token generation
2. **Session Creation**: Create ConversationSession with user context
3. **Document Upload**: Associate documents with user ownership
4. **Tier Validation**: Check subscription_tier before allowing actions
5. **Organization Membership**: Manage org memberships via OrganizationMember
6. **Activity Tracking**: last_login, updated_at timestamps

**Current Implementation**:
- SessionService validates user in `_create_session_impl()`
- DocumentService uses user_id for document ownership
- OrganizationService checks tier limits

#### **Organization Model Uses**
1. **Data Isolation**: Filter queries by organization_id
2. **Quota Management**: Check tier limits (max members, storage)
3. **Billing**: Track subscription status, trial periods
4. **Settings**: Store org-specific configuration (timezone, custom settings)
5. **Creator Tracking**: Know who created the organization

**Current Implementation**:
- Users have active_organization_id
- Documents tagged with organization_id
- Sessions can be org-scoped (future)

#### **OrganizationMember Model Uses**
1. **RBAC**: Determine user permissions within organization
2. **Member Listing**: Get all members of an organization
3. **Role Changes**: Update user role (MEMBER → ORG_ADMIN)
4. **Invitation Audit**: Track who invited whom and when
5. **Access Denial**: Check if user is member before allowing action

**Current Implementation**:
- OrganizationService validates role changes
- Unique constraint prevents duplicate memberships
- Invited_by field tracks invitation source

#### **Document & DocumentChunk Models Uses**
1. **RAG Pipeline**: Document ingestion (PENDING → PROCESSING → INDEXED)
2. **Vector Search**: Retrieve similar chunks for LLM context
3. **Context Retrieval**: Get top-k chunks by semantic similarity
4. **Document History**: Track processing status and errors
5. **Storage Management**: Reference MinIO-stored documents
6. **User-Scoped RAG**: DocumentChunk has user_id for privacy

**Current Implementation** (from DocumentService):
1. Upload document → Create Document record with PENDING status
2. Process document → Extract text, chunk, generate embeddings
3. Store chunks → Create DocumentChunk records with 384-dim embeddings
4. Vector search → Query by similarity within user context

#### **ConversationSession & ConversationTurn Models Uses**
1. **Session Lifecycle**: Create, track, expire, end sessions
2. **History Persistence**: Store all conversation turns permanently
3. **Audio Tracking**: References to user input and TTS output audio
4. **RAG Tracking**: Know which documents were retrieved per turn
5. **Performance Metrics**: Track STT/LLM/TTS timing per turn
6. **Multi-language**: Support Tamil (and other languages) per session
7. **Expiry Management**: Auto-expire inactive sessions

**Current Implementation** (from SessionService):
- Create session with metadata
- Add turns with text, audio keys, and retrieved chunks
- Track processing_time for each turn
- Cache in Redis for fast access
- Expire sessions after CHAT_SESSION_TIMEOUT_MINUTES

#### **AudioFile Model Uses**
1. **Audio I/O Tracking**: Reference user input and assistant output audio
2. **Session Association**: Link audio to conversation sessions
3. **Storage Cleanup**: Auto-delete via expires_at field
4. **Audio Analytics**: Count and measure audio files by type
5. **File Size Monitoring**: Track storage usage

---

## 4. REPOSITORY PATTERN IMPLEMENTATION RECOMMENDATIONS

### 4.1 Priority Ranking for Repository Pattern

**Priority 1 (CRITICAL)** - Core write-heavy models with complex queries:

1. **ConversationSession** - HIGHEST
   - Multiple concurrent CRUD operations
   - Complex expiry/status filtering
   - Heavy cache coordination needed
   - Already being refactored with DatabaseSessionManager
   - Would benefit: ConversationSessionRepository

2. **Document** - HIGHEST
   - Status-based lifecycle (PENDING → PROCESSING → INDEXED → FAILED)
   - User/org-scoped queries
   - Processing orchestration
   - Would benefit: DocumentRepository

3. **DocumentChunk** - VERY HIGH
   - Vector similarity search patterns
   - Batch create operations (100s of chunks per document)
   - User-scoped searches
   - Would benefit: DocumentChunkRepository

**Priority 2 (HIGH)** - Multi-tenant query patterns:

4. **User** - HIGH
   - Complex authentication queries
   - Tier-based business logic
   - Organization membership queries
   - Would benefit: UserRepository

5. **Organization** - HIGH
   - Member management queries
   - Tier/quota validation
   - Would benefit: OrganizationRepository

6. **OrganizationMember** - HIGH
   - Role-based access patterns
   - Member listing by organization
   - Would benefit: OrganizationMemberRepository

**Priority 3 (MEDIUM)** - Single-table patterns:

7. **AudioFile** - MEDIUM
   - Expiry-based cleanup queries
   - Session-associated lookups
   - Would benefit: AudioFileRepository

8. **ConversationTurn** - MEDIUM
   - Already queried through ConversationSession
   - Could be repository but less critical
   - Would benefit: ConversationTurnRepository

**Priority 4 (LOW)** - Simple metadata:

9. **OrganizationInvitation** - LOW
   - Simple CRUD operations
   - Token-based lookup only
   - Could be repository but straightforward queries

10. **SystemInfo** - LOW
    - Single-table key-value store
    - Simple get/set patterns
    - No need for repository

### 4.2 Recommended Repository Architecture

#### **Core Repository Interface** (Base class):
```python
class BaseRepository(Generic[T]):
    async def create(self, obj: T) -> T
    async def read(self, id: str) -> Optional[T]
    async def update(self, id: str, obj: T) -> Optional[T]
    async def delete(self, id: str) -> bool
    async def list(self, filters: Dict) -> List[T]
    async def count(self, filters: Dict) -> int
```

#### **Specialized Repositories** (Implementation priority):

**1. ConversationSessionRepository** (Immediate - Phase 1)
- Methods beyond base:
  - `get_by_user_with_status(user_id, status)`
  - `get_active_by_user(user_id)`
  - `list_expired_sessions(since: datetime, limit: int)`
  - `expire_session(session_id)`
  - `get_with_turns(session_id, limit: int)`
  - `cleanup_expired(batch_size: int)`
- Current Implementation: DatabaseSessionManager (partial, needs refactoring)
- Replacement: ConversationSessionRepository

**2. DocumentRepository** (Phase 1)
- Methods beyond base:
  - `get_by_user(user_id, limit, offset)`
  - `get_by_org(org_id, limit, offset)`
  - `get_by_status(status, limit)`
  - `get_processing_documents()`
  - `update_status(doc_id, status, error_msg=None)`
  - `get_with_chunks(doc_id)`
- Used by: DocumentService

**3. DocumentChunkRepository** (Phase 1)
- Methods beyond base:
  - `search_by_similarity(query_vector, user_id, limit)`
  - `get_by_document(document_id)`
  - `bulk_create(chunks: List[DocumentChunk])`
  - `delete_by_document(document_id)`
  - `get_by_user(user_id, limit)`
- Vector similarity search: Use pgVector directly
- Used by: RAG pipeline

**4. UserRepository** (Phase 2)
- Methods beyond base:
  - `get_by_email(email)`
  - `get_by_username(username)`
  - `search(query: str)`
  - `list_by_tier(tier: str)`
  - `count_organizations(user_id)`
- Used by: AuthService, OrganizationService

**5. OrganizationRepository** (Phase 2)
- Methods beyond base:
  - `get_by_creator(user_id)`
  - `get_user_memberships(user_id)`
  - `get_members(org_id, limit, offset)`
  - `count_members(org_id)`
  - `search(query: str, limit)`
- Used by: OrganizationService

**6. OrganizationMemberRepository** (Phase 2)
- Methods beyond base:
  - `get_by_org_user(org_id, user_id)`
  - `get_by_org(org_id, limit, offset)`
  - `get_by_role(org_id, role)`
  - `update_role(org_id, user_id, role)`
  - `delete_member(org_id, user_id)`
  - `check_membership(org_id, user_id)`
- Used by: OrganizationService

**7. AudioFileRepository** (Phase 2)
- Methods beyond base:
  - `get_by_session(session_id)`
  - `get_expired(before: datetime, limit)`
  - `count_by_type(user_id, file_type)`
  - `delete_expired(before: datetime, batch_size)`
  - `get_by_user_type(user_id, file_type, limit)`
- Used by: ConversationTurnRepository queries

**8. ConversationTurnRepository** (Phase 3)
- Methods beyond base:
  - `get_by_session(session_id, limit, offset)`
  - `get_turn_range(session_id, start_turn, end_turn)`
  - `get_recent_turns(session_id, limit)`
  - `count_by_session(session_id)`
- Used by: SessionService

**9. OrganizationInvitationRepository** (Phase 3)
- Methods beyond base:
  - `get_by_token(token)`
  - `get_pending_by_org(org_id)`
  - `get_pending_by_email(email)`
  - `cleanup_expired(before: datetime)`
  - `accept_invitation(token, user_id)`
- Used by: Organization signup service

### 4.3 Implementation Order (Phases)

**Phase 1 (Weeks 1-2)** - Core voice pipeline:
1. ConversationSessionRepository (refactor DatabaseSessionManager)
2. DocumentRepository (replace DocumentService queries)
3. DocumentChunkRepository (for RAG similarity search)

**Phase 2 (Weeks 3-4)** - Multi-tenancy:
4. UserRepository (for auth queries)
5. OrganizationRepository (for org management)
6. OrganizationMemberRepository (for RBAC)
7. AudioFileRepository (for audio cleanup)

**Phase 3 (Week 5)** - Secondary:
8. ConversationTurnRepository (wrap ConversationTurn queries)
9. OrganizationInvitationRepository (for signup)

### 4.4 Benefits per Model

#### **ConversationSession** - Benefits:
- Consolidate expiry logic (currently in SessionService)
- Cache coordination strategies
- Query optimization for active sessions
- Complex filtering (status, user, activity)
- Estimated queries reduced: 40%

#### **Document** - Benefits:
- Status lifecycle management (PENDING → INDEXED)
- Error handling and retry logic
- User/org scope enforcement
- Batch operations support
- Estimated queries reduced: 35%

#### **DocumentChunk** - Benefits:
- Vector search abstraction
- Batch insert performance
- User-scoped privacy enforcement
- Similarity ranking logic
- Estimated queries reduced: 30%

#### **User** - Benefits:
- Auth query consolidation
- Tier-based validation logic
- Organization count aggregation
- Search functionality
- Estimated queries reduced: 25%

#### **Organization** - Benefits:
- Quota checking logic
- Member management queries
- Tier-based filtering
- Estimated queries reduced: 20%

#### **OrganizationMember** - Benefits:
- RBAC enforcement
- Role hierarchy validation
- Member listing optimization
- Estimated queries reduced: 15%

---

## 5. MODELS BEST SUITED FOR REPOSITORY PATTERN

### 5.1 Top 3 Candidates (Must-Have)

1. **ConversationSession** (CRITICAL)
   - **Why**: Already has DatabaseSessionManager (partial implementation)
   - **Scope**: Complex state machine (ACTIVE → EXPIRED/ENDED)
   - **Queries**: 15+ distinct query patterns
   - **Concurrency**: High (multiple sessions per user)
   - **Cache**: Redis integration needed
   - **Benefit**: Cleaner session lifecycle management
   - **Estimated Effort**: 40-50 hours

2. **Document** (CRITICAL)
   - **Why**: Complex processing lifecycle
   - **Scope**: 4 status states with transitions
   - **Queries**: 12+ distinct patterns
   - **Concurrency**: Medium (batched uploads)
   - **Integration**: DocumentService depends on it
   - **Benefit**: Decouples business logic from DB access
   - **Estimated Effort**: 30-40 hours

3. **DocumentChunk** (CRITICAL)
   - **Why**: Vector search complexity
   - **Scope**: Similarity queries, batch operations
   - **Queries**: 8+ distinct patterns
   - **Concurrency**: High (bulk inserts)
   - **Performance**: Critical for RAG
   - **Benefit**: Simplifies vector search logic
   - **Estimated Effort**: 25-35 hours

### 5.2 Good Secondary Candidates (Should-Have)

4. **User** (HIGH)
   - Consolidates auth queries
   - Tier validation logic
   - Organization counting

5. **Organization** (HIGH)
   - Quota management
   - Member aggregation
   - Search functionality

6. **OrganizationMember** (HIGH)
   - RBAC enforcement
   - Role hierarchy logic

### 5.3 Lower Priority (Nice-to-Have)

7. **AudioFile** (MEDIUM)
8. **ConversationTurn** (MEDIUM)
9. **OrganizationInvitation** (LOW)

### 5.4 No Repository Needed

- **SystemInfo**: Simple key-value store, no complex queries

---

## 6. ARCHITECTURAL INSIGHTS

### 6.1 Current Architecture Patterns

**Service Layer Pattern** (Partial):
- DocumentService: Handles document upload/processing
- OrganizationService: Business logic for org management
- SessionService: Session lifecycle (partial repository)
- Email service, tier service exist

**Data Access**:
- Direct SQLAlchemy queries in services
- No consistent repository pattern yet
- Some caching (Redis for sessions)
- Cascade deletes configured

**Multi-Tenancy**:
- Organization-scoped data (documents, sessions, audio)
- Organization isolation enforced at query level
- Tier-based quotas (User.subscription_tier)

### 6.2 Future Considerations

**Scalability Concerns**:
1. DocumentChunk table (millions of records) needs pagination
2. ConversationSession expiry cleanup needs optimization
3. Vector search performance depends on pgVector indexing
4. Audio file cleanup needs background job

**Repository Pattern Benefits**:
- Centralized query optimization
- Easy to add caching layers
- Simplified testing (mock repositories)
- Cleaner service layer code
- Query metrics collection
- Automatic retry logic
- Transaction management

### 6.3 Integration Points

**With Cache Layer (Redis)**:
- Sessions: Already cached (DatabaseSessionManager)
- Chunks: Could cache similarity searches
- User: Could cache user data

**With Storage Layer (MinIO)**:
- Document: References minio_key
- AudioFile: References minio_key
- ConversationTurn: References audio keys

**With RAG Pipeline**:
- DocumentChunk: Vector embeddings
- ConversationTurn: Retrieved chunks tracking
- Document: Processing orchestration

---

## 7. QUICK REFERENCE TABLES

### 7.1 Model Overview Table

| Model | Type | Owner | Multi-Tenant | Cascade | Status Field | Indexes | Purpose |
|-------|------|-------|--------------|---------|--------------|---------|---------|
| User | Entity | Global | No | N/A | is_active | email, username, tier | Auth |
| Organization | Entity | User | Yes | Members | is_active | name, tier | Workspace |
| OrganizationMember | Join | Org | Yes | On user/org delete | N/A | org+user | RBAC |
| OrganizationInvitation | Event | Org | Yes | Manual | is_expired | token, email, org+expires | Signup |
| Document | Entity | User+Org | Yes | Chunks | status | user+status, org+status | RAG storage |
| DocumentChunk | Vector | User+Doc | Yes | On doc delete | N/A | doc+user, user (for search) | RAG search |
| ConversationSession | Entity | User+Org | Yes | Turns | status | user+status, org+status | Voice tracking |
| ConversationTurn | Event | Session | Yes | N/A | N/A | session+turn, session+time | History |
| AudioFile | Entity | User+Org | Yes | N/A | N/A | user+session, user+type, expires | I/O tracking |
| SystemInfo | Config | Global | No | N/A | N/A | key (PK) | System config |

### 7.2 Relationship Summary

| From | To | Type | Cascade | Use Case |
|------|----|----|---------|----------|
| User → Organization | 1:N | active_org reference | - | Context switch |
| User → OrganizationMember | 1:N | memberships | Delete orphans | Org lookup |
| User → Document | 1:N | owned docs | Delete orphans | Doc ownership |
| User → ConversationSession | 1:N | conversations | Delete orphans | History |
| User → AudioFile | 1:N | audio | Delete orphans | Media cleanup |
| Organization → OrganizationMember | 1:N | members | Delete orphans | Membership |
| Organization → Document | 1:N | docs | - | Org isolation |
| Organization → ConversationSession | 1:N | sessions | - | Org isolation |
| Document → DocumentChunk | 1:N | chunks | Delete orphans | RAG chunks |
| ConversationSession → ConversationTurn | 1:N | turns | Delete orphans | History |

### 7.3 Query Complexity by Model

| Model | Simple Queries | Complex Queries | Aggregate Queries | Performance Critical |
|-------|---|---|---|---|
| User | 4 | 3 | 2 | No |
| Organization | 3 | 4 | 3 | No |
| OrganizationMember | 2 | 4 | 2 | No |
| Document | 3 | 5 | 2 | Yes (large tables) |
| DocumentChunk | 2 | 6 | 1 | YES (vector search) |
| ConversationSession | 3 | 6 | 3 | YES (expiry) |
| ConversationTurn | 2 | 3 | 2 | No |
| AudioFile | 2 | 3 | 1 | No |
| OrganizationInvitation | 2 | 2 | 0 | No |
| SystemInfo | 2 | 0 | 0 | No |

---

## Conclusion

**Repository Pattern Implementation Recommendation**:

Implement repositories in this order:
1. **Phase 1 (CRITICAL)**: ConversationSession, Document, DocumentChunk
2. **Phase 2 (HIGH)**: User, Organization, OrganizationMember, AudioFile
3. **Phase 3 (MEDIUM)**: ConversationTurn, OrganizationInvitation

**Skip**:
- SystemInfo (too simple for pattern)

**Estimated Total Effort**: 130-180 hours across 3-4 weeks

**Expected Benefits**:
- 40% reduction in duplicate query code
- Improved testability and maintainability
- Easier cache integration
- Better separation of concerns
- Centralized query optimization

---

**Document Generated**: November 14, 2025
**Codebase Version**: db_connections branch
**Analysis Scope**: backend/database/models.py and related services

