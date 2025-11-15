# API Routes Visual Architecture Map

**Purpose:** Visual representation of API routes, their database dependencies, and migration order

---

## Current Architecture (As-Is)

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  auth.py     │  │  org.py      │  │  admin_v2.py │          │
│  │              │  │              │  │              │          │
│  │ 12+ queries  │  │ 18+ queries  │  │ 4 queries    │          │
│  │ (inline)     │  │ (inline)     │  │ (inline)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                │                    │
│         └─────────────────┼────────────────┘                    │
│         │                 │                │                    │
│         └────────────────┴───────────────┬─┘                    │
│                          │                                       │
│  ┌──────────────┐  ┌────▼────────┐  ┌──────────────┐          │
│  │  chat.py     │  │  audio.py    │  │  speech.py   │          │
│  │              │  │              │  │              │          │
│  │ SessionMgr ✓ │  │ 4 queries    │  │ No DB access │          │
│  │ (Delegated)  │  │ (inline)     │  │ (N/A)        │          │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘          │
│         │                 │                                     │
└─────────┼─────────────────┼─────────────────────────────────────┘
          │                 │
          └─────────────────┼─────────────────┐
                            │                 │
                  ┌─────────▼─────────┐  ┌───▼──────────┐
                  │  SQL Queries      │  │ MinIO, Redis │
                  │  (Scattered)      │  │ (Abstracted) │
                  │                   │  │              │
                  │ - No validation   │  └──────────────┘
                  │ - Duplicated      │
                  │ - Hard to test    │
                  │ - 94+ total       │
                  └───────────────────┘
```

---

## Target Architecture (Future State)

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  auth.py     │  │  org.py      │  │  admin_v2.py │          │
│  │              │  │              │  │              │          │
│  │ Clean routes │  │ Clean routes │  │ Clean routes │          │
│  │ (Delegated)  │  │ (Delegated)  │  │ (Delegated)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                │                    │
│         └──────────┬──────┴────────────┬───┘                    │
│                    │                   │                        │
│  ┌──────────────┐  │  ┌──────────────┐ │                       │
│  │  chat.py     │  │  │  audio.py    │ │                       │
│  │              │  │  │              │ │                       │
│  │ SessionMgr ✓ │  │  │ Audio Svc ✓  │ │                       │
│  │ (Delegated)  │  │  │ (Delegated)  │ │                       │
│  └──────┬───────┘  │  └──────┬───────┘ │                       │
│         │          │         │         │                       │
└─────────┼──────────┼─────────┼─────────┼───────────────────────┘
          │          │         │         │
        ┌─┴──────────┴─┐      ┌┴─────────┴─────────┐
        │ Repository   │      │  Service Layer    │
        │ Layer        │      │                   │
        │              │      │ - Business logic  │
        │ - UserRepo   │      │ - Validation      │
        │ - OrgRepo    │      │ - Transactions    │
        │ - OrgMemRepo │      │ - Caching         │
        │ - DocRepo    │      └───────────┬───────┘
        │ - AudioRepo  │                  │
        │ - OrgPermRepo│                  │
        └──────┬───────┘                  │
               │                          │
               └──────────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │ Database Abstraction  │
                  │                       │
                  │ - Async/await         │
                  │ - Transactions        │
                  │ - Connection pooling  │
                  │ - Query validation    │
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │ PostgreSQL + pgVector │
                  │ Redis Cache           │
                  │ MinIO Storage         │
                  └───────────────────────┘
```

---

## Query Density Visualization

### Current State (By Lines)

```
auth.py (517 lines)
█████████████████████░░░░░░░░░░░░░░░░░░░░░░ 12+ DB queries
Ratio: 1 query per 43 lines

organization.py (732 lines)
█████████████████████████████░░░░░░░░░░░░░░░ 18+ DB queries
Ratio: 1 query per 41 lines

admin_v2.py (373 lines)
██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 4 DB queries
Ratio: 1 query per 93 lines

chat.py (773 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Fully delegated ✓

audio.py (374 lines)
████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 4 DB queries
Ratio: 1 query per 94 lines

speech.py (129 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: N/A

Total: 94+ inline queries scattered across 5 routes
```

### Target State (After Migration)

```
auth.py (400-420 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Fully delegated ✓

organization.py (500-520 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Fully delegated ✓

admin_v2.py (350 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Fully delegated ✓

chat.py (773 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Already clean ✓

audio.py (350 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: Fully delegated ✓

speech.py (129 lines)
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 DB queries
Ratio: N/A

Total: 0 inline queries - all in 40+ repository methods
```

---

## Dependency Tree

### Current (Tangled)

```
auth.py
  ├─ User model (CRUD)
  │  └─ Direct queries
  │     └─ Validation scattered
  │
  ├─ Organization model (ops)
  │  ├─ Direct queries
  │  └─ AuthHelper (permissions)
  │     └─ Also in organization.py
  │
  └─ Helper functions
     └─ Duplicated in multiple files

organization.py
  ├─ Organization model (CRUD + cascade)
  │  ├─ Direct queries
  │  └─ AuthHelper (permissions)
  │     └─ Also in auth.py (duplicate!)
  │
  ├─ OrganizationMember model (ops)
  │  ├─ Direct queries
  │  └─ Complex validation
  │
  └─ OrganizationService
     └─ Some logic here, some inline

admin_v2.py
  ├─ Document model (query)
  │  └─ Direct query + auth check
  │
  └─ DocumentService
     └─ Main logic delegated ✓

chat.py
  ├─ SessionManager
  │  └─ All queries delegated ✓
  │
  └─ ConversationSession model
     └─ Accessed via manager
```

### Target (Clean)

```
auth.py
  ├─ AuthRoute (handler)
  │  ├─ Injects: UserRepository
  │  ├─ Injects: OrganizationRepository
  │  └─ Injects: OrganizationPermissionRepository
  │
  └─ Calls service layer
     └─ All DB via repositories ✓

organization.py
  ├─ OrganizationRoute (handler)
  │  ├─ Injects: OrganizationRepository
  │  ├─ Injects: OrganizationMemberRepository
  │  └─ Injects: OrganizationPermissionRepository
  │
  └─ Calls service layer
     └─ All DB via repositories ✓

admin_v2.py
  ├─ AdminRoute (handler)
  │  ├─ Injects: DocumentRepository
  │  └─ Injects: DocumentService
  │
  └─ Calls service layer
     └─ All DB via repositories ✓

chat.py
  ├─ ChatRoute (handler)
  │  └─ Injects: SessionManager
  │
  └─ Already clean ✓

audio.py
  ├─ AudioRoute (handler)
  │  ├─ Injects: AudioFileRepository
  │  ├─ Injects: AudioFileService
  │  └─ Injects: UserTierService
  │
  └─ Calls service layer
     └─ All DB via repositories ✓
```

---

## Migration Sequence Timeline

```
┌─── Phase 1: Foundation (2-3 days) ────────────────────────────────┐
│                                                                     │
│  UserRepository              OrganizationPermissionRepository      │
│  ├─ create()                 ├─ verify_membership()                │
│  ├─ get_by_email()           ├─ get_user_role()                   │
│  ├─ get_by_email_or_username()├─ verify_permission()              │
│  ├─ get_by_id()              ├─ count_owners()                    │
│  ├─ exists()                 └─ can_access_org()                  │
│  ├─ update_role()                                                 │
│  ├─ update_status()     ┌──────────────────────────────────┐      │
│  ├─ list()              │ Refactor: auth.py                │      │
│  └─ list_by_active()    │ Remove: 12 inline queries       │      │
│                         │ Add: Repository injections       │      │
│                         │ Result: Clean handler layer      │      │
│                         └──────────────────────────────────┘      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                             ▼
┌─── Phase 2: Organization (2-3 days) ──────────────────────────────┐
│  [Depends on Phase 1 completing]                                   │
│                                                                     │
│  OrganizationRepository      OrganizationMemberRepository          │
│  ├─ create()                 ├─ get_by_organization()              │
│  ├─ get_by_id()              ├─ get_by_id()                        │
│  ├─ get_by_id_with_members() ├─ create()                           │
│  ├─ get_user_organizations() ├─ invite()                           │
│  ├─ update()                 ├─ update_role()                      │
│  ├─ soft_delete()            ├─ remove()                           │
│  ├─ soft_delete_with_cascade()└─ remove_with_validation()          │
│  └─ get_active_by_id()                                             │
│                         ┌──────────────────────────────────┐       │
│                         │ Refactor: organization.py         │       │
│                         │ Remove: 18 inline queries        │       │
│                         │ Add: Repository injections       │       │
│                         │ Consolidate: Org + Perm logic    │       │
│                         │ Result: Clean handler layer      │       │
│                         └──────────────────────────────────┘       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                             ▼
┌─── Phase 3: Admin (1-2 days) ────────────────────────────────────┐
│  [Depends on Phase 1 completing]                                  │
│                                                                    │
│  DocumentRepository                                                │
│  ├─ get_accessible_document()                                     │
│  ├─ get_unauthorized_documents()                                  │
│  └─ list_user_documents()                                         │
│                    ┌──────────────────────────────────┐            │
│                    │ Refactor: admin_v2.py            │            │
│                    │ Remove: 4 inline queries         │            │
│                    │ Add: Repository injections       │            │
│                    │ Already mostly delegated ✓       │            │
│                    │ Result: Fully clean              │            │
│                    └──────────────────────────────────┘            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                             ▼
┌─── Phase 4: Media (1-2 days) ────────────────────────────────────┐
│  [Independent - can run parallel with Phase 2-3]                  │
│                                                                    │
│  AudioFileRepository      AudioFileService                        │
│  ├─ get_by_id_and_session()├─ handle_expiry_logic()               │
│  ├─ get_by_session()       ├─ aggregate_metrics()                 │
│  ├─ get_with_metadata()    └─ validate_retention()                │
│  └─ create()                                                      │
│                    ┌──────────────────────────────────┐            │
│                    │ Refactor: audio.py               │            │
│                    │ Remove: 4 inline queries         │            │
│                    │ Add: Repository injections       │            │
│                    │ Add: Service layer               │            │
│                    │ Result: Fully clean              │            │
│                    └──────────────────────────────────┘            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                             ▼
            ✓ All routes cleaned and migrated
            ✓ 40+ repository methods in place
            ✓ 0 inline queries in routes
            ✓ All tests passing
            ✓ Ready for production
```

---

## Model-Repository Mapping

```
User Model
  │
  └─ UserRepository
      ├─ create(email, username, password_hash, ...)
      ├─ get_by_id(user_id)
      ├─ get_by_email(email)
      ├─ get_by_username(username)
      ├─ get_by_email_or_username(identifier)
      ├─ exists_by_email_or_username(email, username)
      ├─ get_active_by_id(user_id)
      ├─ update_role(user_id, role)
      ├─ update_status(user_id, is_active)
      ├─ list(skip, limit)
      └─ list_by_active()

Organization Model
  │
  └─ OrganizationRepository
      ├─ create(name, description, creator_id, ...)
      ├─ get_by_id(org_id)
      ├─ get_by_id_with_members(org_id)
      ├─ get_user_organizations(user_id)
      ├─ update(org_id, update_data)
      ├─ soft_delete(org_id)
      ├─ soft_delete_with_cascade(org_id)
      ├─ exists_by_name(name)
      └─ get_active_by_id(org_id)

OrganizationMember Model
  │
  └─ OrganizationMemberRepository
      ├─ get_by_organization(org_id)
      ├─ get_by_id(member_id)
      ├─ create(org_id, user_id, role, ...)
      ├─ invite(org_id, email, role, invited_by)
      ├─ update_role(member_id, new_role)
      ├─ remove(member_id)
      └─ remove_with_validation(member_id, org_id)

Permission Model (Implicit)
  │
  └─ OrganizationPermissionRepository
      ├─ verify_membership(user_id, org_id)
      ├─ get_user_role(user_id, org_id)
      ├─ verify_permission(user_id, org_id, roles)
      ├─ count_owners(org_id)
      └─ can_access_org(user_id, org_id)

Document Model
  │
  └─ DocumentRepository
      ├─ get_accessible_document(doc_id, user_id)
      ├─ get_unauthorized_documents(doc_ids, user_id)
      └─ list_user_documents(user_id, skip, limit)

AudioFile Model
  │
  └─ AudioFileRepository
      ├─ get_by_id_and_session(file_id, session_id)
      ├─ get_by_session(session_id)
      ├─ get_with_metadata(file_id, session_id)
      └─ create(session_id, file_path, file_size, ...)

ConversationSession Model
  │
  └─ SessionManager (Already Migrated ✓)
      ├─ create_session(user_id, language, rag_enabled)
      ├─ get_session(session_id)
      ├─ list_user_sessions(user_id, limit)
      ├─ delete_session(session_id, user_id)
      ├─ get_conversation_history(session_id, limit)
      ├─ get_session_stats(session_id)
      └─ add_conversation_turn(...)
```

---

## Anti-Pattern Elimination Map

```
BEFORE: Inline Queries
┌──────────────────┐
│  Route Handler   │
│  ├─ Validate     │
│  ├─ Query DB     │ ← Business logic + data access mixed
│  ├─ Process      │
│  └─ Return       │
└──────────────────┘
       │
       └─ Hard to test
       └─ Hard to reuse
       └─ Hard to change

AFTER: Clean Separation
┌──────────────────┐
│  Route Handler   │
│  ├─ Validate     │
│  ├─ Call service │ ← Business logic only
│  └─ Return       │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Service/Handler  │
│  ├─ Apply logic  │
│  └─ Call repo    │ ← Business rules
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Repository       │
│  ├─ Query DB     │ ← Data access only
│  ├─ Map results  │
│  └─ Return       │
└──────────────────┘
       │
       ▼
       DB

Benefits:
  ✓ Test routes without DB
  ✓ Test repos independently
  ✓ Reuse queries across routes
  ✓ Change DB without touching routes
```

---

## File Size Impact Projection

```
BEFORE (Current)
auth.py:              517 lines (12 queries + logic)
organization.py:      732 lines (18 queries + logic)
admin_v2.py:          373 lines (4 queries + logic)
audio.py:             374 lines (4 queries + logic)
────────────────────────────────
Routes Total:       1,996 lines

AFTER (Projected)
auth.py:              400 lines (clean, delegated)
organization.py:      520 lines (clean, delegated)
admin_v2.py:          350 lines (cleaner)
audio.py:             350 lines (clean, delegated)
────────────────────────────────
Routes Total:       1,620 lines (↓ 19%)

NEW REPOSITORIES
UserRepository:       150 lines
OrganizationRepository: 200 lines
OrganizationMemberRepository: 180 lines
OrganizationPermissionRepository: 120 lines
DocumentRepository:   100 lines
AudioFileRepository:  100 lines
────────────────────────────────
Repositories Total: 850 lines (NEW)

RESULT
Total code:         2,470 lines (↑ 24% total)
BUT: Much better organized
  - Routes: 1,620 lines (down)
  - Repositories: 850 lines (new, testable)
  - Duplicated logic: ELIMINATED
  - Code reuse: MAXIMIZED
```

---

## Integration Points

```
┌────────────────────────────────────────────────────────────┐
│                    HTTP Request                            │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      Route Handler (routes/*.py)     │
        │  (Clean, no database access)         │
        └──────────────────────────────────────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
                ▼          ▼          ▼
        ┌────────────┐ ┌────────┐ ┌──────────┐
        │  Service   │ │Helper  │ │  Auth    │
        │   Layer    │ │Classes │ │Middleware│
        │            │ │(JWT,   │ │          │
        │(Business   │ │ etc)   │ │          │
        │ logic)     │ │        │ │          │
        └──────┬─────┘ └────────┘ └──────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │   Repository Layer (NEW)     │
    │  - UserRepository            │
    │  - OrganizationRepository    │
    │  - DocumentRepository        │
    │  - etc (40+ methods total)   │
    │  (All database queries)      │
    └──────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  SQLAlchemy ORM              │
    │  (Connection pooling)        │
    │  (Query caching)             │
    │  (Transaction management)    │
    └──────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  PostgreSQL Database         │
    │  + pgVector Extension        │
    │  (Persistent storage)        │
    └──────────────────────────────┘
```

---

## Success Visualization

```
Current State                   Target State
═══════════════════════════════════════════════════════════════

Routes + Inline Queries         Routes (Clean)
    │                               │
    ├─ auth.py (12 queries)        ├─ auth.py (0 queries)
    │                               │
    ├─ organization.py (18 queries) ├─ organization.py (0 queries)
    │                               │
    ├─ admin_v2.py (4 queries)     ├─ admin_v2.py (0 queries)
    │                               │
    ├─ audio.py (4 queries)        ├─ audio.py (0 queries)
    │                               │
    ├─ chat.py ✓                   ├─ chat.py ✓
    │                               │
    ├─ speech.py (N/A)             └─ speech.py (N/A)
    │
    └─ Total: 94 queries           Repositories (Clean)
    │  scattered                       │
    │  duplicated                      ├─ UserRepository (9)
    │  hard to test                    ├─ OrganizationRepository (9)
    │  hard to maintain                ├─ OrganizationMemberRepository (7)
    │  hard to change                  ├─ OrganizationPermissionRepository (4)
    │  no single source of truth       ├─ DocumentRepository (3)
    │  transaction boundaries missing  └─ AudioFileRepository (4)
    │                                     
    │                                  Total: 40 queries
    │                                  organized
    │                                  testable
    │                                  maintainable
    │                                  changeable
    │                                  single source of truth
    │                                  transaction boundaries defined
    │
    └─ Result: Code smell            └─ Result: Production ready
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Ready for presentation

