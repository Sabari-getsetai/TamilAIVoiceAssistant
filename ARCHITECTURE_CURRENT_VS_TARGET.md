# Architecture: Current vs Target State

## Current Architecture (Problematic)

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Routes Layer                        │
├──────────────────────────────────────────────────────────────────┤
│  auth.py  │ chat.py  │ speech.py  │ organization.py  │ admin_v2.py
└─────┬──────────────────────────────────────────────────────────┬─┘
      │ Direct Imports (PROBLEM: Tight Coupling)                 │
      ↓                                                           ↓
┌──────────────────────────────────────────────────────────────────┐
│              Helpers Layer (api/helper/)                          │
├──────────────────────────────────────────────────────────────────┤
│ AuthHelper        ChatHelper      DocumentHelper                 │
│ (JWT, password)   (file ops)      (background tasks)            │
│                                                                  │
│ OrganizationHelper    SpeechHelper                              │
│ (permissions)         (audio validation)                        │
└──────┬──────────────────────────────────────────────┬──────────┘
       │                                              │
       ↓                                              ↓
┌──────────────────────────────────────────────────────────────────┐
│              Services Layer (backend/services/)                   │
├──────────────────────────────────────────────────────────────────┤
│ document_service.py   organization_service.py                    │
│ session_service.py    email_service.py                           │
│ tier_service.py                                                  │
│                                                                  │
│ auth/ (EMPTY)         media/ (EMPTY)                            │
│ documents/ (EMPTY)    conversation/ (EMPTY)                     │
│ organization/ (EMPTY) infrastructure/ (EMPTY)                   │
└──────┬─────────────────────────────────────────────┬────────────┘
       │                                             │
       ↓                                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                  Database & Infrastructure                        │
├──────────────────────────────────────────────────────────────────┤
│ PostgreSQL │ Redis │ MinIO │ Ollama │ External APIs             │
└──────────────────────────────────────────────────────────────────┘

PROBLEMS:
========
1. Routes import from helpers (api/ folder)
2. Helpers import from services (correct) BUT split concerns
3. Services directory incomplete and underutilized
4. Permission/auth checks scattered in multiple places
5. No clear dependency flow
6. Violates dependency inversion principle
```

## Target Architecture (Clean)

```
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Routes Layer                         │
├───────────────────────────────────────────────────────────────────┤
│  auth.py  │ chat.py  │ speech.py  │ organization.py  │ admin_v2.py
└─────┬──────────────────────────────────────────────────────┬─────┘
      │ Clean Imports (Dependency Inversion)               │
      ↓                                                     ↓
┌──────────────────────────────────────────────────────────────────┐
│              Services Layer (backend/services/)                   │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │  auth/              │    │  media/             │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ • auth_service      │    │ • audio_service     │             │
│  │ • authorization     │    │   - validate        │             │
│  │   - JWT tokens      │    │   - save            │             │
│  │   - password ops    │    │   - cleanup         │             │
│  │   - current_user    │    │                     │             │
│  │   - org access      │    │                     │             │
│  └─────────────────────┘    └─────────────────────┘             │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │  organization/      │    │  documents/         │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ • org_service       │    │ • document_service  │             │
│  │ • permission_svc    │    │ • document_tasks    │             │
│  │ • tier_service      │    │   - process bg task │             │
│  │   - roles/perms     │    │   - document status │             │
│  │   - org limits      │    │                     │             │
│  └─────────────────────┘    └─────────────────────┘             │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │  conversation/      │    │  infrastructure/    │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ • session_svc       │    │ • email_service     │             │
│  │ • turn_svc          │    │ • storage_service   │             │
│  │   - session mgmt    │    │ • cache_service     │             │
│  │   - turn history    │    │ • health_service    │             │
│  └─────────────────────┘    └─────────────────────┘             │
└──────┬──────────────────────────────────────────────────────┬───┘
       │ Imports (Clean dependencies)                        │
       ↓                                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                  Database & Infrastructure                        │
├──────────────────────────────────────────────────────────────────┤
│ PostgreSQL │ Redis │ MinIO │ Ollama │ External APIs             │
└──────────────────────────────────────────────────────────────────┘

BENEFITS:
========
1. Routes import only from services/
2. Each service module is self-contained
3. Clear dependencies and module boundaries
4. No helpers layer (anti-pattern eliminated)
5. Follows dependency inversion principle
6. Microservice-ready architecture
7. Easy to test and refactor
```

## Module Dependency Flow (Target)

```
ROUTES LAYER
    ↓ (imports)
SERVICES: auth/              → AuthenticationService, AuthorizationService
         ├─ media/           → AudioService
         ├─ organization/    → OrgPermissionService, OrgService, TierService
         ├─ documents/       → DocumentService, DocumentTaskService
         ├─ conversation/    → SessionService (DatabaseSessionManager)
         └─ infrastructure/  → EmailService, StorageService, CacheService

INTERNAL SERVICE DEPENDENCIES
    auth/ ────────→ auth/authorization → uses auth/authentication
    organization/ → organization/permission → uses auth/authorization
    documents/   → documents/task → uses documents/document_service
    conversation/ → session_service (exists at root, may move to conversation/)

DATABASE LAYER
    ↑ (queries)
    │ (from all services)
```

## Service Module Responsibilities

### auth/
- **AuthenticationService**: JWT token handling, password hashing
  - `hash_password()`, `verify_password()`
  - `create_access_token()`, `create_refresh_token()`
  - `verify_token()`
  
- **AuthorizationService**: User/org dependency injection
  - `get_current_user()` - FastAPI dependency
  - `get_current_user_optional()`
  - `get_current_admin_user()`
  - `get_current_organization()` - org access check
  - `get_current_organization_admin()`
  - `get_user_organizations()`

### media/
- **AudioService**: Audio file operations
  - `validate_audio_file()` - unified validation
  - `save_audio_file()` - for processed audio
  - `save_temp_audio_file()` - for temporary storage
  - `cleanup_old_audio_files()` - maintenance

### organization/
- **OrganizationService**: Org creation/management (existing)
- **OrganizationPermissionService**: Role-based access
  - `get_user_organization_role()`
  - `check_organization_permission()`
  - `has_org_admin_permission()`
- **UserTierService**: Tier-based features (existing)

### documents/
- **DocumentService**: Document lifecycle (existing)
- **DocumentTaskService**: Background processing
  - `process_documents_background()`

### conversation/
- **DatabaseSessionManager**: Session persistence (move here)
- **ConversationTurnService**: Turn management (future)
- **ConversationService**: High-level orchestration (future)

### infrastructure/
- **EmailService**: Notifications (existing)
- **StorageService**: MinIO abstraction (future)
- **CacheService**: Redis operations (future)
- **HealthService**: Infrastructure monitoring (future)

## Import Examples

### Before (Current - Routes importing from helpers)
```python
# backend/api/routes/auth.py
from backend.api.helper.AuthHelper import (
    hash_password,
    verify_password,
    get_current_user,
    get_current_organization
)

# backend/api/routes/chat.py
from backend.api.helper.ChatHelper import (
    validate_audio_file,
    save_audio_file,
    cleanup_old_audio_files,
)

# backend/api/routes/organization.py
from backend.api.helper.OrganizationHelper import (
    check_organization_permission,
    get_user_organization_role,
)
```

### After (Target - Routes importing from services)
```python
# backend/api/routes/auth.py
from backend.services.auth.authentication_service import AuthenticationService
from backend.services.auth.authorization_service import AuthorizationService

@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Use service directly
    password_ok = AuthenticationService.verify_password(
        request.password, user.password_hash
    )
    token = AuthenticationService.create_access_token(user.id)
    return {"access_token": token}

@router.get("/me")
async def get_me(
    current_user: User = Depends(AuthorizationService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return current_user

# backend/api/routes/chat.py
from backend.services.media.audio_service import AudioService

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    is_valid, error = AudioService.validate_audio_file(
        file.filename, file.size
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    path = await AudioService.save_audio_file(file)
    return {"path": str(path)}

# backend/api/routes/organization.py
from backend.services.organization.permission_service import OrganizationPermissionService

@router.get("/{org_id}/members")
async def get_members(
    org_id: str,
    current_user: User = Depends(AuthorizationService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Use service for permission check
    has_access = await OrganizationPermissionService.check_organization_permission(
        db, current_user, org_id
    )
    if not has_access:
        raise HTTPException(status_code=403)
    # ... get members
```

## Migration Path (Visual)

```
WEEK 1: Phase 1 - Create Services
├─ auth/authentication_service.py (JWT, passwords)
├─ auth/authorization_service.py (dependencies)
├─ media/audio_service.py (audio operations)
├─ organization/permission_service.py (org roles)
└─ documents/document_task_service.py (background tasks)

WEEK 2: Phase 2 - Module Exports
├─ Update auth/__init__.py
├─ Update media/__init__.py
├─ Update organization/__init__.py
└─ Update documents/__init__.py

WEEK 3: Phase 3 - Compatibility Bridge
└─ Create api/helper/compatibility.py (re-exports from services)

WEEK 4: Phase 4 & 5 - Route Migration & Deprecation
├─ Update auth.py, auth_migrated.py (routes)
├─ Update chat.py, speech.py (routes)
├─ Update organization.py (routes)
├─ Update admin_v2.py (routes)
├─ Run full test suite
├─ Mark helpers as deprecated
└─ Schedule deletion in future sprint

WEEK 5+: Cleanup
├─ Monitor for issues
├─ Document in CLAUDE.md
└─ Delete helpers in next sprint
```

## Testing Strategy

### Unit Tests (New)
```
tests/unit/services/auth/
├─ test_authentication_service.py
└─ test_authorization_service.py

tests/unit/services/media/
├─ test_audio_service.py

tests/unit/services/organization/
├─ test_permission_service.py

tests/unit/services/documents/
└─ test_document_task_service.py
```

### Integration Tests (Existing)
```
tests/integration/
├─ test_auth_routes.py (should still pass)
├─ test_chat_routes.py (should still pass)
├─ test_organization_routes.py (should still pass)
└─ test_admin_routes.py (should still pass)
```

### Compatibility Tests (During Migration)
- Test old imports (deprecated) still work
- Test new imports work correctly
- Test both import paths side-by-side

---

**Document Version:** 1.0
**Date:** November 2025
**Status:** Ready for Implementation
