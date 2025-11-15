# Database Models - Visual Reference Guide

## Model Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                         SYSTEM LAYER                             │
│                       (SystemInfo)                               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                        CORE AUTHENTICATION                               │
│                                                                          │
│  ┌──────────────┐         ┌─────────────────┐  ┌──────────────────┐   │
│  │    User      │◄────────┤ Organization    │──►OrganizationMember│   │
│  │ (Auth Root)  │         │  (Workspace)    │  │   (RBAC Join)    │   │
│  └──────────────┘         └─────────────────┘  └──────────────────┘   │
│        ▲                                                │                │
│        │                                                ▼                │
│        │                          ┌─────────────────────────────────┐   │
│        │                          │ OrganizationInvitation          │   │
│        │                          │ (Pending Signup + Role)         │   │
│        │                          └─────────────────────────────────┘   │
│        └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       CONVERSATION PIPELINE                              │
│                                                                          │
│  ┌────────────────────────┐         ┌──────────────────────────────┐   │
│  │ ConversationSession    │ 1:N ───►│  ConversationTurn            │   │
│  │ (Session Lifecycle)    │◄────────│  (Individual Exchanges)      │   │
│  │ ↑ ACTIVE               │         │  ↓ STT→RAG→LLM→TTS         │   │
│  │ ↓ EXPIRED/ENDED        │         │  • audio_input_key (User)    │   │
│  │ ↓ status tracking      │         │  • audio_output_key (TTS)    │   │
│  │                        │         │  • retrieved_chunks (RAG)    │   │
│  │ FK: user_id            │         │  • processing_time metrics   │   │
│  │ FK: organization_id    │         └──────────────────────────────┘   │
│  └────────────────────────┘                                             │
│           ▲                                                              │
│           │                                                              │
│         User (optional for anonymous sessions)                         │
│         Organization (optional, for multi-tenant)                      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                                     │
│                                                                          │
│  ┌─────────────────────────┐         ┌──────────────────────────────┐  │
│  │    Document             │ 1:N ───►│  DocumentChunk               │  │
│  │ (File Metadata)         │◄────────│  (Vector Embeddings)         │  │
│  │ ↓ PENDING               │         │                              │  │
│  │ ↓ PROCESSING            │         │  • text (chunk content)      │  │
│  │ ↓ INDEXED               │         │  • embedding (384-dim)       │  │
│  │ ↓ FAILED                │         │  • chunk_index               │  │
│  │                         │         │  • chunk_metadata            │  │
│  │ FK: user_id             │         │  FK: user_id (scoped search) │  │
│  │ FK: organization_id     │         │  FK: document_id             │  │
│  │ MinIO: minio_key        │         └──────────────────────────────┘  │
│  │ Processing: minio link  │              ▲                             │
│  │                         │              │ Vector Similarity Search    │
│  │ Session grouping        │         RAG Context Retrieval              │
│  └─────────────────────────┘         LLM Prompting                      │
│           ▲                                                              │
│           │                                                              │
│         User (ownership)                                                │
│         Organization (scoping)                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       AUDIO STORAGE                                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │           AudioFile (Media Lifecycle)                        │       │
│  │  • minio_key (storage path)                                  │       │
│  │  • file_type: USER_INPUT | TTS_OUTPUT | REFINED              │       │
│  │  • duration, sample_rate, file_size                          │       │
│  │  • expires_at (auto-cleanup)                                 │       │
│  │  • FK: user_id, organization_id, session_id (optional)       │       │
│  └──────────────────────────────────────────────────────────────┘       │
│           ▲ Referenced by ConversationTurn                              │
│           │ Referenced in conversation flow                             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Session Lifecycle State Machine

```
                    ┌─────────────┐
                    │   CREATE    │
                    │  New Session│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────────┐
          ┌────────►│     ACTIVE      │◄────┐
          │         │ (User talking)  │     │
          │         └────┬────────────┘     │
          │              │                  │ Activity Update
          │              │                  │ (keep-alive)
          │         TIMEOUT                 │
          │         (no activity)           │
          │              │                  │
          │              ▼                  │
          │         ┌──────────────┐        │
          └─────────┤   EXPIRED    │        │
                    │ (Timed Out)  │        │
                    └──────────────┘        │
                                            │
                    ┌──────────────┐        │
                    │    ENDED     │◄───────┘
                    │ (User-ended) │
                    └──────────────┘

Transitions:
- CREATE → ACTIVE: Session creation
- ACTIVE → EXPIRED: No activity for CHAT_SESSION_TIMEOUT_MINUTES
- ACTIVE → ENDED: User ends conversation
- All → Database with associated ConversationTurns
```

## Document Processing Pipeline

```
                    ┌──────────┐
                    │ Upload   │
                    │ to MinIO │
                    └────┬─────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    Document Record   │
              │    Status: PENDING   │
              │    minio_key: set    │
              │    file_size: set    │
              └────┬─────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Update Status:          │
        │  PENDING → PROCESSING    │
        │  Download from MinIO     │
        └────┬─────────────────────┘
             │
             ├─── Text Extraction (PDF/DOCX/TXT)
             │         │
             │         ▼
             │    ┌─────────────┐
             │    │ Full Text   │
             │    └─────────────┘
             │         │
             ├─────────┤
             │         │
             │         ▼
             │    ┌─────────────────┐
             │    │ Text Chunking   │
             │    │ (size/overlap)  │
             │    └─────────────────┘
             │         │
             │         ▼
             │    ┌──────────────────┐
             │    │ Embedding Model  │
             │    │ 384-dim vectors  │
             │    └──────────────────┘
             │         │
             │         ▼
             │    ┌──────────────────┐
             │    │ DocumentChunk    │
             │    │ Records Created  │
             │    │ (+ embeddings)   │
             │    └──────────────────┘
             │         │
             ▼         ▼
      ┌────────────────────────────┐
      │  Status: INDEXED           │
      │  processed_date: set       │
      │  All chunks stored in DB   │
      └────────────────────────────┘

Error Path: Any step fails → Status: FAILED, error_message logged
```

## Data Isolation & Multi-Tenancy

```
┌─────────────────────────────────────────────────────────┐
│  Organization Scope: Every query filters by org_id      │
└─────────────────────────────────────────────────────────┘

User (Global)
  ├── Organization A (tenant scope)
  │    ├── Document 1 (org_id = A)
  │    │   ├── DocumentChunk 1.1 (org scoped)
  │    │   └── DocumentChunk 1.2 (org scoped)
  │    ├── Document 2 (org_id = A)
  │    ├── ConversationSession A.1 (org_id = A)
  │    │   ├── ConversationTurn A.1.1
  │    │   └── ConversationTurn A.1.2
  │    └── AudioFile A.1 (org_id = A)
  │
  └── Organization B (different tenant scope)
       ├── Document 3 (org_id = B) [ISOLATED FROM A]
       ├── ConversationSession B.1 (org_id = B) [ISOLATED FROM A]
       └── AudioFile B.1 (org_id = B) [ISOLATED FROM A]

Query Rule: WHERE organization_id = ? ALWAYS applied to:
- Document
- DocumentChunk
- ConversationSession
- ConversationTurn
- AudioFile
```

## Caching Strategy

```
┌───────────────────────────────────┐
│  Redis Cache Layers               │
└───────────────────────────────────┘

Fast Path (Cached):
┌─────────────────────────────┐
│ ConversationSession         │
│ session_id → Session Data   │
│ user_id:sessions → List     │
│ session:turns → Turn List   │
└─────────────────────────────┘
         ▲
         │ Cache Hits (95%+ for active sessions)
    SQL Query
         │
    PostgreSQL

Slow Path (Full Query):
├─ DocumentChunk: Vector search (not cached, uses pgVector)
├─ User: Auth lookups (could cache)
├─ Organization: Membership queries (could cache)
└─ AudioFile: Expiry cleanup (batch operations)
```

## Relationship Cardinality Summary

```
User (1) ──────────┬─── (N) Organization (active org reference)
                   ├─── (N) Document (ownership + cascade)
                   ├─── (N) ConversationSession (history + cascade)
                   ├─── (N) AudioFile (media + cascade)
                   ├─── (N) OrganizationMember (memberships + cascade)
                   └─── (N) Organization (creator link)

Organization (1) ──┬─── (N) OrganizationMember (members + cascade)
                   ├─── (N) Document (org scope)
                   ├─── (N) ConversationSession (org scope)
                   ├─── (N) AudioFile (org scope)
                   └── (1) User (creator reference)

OrganizationMember (N:N) ──┬─── (1) User
                           └─── (1) Organization

Document (1) ───────────── (N) DocumentChunk (cascade delete)
                           └─── (1) User (ownership)

ConversationSession (1) ────┬─── (N) ConversationTurn (cascade)
                            ├─── (1) User (optional)
                            └─── (1) Organization (optional)

ConversationTurn (N) ──────── (1) ConversationSession

AudioFile (N) ──┬─── (1) User
                ├─── (1) Organization
                └─── (1) ConversationSession (optional)
```

## Enum Values Reference

```
UserRole (on User):
  - USER (default)
  - ADMIN (system admin)
  - ORGANIZATION_ADMIN

DocumentStatus (on Document):
  - PENDING (uploaded, waiting to process)
  - PROCESSING (extracting, chunking, embedding)
  - INDEXED (ready for RAG)
  - FAILED (error during processing)

SessionStatus (on ConversationSession):
  - ACTIVE (user can interact)
  - EXPIRED (timed out, no activity)
  - ENDED (user closed)

AudioFileType (on AudioFile):
  - USER_INPUT (audio from user speech → STT input)
  - TTS_OUTPUT (synthesized audio from TTS → user playback)
  - REFINED (post-processed audio)

OrganizationRole (on OrganizationMember):
  - MEMBER (regular user)
  - ORG_ADMIN (organization admin)
  - ADMIN (legacy, avoid)
  - OWNER (org creator/owner)
```

## Index Optimization Guide

```
High-Impact Indexes (Used Frequently):
├─ User.email (unique, auth lookup)
├─ User.username (unique, auth lookup)
├─ Document.(user_id, status) (filtering uploads by user/status)
├─ Document.(organization_id, status) (org-wide document discovery)
├─ DocumentChunk.user_id (user-scoped vector search)
├─ ConversationSession.(user_id, status) (active sessions lookup)
├─ ConversationSession.(organization_id, status) (org sessions)
├─ ConversationTurn.(session_id, turn_number) (history retrieval)
├─ AudioFile.(user_id, session_id) (session audio lookup)
├─ AudioFile.expires_at (cleanup jobs)
├─ OrganizationInvitation.token (signup link)
├─ OrganizationInvitation.(organization_id, invited_email) (unique)
└─ OrganizationInvitation.(organization_id, expires_at) (cleanup)

Compound Indexes (for common WHERE + ORDER BY):
├─ Document.(user_id, status, upload_date DESC)
├─ ConversationSession.(user_id, last_activity DESC)
├─ ConversationTurn.(session_id, turn_number ASC)
└─ AudioFile.(organization_id, file_type, created_at DESC)
```

## Vector Embedding Specifications

```
Model: DocumentChunk.embedding
├─ Dimensions: 384
├─ Type: pgVector
├─ Model Used: sentence-transformers (multilingual)
├─ Similarity Metric: Cosine similarity
├─ Use Case: RAG context retrieval
└─ Query: SELECT * FROM document_chunks 
           WHERE user_id = ? 
           ORDER BY embedding <-> query_embedding 
           LIMIT 10

Performance:
├─ Indexing: pgVector IVFFLAT or HNSW recommended
├─ Query Time: ~100ms per similarity search
├─ Storage: 384 floats × 8 bytes = ~3KB per chunk
└─ Scalability: Supports millions of chunks
```

## Transaction Patterns

```
Session Creation:
1. BEGIN TRANSACTION
2. INSERT INTO conversation_sessions (...)
3. COMMIT
4. Cache in Redis
5. Return session_id

Turn Addition:
1. BEGIN TRANSACTION
2. SELECT session (FOR UPDATE to prevent race)
3. INSERT INTO conversation_turns (...)
4. UPDATE conversation_sessions SET total_turns = total_turns + 1
5. COMMIT
6. Cache turn in Redis
7. Return turn_id

Document Processing:
1. BEGIN TRANSACTION
2. UPDATE document SET status = PROCESSING
3. COMMIT (release lock)
4. Process (extract, chunk, embed) [LONG OPERATION]
5. BEGIN TRANSACTION
6. DELETE old chunks IF EXISTS
7. INSERT new chunks (bulk)
8. UPDATE document SET status = INDEXED, processed_date = NOW()
9. COMMIT
10. Cache in Redis (optional)
```

