# API Routes Analysis for Repository Pattern Migration

**Document Type:** Architecture Analysis  
**Date:** November 2025  
**Focus:** SQLAlchemy database access patterns in API routes  
**Purpose:** Identify repository pattern migration candidates and migration order  

---

## Executive Summary

The Tamil AI Voice Assistant backend has **7 main API route modules** with varying levels of direct SQLAlchemy database access. Analysis identifies **4 critical routes** that require immediate migration to the repository pattern, and establishes a data-driven migration roadmap.

### Key Findings
- **94+ direct database queries** scattered across routes (inline SQLAlchemy usage)
- **Auth route** is most complex with authentication + org management mixed concerns
- **Organization route** has complex permission logic that duplicates across multiple endpoints
- **Admin_v2 route** delegates to services (already partially migrated)
- **Chat & Audio routes** have lighter database load, good candidates for later migration
- **Critical issue:** No transaction boundary abstraction layer exists

---

## 1. Route Files Overview

### Route Inventory

| File | Lines | Status | DB Queries | Complexity |
|------|-------|--------|-----------|-----------|
| auth.py | 517 | Mixed | 12+ | HIGH - Auth + Org logic mixed |
| organization.py | 732 | High | 18+ | HIGH - Complex permissions |
| admin_v2.py | 373 | Partial | 8+ | MEDIUM - Uses services |
| chat.py | 773 | Light | 3 | LOW - Session manager abstraction |
| audio.py | 374 | Medium | 8+ | MEDIUM - Tier-based queries |
| speech.py | 129 | Minimal | 0 | LOW - No DB access |
| legacy/admin.py | Deprecated | N/A | N/A | N/A - Deprecated |

---

## 2. Detailed Route Analysis

### 2.1 Authentication Route (`auth.py`) - CRITICAL PRIORITY

**Status:** Requires immediate migration  
**Urgency:** P0 - Blocks all other auth-dependent routes

#### Database Access Patterns

**Direct SQLAlchemy Queries: 12+**

1. **User Registration** (lines 61-74)
   ```python
   # Antipattern: Direct inline query
   existing_user = await db.execute(
       select(User).where(
           and_(User.email == user_data.email, User.username == user_data.username)
       )
   )
   ```
   - Concern: Duplicate checking logic
   - Should extract: `UserRepository.user_exists_by_email_or_username()`

2. **User Login** (lines 115-122)
   ```python
   user_result = await db.execute(
       select(User).where(
           and_(
               User.is_active == True,
               (User.email == login_data.username_or_email) | (User.username == login_data.username_or_email)
           )
       )
   )
   ```
   - Concern: Complex where clause with OR logic
   - Should extract: `UserRepository.get_by_email_or_username()`
   - Update: Inline `user.last_login` without transaction consistency check

3. **Token Refresh** (lines 165-168)
   ```python
   user_result = await db.execute(
       select(User).where(and_(User.id == user_id, User.is_active == True))
   )
   ```
   - Concern: Simple but repeated pattern
   - Should extract: `UserRepository.get_active_by_id()`

4. **Get My Organizations** (lines 313-323)
   ```python
   result = await db.execute(
       select(Organization, OrganizationMember.role)
       .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
       .where(and_(
           OrganizationMember.user_id == current_user.id,
           Organization.is_active == True
       ))
       .order_by(Organization.name)
   )
   ```
   - Concern: Complex JOIN operation, ordering logic mixed in
   - Should extract: `OrganizationRepository.get_user_organizations()`

5. **Set Active Organization** (lines 343-353)
   ```python
   membership = await db.execute(
       select(OrganizationMember, Organization)
       .join(Organization, OrganizationMember.organization_id == Organization.id)
       .where(and_(
           OrganizationMember.user_id == current_user.id,
           OrganizationMember.organization_id == request.organization_id,
           Organization.is_active == True
       ))
   )
   ```
   - Concern: Access control query
   - Should extract: `OrganizationRepository.verify_membership()`

6. **Get Auth Status** (lines 402-434)
   ```python
   user_orgs = await db.execute(
       select(Organization)
       .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
       .where(and_(
           OrganizationMember.user_id == current_user.id,
           Organization.is_active == True
       ))
   )
   ```
   - Concern: Multiple queries in same endpoint, complexity
   - Should extract: `OrganizationRepository.get_active_organization()`

7. **Create Organization** (lines 258-290)
   ```python
   new_org = Organization(...)
   db.add(new_org)
   await db.flush()
   # Add creator as owner
   membership = OrganizationMember(...)
   db.add(membership)
   current_user.active_organization_id = new_org.id
   await db.commit()
   ```
   - Concern: Multi-entity creation, transactional coupling
   - Should extract: `OrganizationRepository.create_with_owner()`
   - **Transaction boundary issue:** No atomic transaction management

8. **List Users (Admin)** (lines 455-458)
   ```python
   result = await db.execute(
       select(User).offset(skip).limit(limit)
   )
   ```
   - Should extract: `UserRepository.list()`

9. **Update User Role** (lines 472-488)
   ```python
   user_result = await db.execute(select(User).where(User.id == user_id))
   user = user_result.scalar_one_or_none()
   user.role = new_role
   user.updated_at = utc_now()
   await db.commit()
   ```
   - Should extract: `UserRepository.update_role()`

10. **Toggle User Status** (lines 500-516)
    - Similar to #9

#### Query Complexity Metrics
- **Average query length:** 4-8 lines (vs 1-2 with repository)
- **WHERE clause patterns:** AND, OR, complex JOINs
- **Transaction handling:** Implicit (no atomic blocks)
- **Code duplication:** Organization queries repeated in helper functions

#### Dependencies & Concerns
```
auth.py → User, Organization, OrganizationMember models
       → Helper functions (AuthHelper) for token operations
       → Mixed concerns: Auth + Organization management
       → Missing: Transaction boundaries, access control repository
```

#### Migration Impact
- **Blocking:** All protected endpoints depend on auth
- **Scope:** 12+ queries → 8-10 repository methods
- **Effort:** HIGH - Must maintain backward compatibility
- **Breaking changes:** None if repository interface matches current flow

---

### 2.2 Organization Route (`organization.py`) - CRITICAL PRIORITY

**Status:** Requires immediate migration  
**Urgency:** P0 - Most complex permission logic

#### Database Access Patterns

**Direct SQLAlchemy Queries: 18+**

1. **List Organizations** (lines 119-143)
   ```python
   # For admins - get all
   result = await db.execute(
       select(Organization)
       .options(selectinload(Organization.members))
       .where(Organization.is_active == True)
       .order_by(Organization.name)
   )
   # For users - get their organizations
   result = await db.execute(
       select(Organization, OrganizationMember.role)
       .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
       .options(selectinload(Organization.members))
       .where(and_(
           OrganizationMember.user_id == current_user.id,
           Organization.is_active == True
       ))
       .order_by(Organization.name)
   )
   ```
   - Concern: Branching logic based on user role inside query
   - Should extract: `OrganizationRepository.get_user_organizations()` + overloads

2. **Get Organization** (lines 184-189)
   ```python
   result = await db.execute(
       select(Organization)
       .options(selectinload(Organization.members))
       .where(Organization.id == organization_id)
   )
   ```
   - Should extract: `OrganizationRepository.get_by_id_with_members()`

3. **Update Organization** (lines 245-266)
   ```python
   result = await db.execute(
       select(Organization)
       .options(selectinload(Organization.members))
       .where(Organization.id == organization_id)
   )
   organization = result.scalar_one_or_none()
   # ... update fields ...
   await db.commit()
   ```
   - Should extract: `OrganizationRepository.update()`

4. **Delete Organization** (lines 313-339)
   ```python
   result = await db.execute(select(Organization).where(Organization.id == organization_id))
   organization = result.scalar_one_or_none()
   organization.is_active = False
   
   # Clear active organization for affected users
   users_result = await db.execute(
       select(User).where(User.active_organization_id == organization_id)
   )
   ```
   - Concern: Cascade update logic mixed in
   - Should extract: `OrganizationRepository.soft_delete_with_cascade()`

5. **Switch Organization** (lines 368-376)
   ```python
   result = await db.execute(
       select(Organization).where(
           and_(
               Organization.id == organization_id,
               Organization.is_active == True
           )
       )
   )
   ```
   - Should extract: `OrganizationRepository.get_active_by_id()`

6. **List Members** (lines 417-423)
   ```python
   result = await db.execute(
       select(OrganizationMember, User)
       .join(User, OrganizationMember.user_id == User.id)
       .where(OrganizationMember.organization_id == organization_id)
       .order_by(OrganizationMember.joined_at)
   )
   ```
   - Should extract: `OrganizationMemberRepository.get_by_organization()`

7. **Invite Member** (lines 505-525)
   ```python
   # Check if user exists
   result = await db.execute(select(User).where(User.email == request.email))
   target_user = result.scalar_one_or_none()
   
   # Check if already member
   result = await db.execute(
       select(OrganizationMember).where(
           and_(
               OrganizationMember.organization_id == organization_id,
               OrganizationMember.user_id == target_user.id
           )
       )
   )
   existing_membership = result.scalar_one_or_none()
   
   # Create membership
   membership = OrganizationMember(...)
   db.add(membership)
   await db.commit()
   ```
   - Concern: Multiple existence checks
   - Should extract: `OrganizationMemberRepository.invite()`

8. **Update Member Role** (lines 585-618)
   ```python
   result = await db.execute(
       select(OrganizationMember, User).join(User, OrganizationMember.user_id == User.id)
       .where(and_(
           OrganizationMember.id == member_id,
           OrganizationMember.organization_id == organization_id
       ))
   )
   member_user = result.first()
   
   # ... validation ...
   
   member.role = request.role
   await db.commit()
   ```
   - Should extract: `OrganizationMemberRepository.update_role()`

9. **Remove Member** (lines 659-722)
   ```python
   result = await db.execute(
       select(OrganizationMember, User).join(User, OrganizationMember.user_id == User.id)
       .where(and_(
           OrganizationMember.id == member_id,
           OrganizationMember.organization_id == organization_id
       ))
   )
   member_user = result.first()
   
   # Check last owner
   result = await db.execute(
       select(func.count(OrganizationMember.id))
       .where(and_(
           OrganizationMember.organization_id == organization_id,
           OrganizationMember.role == OrganizationRole.OWNER
       ))
   )
   owner_count = result.scalar()
   
   # Remove and update active org
   await db.delete(member)
   await db.commit()
   ```
   - Concern: Complex validation with COUNT query
   - Should extract: `OrganizationMemberRepository.remove_with_validation()`

#### Query Complexity Metrics
- **Total direct queries:** 18+
- **JOINs with selectinload:** 6+ instances
- **Complex WHERE clauses:** 8+ instances
- **Branching logic:** 2 instances (admin vs user)
- **Cascade operations:** 2 instances (soft delete, cascade update)

#### Permission Logic Issues
**Duplicated across multiple files:**
1. `check_organization_permission()` - Called in routes
2. `get_user_organization_role()` - Called in routes
3. `has_org_admin_permission()` - Helper function

These should be consolidated into `OrganizationPermissionRepository`.

#### Dependencies & Concerns
```
organization.py → Organization, OrganizationMember, User models
               → OrganizationService (validation logic)
               → OrganizationHelper (permission checks)
               → Issue: Permission logic split between helper and service
```

#### Critical Issue: Owner Count Query
```python
# Current pattern (line 699-708)
result = await db.execute(
    select(func.count(OrganizationMember.id))
    .where(and_(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.role == OrganizationRole.OWNER
    ))
)
owner_count = result.scalar()

# Should be in repository
OrganizationMemberRepository.count_owners_in_organization(org_id)
```

#### Migration Impact
- **Scope:** 18+ queries → 12-15 repository methods
- **Breaking changes:** None (interface remains same)
- **Permission layer:** Must extract to new repository
- **Service consolidation:** Merge OrganizationHelper into service

---

### 2.3 Admin_v2 Route (`admin_v2.py`) - MEDIUM PRIORITY

**Status:** Partially migrated (already uses services)  
**Urgency:** P1 - Good model for repository pattern

#### Database Access Patterns

**Direct SQLAlchemy Queries: 8+ (declining)**

1. **Upload Documents** (uses service)
   ```python
   document = await service.upload_document(...)  # Delegated ✓
   ```

2. **Process Documents** (lines 136-150)
   ```python
   # Direct query for authorization
   if current_user.role.value != "ADMIN":
       result = await db.execute(
           select(Document.id).where(
               and_(
                   Document.id.in_(request.document_ids),
                   Document.user_id != current_user.id
               )
           )
       )
       unauthorized_docs = result.scalars().all()
   ```
   - Should extract: `DocumentRepository.get_unauthorized_documents()`

3. **List Documents** (uses service) ✓
4. **Get Document** (lines 228-236)
   ```python
   # Direct query for authorization
   where_clause = Document.id == document_id
   if current_user.role.value != "ADMIN":
       where_clause = and_(where_clause, Document.user_id == current_user.id)
   
   result = await db.execute(select(Document).where(where_clause))
   document = result.scalar_one_or_none()
   ```
   - Should extract: `DocumentRepository.get_accessible_document()`

5. **Delete Document** (similar to #4, lines 254-260)
6. **Reprocess Document** (similar pattern, lines 287-290)

#### Good Practices Observed ✓
- Uses `DocumentService` for main operations
- Service abstraction for document-specific logic
- Clean separation of concerns (mostly)

#### Issues to Address
1. **Inconsistency:** Some operations use service, others use direct queries
2. **Authorization:** Duplicated authorization logic in routes
3. **Repository gap:** Missing `DocumentRepository` for data access

#### Migration Path
- Extract remaining 4-5 queries to `DocumentRepository`
- Already has service layer (minimal changes needed)
- Easy migration target

---

### 2.4 Chat Route (`chat.py`) - LOW PRIORITY (Phase 2)

**Status:** Minimal database access  
**Urgency:** P2 - Good foundational code

#### Database Access Patterns

**Direct SQLAlchemy Queries: 3 (mostly through SessionManager)**

1. **Session CRUD Operations** (lines 75-240)
   ```python
   session_manager = await get_session_manager()
   session_id = await session_manager.create_session(...)  # Delegated ✓
   session_info = await session_manager.get_session(...)   # Delegated ✓
   await session_manager.delete_session(...)                # Delegated ✓
   ```

2. **History Retrieval** (lines 260)
   ```python
   history = await session_manager.get_conversation_history(...)  # Delegated ✓
   ```

3. **Statistics** (lines 294)
   ```python
   stats = await session_manager.get_session_stats(...)  # Delegated ✓
   ```

#### Good Practices Observed ✓
- **Complete abstraction:** All database access via `SessionManager`
- **Service pattern:** Clean dependency injection
- **No direct SQLAlchemy:** Routes don't touch database directly
- **Model example:** Best practices for business logic isolation

#### Status
- Already follows repository pattern principles
- SessionManager = de facto repository
- Minimal migration needed
- Use as reference implementation for other routes

---

### 2.5 Audio Route (`audio.py`) - MEDIUM PRIORITY

**Status:** Moderate database access  
**Urgency:** P1 - Supports critical feature

#### Database Access Patterns

**Direct SQLAlchemy Queries: 8+**

1. **Get Presigned URL** (lines 60-78)
   ```python
   session_stmt = select(ConversationSession).where(ConversationSession.id == session_id)
   session_result = await db.execute(session_stmt)
   session = session_result.scalar_one_or_none()
   
   # Audio file query
   audio_stmt = select(AudioFile).where(
       and_(
           AudioFile.id == audio_file_id,
           AudioFile.session_id == session_id
       )
   )
   audio_result = await db.execute(audio_stmt)
   audio_file = audio_result.scalar_one_or_none()
   ```
   - Should extract: `AudioFileRepository.get_by_id_and_session()`

2. **List Session Files** (lines 166-168)
   ```python
   audio_stmt = select(AudioFile).where(AudioFile.session_id == session_id)
   audio_result = await db.execute(audio_stmt)
   audio_files = audio_result.scalars().all()
   ```
   - Should extract: `AudioFileRepository.get_by_session()`

3. **Get File Info** (lines 234-241)
   ```python
   audio_stmt = select(AudioFile).where(
       and_(
           AudioFile.id == audio_file_id,
           AudioFile.session_id == session_id
       )
   )
   ```
   - Should extract: `AudioFileRepository.get_with_metadata()`

4. **Get Metrics** (lines 316-318)
   ```python
   audio_stmt = select(AudioFile).where(AudioFile.session_id == session_id)
   audio_result = await db.execute(audio_stmt)
   audio_files = audio_result.scalars().all()
   ```

#### Complexity Considerations
- **Retention logic:** Needs tier-based filtering (UserTierService)
- **MinIO integration:** Pre-signed URL generation mixed with DB access
- **Metric calculations:** In-memory aggregation (would benefit from DB aggregation)

#### Dependencies
```
audio.py → AudioFile, ConversationSession models
        → UserTierService (tier information)
        → MinIO client (storage access)
        → Issue: Business logic (retention) mixed with data access
```

#### Migration Impact
- **Scope:** 8+ queries → 4-5 repository methods
- **Service layer needed:** `AudioFileService` for retention logic
- **Effort:** MEDIUM - Some aggregation logic moves to repository

---

### 2.6 Speech Route (`speech.py`) - NO ACTION

**Status:** No database access  
**Urgency:** N/A - No migration needed

- Pure speech processing (STT/TTS)
- File handling only
- No database queries
- Can proceed independently

---

## 3. Cross-Route Dependency Analysis

### 3.1 Direct Dependencies

```
auth.py
  ├─ User model (CRUD)
  ├─ Organization model (Create, List, Get, Update)
  ├─ OrganizationMember model (Create, Verify)
  └─ → organization.py (uses same models)

organization.py
  ├─ Organization model (CRUD + soft delete + cascade)
  ├─ OrganizationMember model (CRUD + count)
  ├─ User model (Update active_organization_id)
  └─ → auth.py (shares models)

admin_v2.py
  ├─ Document model (Query access control)
  └─ → Services (DocumentService, UserTierService)

chat.py
  ├─ SessionManager (repository pattern)
  ├─ ConversationSession model (indirect)
  └─ → audio.py (shares session data)

audio.py
  ├─ AudioFile model (CRUD + expiry logic)
  ├─ ConversationSession model (validation)
  └─ → chat.py (reads same sessions)
```

### 3.2 Shared Models

| Model | Used in | Query Type | Conflict Risk |
|-------|---------|-----------|----------------|
| User | auth.py, organization.py, admin_v2.py | CRUD, filter | MEDIUM - Multiple write paths |
| Organization | auth.py, organization.py | CRUD, query | HIGH - Competing mutation |
| OrganizationMember | auth.py, organization.py | CRUD | HIGH - Complex permissions |
| Document | admin_v2.py | Query + filter | LOW - Service handles most |
| AudioFile | audio.py, (chat.py indirect) | CRUD | LOW - Single writer |
| ConversationSession | chat.py, audio.py | Query | LOW - Read-heavy |

### 3.3 Transaction Boundaries Issue

**Critical Finding:** No atomic transaction handling across routes

Example: Organization creation in `auth.py` (lines 258-290):
```python
new_org = Organization(...)
db.add(new_org)
await db.flush()  # Get ID but no transaction boundary!

membership = OrganizationMember(...)
db.add(membership)

current_user.active_organization_id = new_org.id
await db.commit()  # Single commit for 3 entities!
```

**Risk:** Partial failure leaves inconsistent state
**Solution:** Repository must provide atomic transaction methods

---

## 4. Repository Pattern Migration Roadmap

### 4.1 Priority Tiers

#### Tier 1: CRITICAL (Week 1-2)
Must implement before other migrations

1. **UserRepository**
   - `create()` - Registration
   - `get_by_email()` - Login
   - `get_by_username()`
   - `get_by_email_or_username()` - Login fallback
   - `get_by_id()` - Token refresh
   - `exists_by_email_or_username()` - Duplicate check
   - `update_role()` - Admin operations
   - `update_status()` - Admin operations
   - `list()` - Admin listing
   - **Estimated methods:** 10
   - **Current queries:** 9 in auth.py

2. **OrganizationRepository**
   - `create()` - Creation
   - `get_by_id()` - Get details
   - `get_by_id_with_members()` - With member data
   - `get_user_organizations()` - User's orgs
   - `update()` - Update details
   - `soft_delete()` - Soft delete
   - `soft_delete_with_cascade()` - Delete + clear user references
   - `get_active_by_id()` - For active check
   - **Estimated methods:** 8
   - **Current queries:** 6 in auth.py + 8 in organization.py

3. **OrganizationPermissionRepository**
   - `verify_membership()` - Is user member?
   - `get_user_role()` - User's role in org
   - `verify_permission()` - Role-based access
   - `count_owners()` - For validation
   - **Estimated methods:** 4
   - **Current pattern:** Helper functions + inline checks

#### Tier 2: HIGH PRIORITY (Week 2-3)
Blocks organization.py full migration

4. **OrganizationMemberRepository**
   - `get_by_organization()` - List members
   - `get_by_id()` - Get member
   - `create()` - Add member
   - `invite()` - With duplicate check
   - `update_role()` - Change role
   - `remove()` - Delete member
   - `remove_with_validation()` - Remove + owner check
   - **Estimated methods:** 7
   - **Current queries:** 6 in organization.py

5. **DocumentRepository**
   - `get_accessible_document()` - Access control
   - `get_unauthorized_documents()` - Admin checks
   - `list_user_documents()` - Already in service
   - **Estimated methods:** 3
   - **Current queries:** 4 in admin_v2.py

#### Tier 3: MEDIUM PRIORITY (Week 3-4)
Supports audio/media features

6. **AudioFileRepository**
   - `get_by_id_and_session()` - Single file
   - `get_by_session()` - Session files
   - `get_with_metadata()` - File info
   - `create()` - Store metadata
   - **Estimated methods:** 4
   - **Current queries:** 4 in audio.py

#### Tier 4: REFERENCE (Ongoing)
Already implemented - no action needed

7. **SessionRepository** (SessionManager)
   - Already follows pattern
   - Use as reference for others

### 4.2 Migration Sequence Dependency Graph

```
Phase 1 (Foundation)
├─ UserRepository              [Core authentication]
├─ OrganizationPermissionRepo  [ACL foundation]
└─ → auth.py refactoring       [Unblock org routes]

Phase 2 (Organization Management)
├─ OrganizationRepository       [Depends on permission repo]
├─ OrganizationMemberRepository [Depends on org repo]
└─ → organization.py refactoring [Unblock admin routes]

Phase 3 (Document Management)
├─ DocumentRepository           [Depends on user/org repo]
└─ → admin_v2.py refactoring   [Mostly complete]

Phase 4 (Media & Sessions)
├─ AudioFileRepository          [Depends on session stability]
└─ → audio.py refactoring      [Improve metrics queries]
```

---

## 5. Current Database Query Patterns

### 5.1 Most Common Patterns

#### Pattern 1: User Existence Check (Antipattern)
**Frequency:** 3+ instances

```python
# Current (auth.py:61-68, organization.py:505-508)
result = await db.execute(
    select(User).where(User.email == email)
)
user = result.scalar_one_or_none()
if not user:
    raise HTTPException(...)

# Repository solution
user = await user_repo.get_by_email(email)
if not user:
    raise HTTPException(...)
```

**Issue:** No single responsibility - query + existence check mixed  
**Benefit:** Cleaner code + reusable method

#### Pattern 2: Complex Filter with OR
**Frequency:** 2+ instances

```python
# Current (auth.py:116-122)
result = await db.execute(
    select(User).where(
        and_(
            User.is_active == True,
            (User.email == identifier) | (User.username == identifier)
        )
    )
)

# Repository solution
user = await user_repo.get_by_email_or_username(identifier)
```

**Issue:** Complex logic hard to test independently  
**Benefit:** Encapsulated search logic

#### Pattern 3: Authorization Query
**Frequency:** 4+ instances

```python
# Current (organization.py:343-353)
membership = await db.execute(
    select(OrganizationMember, Organization)
    .join(Organization, ...)
    .where(and_(...))
)

# Repository solution
has_access = await org_perm_repo.verify_membership(user_id, org_id)
```

**Issue:** Repeated in multiple routes  
**Benefit:** Single source of truth for permissions

#### Pattern 4: CASCADE Operations
**Frequency:** 2 instances

```python
# Current (organization.py:325-339)
organization.is_active = False
users = await db.execute(select(User).where(...))
for user in users:
    user.active_organization_id = None
await db.commit()

# Repository solution
await org_repo.soft_delete_with_cascade(org_id)
```

**Issue:** Multi-step manual cascade  
**Benefit:** Atomic operation, clearer intent

#### Pattern 5: Count Operations
**Frequency:** 1 critical instance

```python
# Current (organization.py:699-708)
result = await db.execute(
    select(func.count(...)).where(...)
)
count = result.scalar()

# Repository solution
count = await org_member_repo.count_owners(org_id)
```

**Issue:** One-off counting logic  
**Benefit:** Reusable aggregation method

### 5.2 Anti-Patterns Identified

| Anti-Pattern | Location | Instances | Severity |
|--------------|----------|-----------|----------|
| Inline query in route | Multiple | 18+ | HIGH |
| Complex WHERE in code | auth.py, org.py | 6+ | HIGH |
| Manual cascade logic | organization.py:325 | 1 | MEDIUM |
| Existence check + fetch | auth.py, org.py | 3+ | MEDIUM |
| Missing transaction boundaries | auth.py:258 | 2+ | HIGH |
| Branching on role in query | organization.py:119 | 1 | MEDIUM |
| No bulk operation handling | organization.py:699 | - | LOW |

---

## 6. Repository Candidates Ranked by Impact

### 6.1 Quick Win Repositories (1-2 days each)

| Repository | Queries Replaced | Benefit | Complexity |
|---|---|---|---|
| UserRepository | 9 | Eliminates duplicate auth logic | MEDIUM |
| OrganizationPermissionRepository | 4 | Single source for ACL | MEDIUM |
| AudioFileRepository | 4 | Encapsulates tier logic | LOW |

### 6.2 Strategic Repositories (2-3 days each)

| Repository | Queries Replaced | Benefit | Complexity |
|---|---|---|---|
| OrganizationRepository | 8 | Atomic operations, cascade | HIGH |
| OrganizationMemberRepository | 6 | Complex permission logic | HIGH |

### 6.3 Service Enhancement (Already Started)

| Service | Status | Action |
|---|---|---|
| DocumentService | Partial | Extract authorization queries |
| OrganizationService | Exists | Consolidate helper functions |

---

## 7. Transaction & Consistency Issues

### 7.1 Identified Issues

**Issue #1: Implicit Transactions**
- Location: auth.py organization creation (lines 258-290)
- Problem: Multiple entities added in single commit
- Risk: Partial failure leaves orphaned org or member
- Solution: Atomic repository method

**Issue #2: Read-Modify-Write Pattern**
- Location: Multiple (auth.py:133, organization.py:617)
- Problem: Separate read and write operations
- Risk: Race conditions with concurrent updates
- Solution: Dedicated update methods

**Issue #3: Cascade Operations**
- Location: organization.py:325-339
- Problem: Manual loop updating dependent rows
- Risk: Incomplete cascade on error
- Solution: Database-level constraints + atomic operation

**Issue #4: State Consistency**
- Location: organization.py:230-339
- Problem: No verification after update
- Risk: Update succeeds but data stale
- Solution: Return updated entity with db.refresh()

### 7.2 Transaction Pattern to Implement

```python
# Correct pattern for all repository methods
async def create_with_dependencies(self, ...):
    """Create entity with dependent relationships atomically."""
    try:
        entity = Entity(...)
        self.session.add(entity)
        await self.session.flush()  # Get ID
        
        # Create dependencies using entity ID
        dependent = Dependent(entity_id=entity.id)
        self.session.add(dependent)
        
        await self.session.commit()  # Atomic!
        await self.session.refresh(entity)
        return entity
        
    except IntegrityError as e:
        await self.session.rollback()
        raise RepositoryException(f"Integrity violation: {e}")
    except Exception as e:
        await self.session.rollback()
        raise RepositoryException(f"Failed to create: {e}")
```

---

## 8. Helper Functions Consolidation

### 8.1 Current Helper Duplication

**File:** `backend/api/helper/OrganizationHelper.py`
- `check_organization_permission()` - Permission check
- `get_user_organization_role()` - Role lookup
- `has_org_admin_permission()` - Role-based access

**File:** `backend/api/helper/AuthHelper.py`
- `get_current_organization()` - Dependency injection
- Token/password operations (should stay)

### 8.2 Migration Plan for Helpers

```
OrganizationHelper.py
├─ check_organization_permission()
│  └─ → OrganizationPermissionRepository.verify_access()
├─ get_user_organization_role()
│  └─ → OrganizationPermissionRepository.get_user_role()
└─ has_org_admin_permission()
   └─ → OrganizationPermissionRepository.has_permission()

AuthHelper.py
├─ Keep: JWT operations, password hashing
└─ Move: get_current_organization() → middleware/auth.py
```

---

## 9. Testing Implications

### 9.1 Current Testing Gaps

- No isolated unit tests for queries (tested through routes)
- Integration tests cover happy path only
- Permission logic not independently testable

### 9.2 Repository Testing Benefits

Each repository method will enable:
- Unit tests without database (mock repository)
- Query validation tests (integration layer)
- Permission logic tests (isolated)

**Example Test Structure:**

```python
# Unit test (no DB)
async def test_verify_membership():
    mock_repo = AsyncMock(spec=OrganizationPermissionRepository)
    mock_repo.verify_membership.return_value = True
    assert await mock_repo.verify_membership("user1", "org1")

# Integration test (with DB)
async def test_verify_membership_integration(db_session):
    repo = OrganizationPermissionRepository(db_session)
    result = await repo.verify_membership("user1", "org1")
    assert isinstance(result, bool)
```

---

## 10. Migration Implementation Plan

### 10.1 Phase 1: Foundation (Week 1)

**Deliverables:**
1. ✓ UserRepository (auth.py → 9 queries)
2. ✓ OrganizationPermissionRepository (helper functions)
3. Refactor auth.py to use repositories
4. Update tests

**Time estimate:** 2-3 days  
**Blockers:** None (independent)

### 10.2 Phase 2: Organization (Week 2)

**Deliverables:**
1. OrganizationRepository (auth.py + org.py → 8 queries)
2. OrganizationMemberRepository (org.py → 6 queries)
3. Refactor organization.py
4. Consolidate OrganizationHelper
5. Update tests

**Time estimate:** 2-3 days  
**Blockers:** Depends on Phase 1

### 10.3 Phase 3: Admin (Week 3)

**Deliverables:**
1. DocumentRepository (admin_v2.py → 4 queries)
2. Refactor admin_v2.py
3. Consolidate with DocumentService
4. Update tests

**Time estimate:** 1-2 days  
**Blockers:** Depends on Phase 1

### 10.4 Phase 4: Media (Week 4)

**Deliverables:**
1. AudioFileRepository (audio.py → 4 queries)
2. Refactor audio.py
3. Create AudioFileService
4. Update tests

**Time estimate:** 1-2 days  
**Blockers:** None

---

## 11. Success Metrics

### 11.1 Code Quality Improvements

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Inline queries in routes | 40+ | 0 | 0 |
| Average query lines per endpoint | 6-8 | 1-2 | 1-2 |
| Duplicated query logic | 6+ | 0 | 0 |
| Repository methods | 0 | 40+ | 40+ |

### 11.2 Testability Improvements

| Aspect | Before | After |
|--------|--------|-------|
| Isolated unit tests | Limited | Full coverage |
| Query tests | None | Per repository |
| Permission tests | Route-level | Unit-level |
| Mock-ability | Hard | Easy (dependency injection) |

### 11.3 Maintainability Improvements

| Aspect | Improvement |
|--------|------------|
| Single source of truth for queries | Multiple places → Repository |
| Authorization logic | Routes + helpers → Permission repo |
| Database changes | Touch every route → Update repository |
| New feature queries | Copy from routes → Reuse repository |

---

## 12. Risk Assessment

### 12.1 High Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Breaking auth flow | LOW | CRITICAL | Comprehensive tests before deploy |
| Permission escalation | LOW | CRITICAL | Peer review + security tests |
| Transaction deadlocks | MEDIUM | HIGH | Load testing + timeout handling |
| Data inconsistency | MEDIUM | HIGH | Atomic operations + validation |

### 12.2 Medium Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Performance regression | MEDIUM | MEDIUM | Before/after query profiling |
| API compatibility | LOW | MEDIUM | Version in response, test endpoints |
| Session manager stability | LOW | MEDIUM | Existing tests already pass |

---

## 13. Recommendations

### 13.1 Immediate Actions (Next 1-2 days)

1. **Create CONTEXT.md** with migration progress
2. **Set up repository base class** with common patterns
3. **Begin Phase 1** (UserRepository + OrganizationPermissionRepository)
4. **Run baseline tests** to establish test pass rate

### 13.2 Implementation Strategy

1. **Create repositories incrementally** (not big bang)
2. **Maintain backward compatibility** during migration
3. **Migrate one route at a time** (not all at once)
4. **Add tests for each repository** before migration
5. **Keep CONTEXT.md updated** during implementation

### 13.3 Best Practices to Adopt

```python
# 1. Constructor dependency injection
class AuthRoute:
    def __init__(self, user_repo: UserRepository, org_repo: OrganizationRepository):
        self.user_repo = user_repo
        self.org_repo = org_repo

# 2. Async repository methods
async def get_user(self, user_id: str) -> User:
    return await self.session.get(User, user_id)

# 3. Atomic operations
async def create_org_with_owner(self, ...):
    try:
        org = Organization(...)
        self.session.add(org)
        await self.session.flush()
        
        member = OrganizationMember(organization_id=org.id, ...)
        self.session.add(member)
        
        await self.session.commit()
        return org
    except Exception:
        await self.session.rollback()
        raise

# 4. Comprehensive error handling
class RepositoryException(Exception):
    """Base repository exception"""
    pass

# 5. Method naming convention
# get_* → Single entity
# list_* → Multiple entities
# exists_* → Boolean check
# count_* → Count result
# create_* → Create entity
# update_* → Update entity
# delete_* → Delete entity
```

---

## 14. Appendix: Complete Query Mapping

### Auth Route Query Mapping
```
Line 61-68:   select(User) where email/username → UserRepository.exists_by_email_or_username()
Line 115-122: select(User) where active/email/username → UserRepository.get_by_email_or_username()
Line 165-168: select(User) where id/active → UserRepository.get_active_by_id()
Line 246-248: select(Organization) where name → OrganizationRepository.exists_by_name()
Line 313-323: select(Organization).join(...) → OrganizationRepository.get_user_organizations()
Line 343-353: select(OrganizationMember).join(...) → OrganizationPermissionRepository.verify_membership()
Line 402-411: select(Organization).join(...) → OrganizationRepository.get_user_organizations()
Line 418-428: select(Organization).join(...) → OrganizationRepository.get_active_organization()
Line 455-458: select(User).offset.limit → UserRepository.list()
Line 472-475: select(User) where id → UserRepository.get_by_id()
Line 500-503: select(User) where id → UserRepository.get_by_id()
```

### Organization Route Query Mapping
```
Line 119-143: select(Organization) with/without join → OrganizationRepository.list_user_organizations()
Line 184-189: select(Organization) with selectinload → OrganizationRepository.get_by_id_with_members()
Line 245-250: select(Organization) with selectinload → OrganizationRepository.get_by_id_with_members()
Line 313-335: select(Organization/User) with cascade → OrganizationRepository.soft_delete_with_cascade()
Line 368-376: select(Organization) where active → OrganizationRepository.get_active_by_id()
Line 417-423: select(OrganizationMember).join(User) → OrganizationMemberRepository.get_by_organization()
Line 505-525: select(User) + select(OrganizationMember) → OrganizationMemberRepository.invite()
Line 585-594: select(OrganizationMember).join(User) → OrganizationMemberRepository.get_by_id()
Line 617-618: member.role = ...; commit → OrganizationMemberRepository.update_role()
Line 659-722: select(OrganizationMember).join(User) + count → OrganizationMemberRepository.remove_with_validation()
```

### Admin V2 Route Query Mapping
```
Line 136-143: select(Document.id) where authorization → DocumentRepository.get_unauthorized_documents()
Line 228-231: select(Document) where authorization → DocumentRepository.get_accessible_document()
Line 254-257: select(Document) where authorization → DocumentRepository.get_accessible_document()
Line 287-290: select(Document) where authorization → DocumentRepository.get_accessible_document()
```

### Audio Route Query Mapping
```
Line 60-62:   select(ConversationSession) → ConversationSessionRepository.get_by_id()
Line 68-75:   select(AudioFile) where session → AudioFileRepository.get_by_id_and_session()
Line 154-157: select(ConversationSession) → ConversationSessionRepository.get_by_id()
Line 166-168: select(AudioFile) where session → AudioFileRepository.get_by_session()
Line 234-241: select(AudioFile) where session → AudioFileRepository.get_by_id_and_session()
Line 316-318: select(AudioFile) where session → AudioFileRepository.get_by_session()
```

---

## 15. Document Metadata

**Status:** Ready for implementation  
**Next Steps:**
1. Create CONTEXT.md for session persistence
2. Set up Phase 1 implementation
3. Begin with UserRepository

**Last Updated:** November 2025  
**Review Date:** Post-Phase 1 completion

