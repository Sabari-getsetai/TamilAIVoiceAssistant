# Organization Architecture

This document describes the multi-tenant organization architecture of the Tamil AI Voice Assistant platform.

## Overview

The platform implements a **multi-tenant architecture** where:
- Each organization has isolated data and resources
- Users can belong to multiple organizations
- All data access is scoped by organization context
- Organizations have hierarchical role-based access control

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Context │  │ Org Selector │  │ Role Guards  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ JWT with org_id
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Authentication Middleware                │   │
│  │  - Validates JWT token                               │   │
│  │  - Extracts user_id and org_id                       │   │
│  │  - Verifies organization membership                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Organization Context Manager                │   │
│  │  - Injects org_id into all queries                   │   │
│  │  - Enforces data isolation                           │   │
│  │  - Validates role permissions                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Organizations│  │    Users     │  │  Documents   │      │
│  │              │  │              │  │              │      │
│  │ - id         │  │ - id         │  │ - id         │      │
│  │ - name       │  │ - email      │  │ - org_id ────┼──┐   │
│  │ - owner_id   │  │ - password   │  │ - filename   │  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│         │                  │                            │   │
│         │                  │                            │   │
│  ┌──────────────────────────────────┐                  │   │
│  │    OrganizationMembers           │                  │   │
│  │  - org_id ───────────────────────┼──────────────────┘   │
│  │  - user_id                       │                      │
│  │  - role (Owner/Admin/Member)     │                      │
│  │  - joined_at                     │                      │
│  └──────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Organization Model

```python
class Organization(Base):
    __tablename__ = "organizations"
    
    id: UUID
    name: str  # Globally unique
    description: Optional[str]
    owner_id: UUID  # Reference to User
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    members: List[OrganizationMember]
    documents: List[Document]
    chat_sessions: List[ChatSession]
```

**Key Features:**
- Globally unique organization names
- Owner is automatically assigned on creation
- Soft delete support (is_deleted flag)
- Audit trail (created_at, updated_at)

### 2. Organization Member Model

```python
class OrganizationMember(Base):
    __tablename__ = "organization_members"
    
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationRole  # Owner, Admin, Member
    joined_at: datetime
    invited_by: Optional[UUID]
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id'),
    )
```

**Role Hierarchy:**
- **Owner**: Full control, can delete organization, manage all members
- **Admin**: Can manage members, documents, and settings
- **Member**: Can view and use organization resources

### 3. User Model (Extended)

```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID
    email: str  # Unique
    password_hash: str
    full_name: str
    is_email_verified: bool
    email_verification_token: Optional[str]
    email_verification_expires: Optional[datetime]
    created_at: datetime
    
    # Relationships
    organizations: List[OrganizationMember]
    owned_organizations: List[Organization]
```

## Data Isolation Strategy

### 1. Query-Level Isolation

All database queries automatically include organization context:

```python
# Example: Fetching documents
documents = db.query(Document).filter(
    Document.organization_id == current_org_id,
    Document.is_deleted == False
).all()
```

### 2. API-Level Isolation

Every API endpoint validates organization membership:

```python
@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization)
):
    # current_org is automatically validated
    # Only returns documents for current_org
    return document_service.list_documents(current_org.id)
```

### 3. Vector Store Isolation

Document embeddings are tagged with organization ID:

```python
# When storing embeddings
metadata = {
    "organization_id": str(org_id),
    "document_id": str(doc_id),
    "filename": filename
}

# When querying
filter_dict = {"organization_id": str(org_id)}
results = vectorstore.similarity_search(
    query, 
    k=5, 
    filter=filter_dict
)
```

## Authentication Flow

### 1. Registration & Organization Creation

```
User Registration
    ↓
Email Verification (if enabled)
    ↓
Organization Creation (required)
    ↓
User becomes Owner
    ↓
JWT Token with org_id
```

### 2. Login with Multiple Organizations

```
User Login
    ↓
Fetch User's Organizations
    ↓
If multiple orgs:
    ├─→ Return list of organizations
    └─→ User selects organization
        ↓
    Generate JWT with selected org_id
    
If single org:
    └─→ Generate JWT with org_id
```

### 3. Organization Switching

```
User requests org switch
    ↓
Validate membership
    ↓
Generate new JWT with new org_id
    ↓
Frontend updates context
```

## JWT Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "org_id": "organization_id",
  "role": "admin",
  "exp": 1234567890
}
```

**Token Claims:**
- `sub`: User ID
- `email`: User email
- `org_id`: Current organization ID
- `role`: User's role in current organization
- `exp`: Token expiration timestamp

## Member Invitation Flow

```
Admin/Owner initiates invitation
    ↓
System generates invitation token
    ↓
Email sent to invitee
    ↓
Invitee clicks link
    ↓
If user exists:
    ├─→ Add to organization
    └─→ Send confirmation email
    
If user doesn't exist:
    ├─→ Redirect to registration
    ├─→ Auto-join after registration
    └─→ Send welcome email
```

## Role-Based Access Control (RBAC)

### Permission Matrix

| Action | Owner | Admin | Member |
|--------|-------|-------|--------|
| View documents | ✅ | ✅ | ✅ |
| Upload documents | ✅ | ✅ | ✅ |
| Delete documents | ✅ | ✅ | ❌ |
| Invite members | ✅ | ✅ | ❌ |
| Remove members | ✅ | ✅ | ❌ |
| Change member roles | ✅ | ✅ | ❌ |
| Update org settings | ✅ | ✅ | ❌ |
| Delete organization | ✅ | ❌ | ❌ |
| Transfer ownership | ✅ | ❌ | ❌ |

### Implementation

```python
def require_role(min_role: OrganizationRole):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_member = kwargs.get('current_member')
            if current_member.role < min_role:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@router.delete("/members/{member_id}")
@require_role(OrganizationRole.ADMIN)
async def remove_member(...):
    # Only Admin and Owner can access
    pass
```

## Scalability Considerations

### 1. Database Indexing

```sql
-- Organization lookups
CREATE INDEX idx_org_name ON organizations(name);
CREATE INDEX idx_org_owner ON organizations(owner_id);

-- Member lookups
CREATE INDEX idx_member_org ON organization_members(organization_id);
CREATE INDEX idx_member_user ON organization_members(user_id);

-- Document lookups
CREATE INDEX idx_doc_org ON documents(organization_id);
```

### 2. Caching Strategy

```python
# Cache organization membership
@cache(ttl=300)  # 5 minutes
def get_user_organizations(user_id: UUID):
    return db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).all()

# Cache organization details
@cache(ttl=600)  # 10 minutes
def get_organization(org_id: UUID):
    return db.query(Organization).get(org_id)
```

### 3. Connection Pooling

```python
# PostgreSQL connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

## Security Measures

### 1. Organization Name Validation

- Must be unique globally
- 3-50 characters
- Alphanumeric, spaces, hyphens, underscores only
- Case-insensitive uniqueness check

### 2. Member Invitation Security

- Tokens expire after 7 days
- One-time use tokens
- Email verification required
- Rate limiting on invitations

### 3. Data Access Validation

- Every query includes organization filter
- Middleware validates organization membership
- Role-based permission checks
- Audit logging for sensitive operations

## Migration Strategy

### From Single-Tenant to Multi-Tenant

1. **Create default organization** for existing users
2. **Migrate existing data** to default organization
3. **Update all queries** to include organization filter
4. **Add organization context** to JWT tokens
5. **Update frontend** to handle organization selection

### Database Migration

```python
# Alembic migration
def upgrade():
    # Create organizations table
    op.create_table('organizations', ...)
    
    # Create organization_members table
    op.create_table('organization_members', ...)
    
    # Add organization_id to existing tables
    op.add_column('documents', 
        sa.Column('organization_id', UUID, nullable=True))
    
    # Create default organization
    # Migrate existing data
    # Make organization_id non-nullable
```

## Monitoring & Observability

### Key Metrics

- Organizations created per day
- Active organizations
- Average members per organization
- Documents per organization
- API requests per organization
- Storage usage per organization

### Logging

```python
logger.info(
    "Organization action",
    extra={
        "org_id": org_id,
        "user_id": user_id,
        "action": "member_invited",
        "target_email": invitee_email
    }
)
```

## Future Enhancements

1. **Organization Billing**: Track usage and implement billing
2. **Organization Templates**: Pre-configured organization setups
3. **Organization Analytics**: Usage statistics and insights
4. **Organization Branding**: Custom logos and themes
5. **Organization API Keys**: Programmatic access
6. **Organization Webhooks**: Event notifications
7. **Organization Backup**: Automated data backups
8. **Organization Transfer**: Transfer ownership between users

## References

- [Organization Management Feature](../features/organization-management.md)
- [Member Management Feature](../features/member-management.md)
- [Authentication Feature](../features/authentication.md)
- [Organization API Reference](../api/organization-api.md)
