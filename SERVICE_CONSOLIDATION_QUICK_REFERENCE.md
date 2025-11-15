# Service Consolidation Quick Reference

## What to Move Where - Quick Table

| Helper Function | Current Location | New Location | New Class | Priority |
|---|---|---|---|---|
| `hash_password()` | AuthHelper.py:23 | auth/authentication_service.py | AuthenticationService | HIGH |
| `verify_password()` | AuthHelper.py:29 | auth/authentication_service.py | AuthenticationService | HIGH |
| `create_access_token()` | AuthHelper.py:38 | auth/authentication_service.py | AuthenticationService | HIGH |
| `create_refresh_token()` | AuthHelper.py:54 | auth/authentication_service.py | AuthenticationService | HIGH |
| `verify_token()` | AuthHelper.py:71 | auth/authentication_service.py | AuthenticationService | HIGH |
| `get_current_user()` | AuthHelper.py:96 | auth/authorization_service.py | AuthorizationService | HIGH |
| `get_current_user_optional()` | AuthHelper.py:137 | auth/authorization_service.py | AuthorizationService | HIGH |
| `get_current_admin_user()` | AuthHelper.py:152 | auth/authorization_service.py | AuthorizationService | HIGH |
| `get_current_organization()` | AuthHelper.py:165 | auth/authorization_service.py | AuthorizationService | HIGH |
| `get_current_organization_admin()` | AuthHelper.py:218 | auth/authorization_service.py | AuthorizationService | HIGH |
| `get_user_organizations()` | AuthHelper.py:233 | auth/authorization_service.py | AuthorizationService | HIGH |
| `validate_audio_file()` | ChatHelper.py:18 | media/audio_service.py | AudioService | MEDIUM |
| `save_audio_file()` | ChatHelper.py:41 | media/audio_service.py | AudioService | MEDIUM |
| `cleanup_old_audio_files()` | ChatHelper.py:69 | media/audio_service.py | AudioService | MEDIUM |
| `validate_audio_file()` | SpeechHelper.py:15 | media/audio_service.py | AudioService | MEDIUM |
| `save_temp_audio_file()` | SpeechHelper.py:29 | media/audio_service.py | AudioService | MEDIUM |
| `get_user_organization_role()` | OrganizationHelper.py:12 | organization/permission_service.py | OrganizationPermissionService | MEDIUM |
| `check_organization_permission()` | OrganizationHelper.py:31 | organization/permission_service.py | OrganizationPermissionService | MEDIUM |
| `has_org_admin_permission()` | OrganizationHelper.py:54 | organization/permission_service.py | OrganizationPermissionService | MEDIUM |
| `process_documents_background()` | DocumentHelper.py:14 | documents/document_task_service.py | DocumentTaskService | MEDIUM |

## Files to Modify (Import Updates)

### Phase 4 Import Changes

| File | Current Imports | New Imports |
|------|---|---|
| `auth.py` | `from backend.api.helper.AuthHelper import ...` | `from backend.services.auth.authentication_service import AuthenticationService` + `from backend.services.auth.authorization_service import AuthorizationService` |
| `auth_migrated.py` | `from backend.api.helper.AuthHelper import ...` | Same as auth.py |
| `chat.py` | `from backend.api.helper.ChatHelper import ...` | `from backend.services.media.audio_service import AudioService` |
| `speech.py` | `from backend.api.helper.SpeechHelper import ...` | `from backend.services.media.audio_service import AudioService` |
| `organization.py` | `from backend.api.helper.OrganizationHelper import ...` | `from backend.services.organization.permission_service import OrganizationPermissionService` |
| `admin_v2.py` | `from backend.api.helper.DocumentHelper import ...` | `from backend.services.documents.document_task_service import DocumentTaskService` |

## New Files to Create

### 1. `backend/services/auth/authentication_service.py`
```python
"""JWT and password handling for authentication."""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, status
from backend.settings import settings


class AuthenticationService:
    """Handle JWT tokens and password operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token."""
        from uuid import uuid4
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "jti": str(uuid4())
        }
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[str]:
        """Verify JWT token and return user ID."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            token_type_claim: str = payload.get("type")
            
            if user_id is None or token_type_claim != token_type:
                return None
            return user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
```

### 2. `backend/services/auth/authorization_service.py`
```python
"""User and organization authorization services."""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.database import get_db
from backend.database.models import User, Organization, OrganizationMember, UserRole, OrganizationRole
from .authentication_service import AuthenticationService


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class AuthorizationService:
    """Handle user authorization and dependency injection."""
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current authenticated user from JWT token."""
        user_id = AuthenticationService.verify_token(credentials.credentials, "access")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    async def get_current_user_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if authenticated, None otherwise."""
        if not credentials:
            return None
        
        try:
            return await AuthorizationService.get_current_user(credentials, db)
        except HTTPException:
            return None
    
    @staticmethod
    async def get_current_admin_user(
        current_user: User = Depends(lambda: AuthorizationService.get_current_user)
    ) -> User:
        """Ensure current user has admin privileges."""
        if current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return current_user
    
    @staticmethod
    async def get_current_organization(
        current_user: User = Depends(lambda: AuthorizationService.get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> Organization:
        """Get current user's active organization and validate membership."""
        if not current_user.active_organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active organization. Please create or join an organization to access the app.",
                headers={"X-Auth-Error": "NO_ORGANIZATION"}
            )
        
        result = await db.execute(
            select(Organization, OrganizationMember)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                and_(
                    Organization.id == current_user.active_organization_id,
                    Organization.is_active == True,
                    OrganizationMember.user_id == current_user.id
                )
            )
        )
        
        org_membership = result.first()
        
        if not org_membership:
            current_user.active_organization_id = None
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization access has been revoked.",
                headers={"X-Auth-Error": "ORGANIZATION_ACCESS_REVOKED"}
            )
        
        organization, membership = org_membership
        organization._current_user_membership = membership
        return organization
    
    @staticmethod
    async def get_current_organization_admin(
        organization: Organization = Depends(lambda: AuthorizationService.get_current_organization)
    ) -> Organization:
        """Ensure current user has admin privileges in their organization."""
        membership = getattr(organization, '_current_user_membership', None)
        
        if not membership or membership.role not in [OrganizationRole.ADMIN, OrganizationRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization admin privileges required"
            )
        
        return organization
    
    @staticmethod
    async def get_user_organizations(
        current_user: User = Depends(lambda: AuthorizationService.get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> List[Organization]:
        """Get all organizations user is a member of."""
        result = await db.execute(
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(
                and_(
                    OrganizationMember.user_id == current_user.id,
                    Organization.is_active == True
                )
            )
            .order_by(Organization.name)
        )
        
        return list(result.scalars().all())
```

### 3. `backend/services/media/audio_service.py`
```python
"""Audio file handling and validation service."""
import shutil
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile
from backend.settings import settings


class AudioService:
    """Handle audio file operations."""
    
    ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
    MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_audio_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate uploaded audio file."""
        ext = Path(filename).suffix.lower()
        if ext not in AudioService.ALLOWED_EXTENSIONS:
            return False, f"Audio type '{ext}' not allowed. Allowed: {', '.join(AudioService.ALLOWED_EXTENSIONS)}"
        
        if file_size > AudioService.MAX_AUDIO_SIZE:
            return False, f"Audio file too large. Maximum size: {AudioService.MAX_AUDIO_SIZE / 1024 / 1024}MB"
        
        return True, None
    
    @staticmethod
    async def save_audio_file(file: UploadFile, prefix: str = "upload") -> Path:
        """Save uploaded audio file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(file.filename).suffix
        filename = f"{prefix}_{unique_id}_{timestamp}{ext}"
        
        settings.AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
        file_path = settings.AUDIO_OUT_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    @staticmethod
    async def save_temp_audio_file(file: UploadFile) -> Path:
        """Save uploaded audio file temporarily."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(file.filename).suffix if file.filename else ".wav"
        filename = f"temp_stt_{unique_id}_{timestamp}{ext}"
        
        temp_dir = settings.AUDIO_OUT_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / filename
        
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return file_path
    
    @staticmethod
    def cleanup_old_audio_files(max_age_hours: int = 24):
        """Clean up old audio files."""
        try:
            if not settings.AUDIO_OUT_DIR.exists():
                return
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in settings.AUDIO_OUT_DIR.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        print(f"Cleaned up old audio file: {file_path.name}")
        except Exception as e:
            print(f"Error cleaning up audio files: {e}")
```

### 4. `backend/services/organization/permission_service.py`
```python
"""Organization permission and role checking service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.database.models import OrganizationMember, OrganizationRole, User


class OrganizationPermissionService:
    """Handle organization-level permissions and role checks."""
    
    @staticmethod
    async def get_user_organization_role(
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> Optional[OrganizationRole]:
        """Get user's role in a specific organization."""
        result = await db.execute(
            select(OrganizationMember.role)
            .where(
                and_(
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.organization_id == organization_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def check_organization_permission(
        db: AsyncSession,
        user: User,
        organization_id: str,
        required_roles: List[OrganizationRole] = None
    ) -> bool:
        """Check if user has permission to access organization."""
        # System admins have access to all organizations
        if user.role.value == "admin":
            return True
        
        # Check organization membership
        user_role = await OrganizationPermissionService.get_user_organization_role(
            db, user.id, organization_id
        )
        if not user_role:
            return False
        
        # Check specific role requirements
        if required_roles and user_role not in required_roles:
            return False
        
        return True
    
    @staticmethod
    def has_org_admin_permission(user_role: OrganizationRole, action: str) -> bool:
        """Check if ORG_ADMIN role has permission for specific actions."""
        if user_role not in [OrganizationRole.ORG_ADMIN, OrganizationRole.ADMIN, OrganizationRole.OWNER]:
            return False
        
        if user_role == OrganizationRole.OWNER:
            return True
        
        if user_role == OrganizationRole.ADMIN:
            return True
        
        if user_role == OrganizationRole.ORG_ADMIN:
            allowed_actions = [
                "view_organization", "view_members", "remove_member",
                "update_member_role", "update_organization", "manage_billing"
            ]
            restricted_actions = [
                "delete_organization", "promote_to_owner", "demote_owner"
            ]
            
            if action in allowed_actions:
                return True
            if action in restricted_actions:
                return False
        
        return False
```

### 5. `backend/services/documents/document_task_service.py`
```python
"""Document background processing task service."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from backend.database.models import Document, DocumentStatus
from backend.services.document_service import get_document_service


logger = logging.getLogger(__name__)


class DocumentTaskService:
    """Handle document processing background tasks."""
    
    @staticmethod
    async def process_documents_background(
        document_ids: List[str],
        session: AsyncSession,
        force_reprocess: bool = False
    ):
        """Background task for processing documents."""
        service = get_document_service()
        
        processed_count = 0
        failed_count = 0
        
        for doc_id in document_ids:
            try:
                result = await session.execute(
                    select(Document).where(Document.id == doc_id)
                )
                document = result.scalar_one_or_none()
                
                if not document:
                    logger.warning(f"Document not found for processing: {doc_id}")
                    failed_count += 1
                    continue
                
                if document.status == DocumentStatus.INDEXED and not force_reprocess:
                    logger.info(f"Document already processed, skipping: {doc_id}")
                    continue
                
                if force_reprocess and document.status == DocumentStatus.INDEXED:
                    document.status = DocumentStatus.PENDING
                    await session.commit()
                
                success = await service.process_document(doc_id, session)
                if success:
                    processed_count += 1
                    logger.info(f"Document processed successfully: {doc_id}")
                else:
                    failed_count += 1
                    logger.error(f"Document processing failed: {doc_id}")
            
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing document {doc_id}: {e}")
        
        logger.info(f"Background processing completed: {processed_count} processed, {failed_count} failed")
```

## Updated `__init__.py` Files

### `backend/services/auth/__init__.py`
```python
"""Auth Service Module - Authentication and Authorization"""
from .authentication_service import AuthenticationService
from .authorization_service import AuthorizationService

__all__ = ["AuthenticationService", "AuthorizationService"]
```

### `backend/services/media/__init__.py`
```python
"""Media Service Module - Audio Processing and Speech"""
from .audio_service import AudioService

__all__ = ["AudioService"]
```

### `backend/services/organization/__init__.py`
```python
"""Organization Service Module - Multi-Tenant Management"""
from .permission_service import OrganizationPermissionService
from ..organization_service import OrganizationService
from ..tier_service import UserTierService

__all__ = ["OrganizationPermissionService", "OrganizationService", "UserTierService"]
```

### `backend/services/documents/__init__.py`
```python
"""Documents Service Module - Document Lifecycle and RAG"""
from .document_task_service import DocumentTaskService
from ..document_service import DocumentService

__all__ = ["DocumentService", "DocumentTaskService"]
```

## Example: Route Migration (Before & After)

### Example 1: Auth Route

**BEFORE:**
```python
# backend/api/routes/auth.py
from backend.api.helper.AuthHelper import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_organization
)

@router.post("/register")
async def register_user(user_data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Use helper functions directly
    password_hash = hash_password(user_data.password)
    # ... create user
    return user_response

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

**AFTER:**
```python
# backend/api/routes/auth.py
from backend.services.auth.authentication_service import AuthenticationService
from backend.services.auth.authorization_service import AuthorizationService

@router.post("/register")
async def register_user(user_data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Use service class
    password_hash = AuthenticationService.hash_password(user_data.password)
    # ... create user
    return user_response

@router.get("/me")
async def get_me(current_user: User = Depends(AuthorizationService.get_current_user)):
    return current_user
```

### Example 2: Chat Route

**BEFORE:**
```python
# backend/api/routes/chat.py
from backend.api.helper.ChatHelper import (
    validate_audio_file,
    save_audio_file,
    cleanup_old_audio_files,
)

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    is_valid, error = validate_audio_file(file.filename, file.size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    path = await save_audio_file(file)
    return {"path": str(path)}
```

**AFTER:**
```python
# backend/api/routes/chat.py
from backend.services.media.audio_service import AudioService

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    is_valid, error = AudioService.validate_audio_file(file.filename, file.size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    path = await AudioService.save_audio_file(file)
    return {"path": str(path)}
```

---

**Document Version:** 1.0
**Date:** November 2025
**Status:** Ready for Implementation
