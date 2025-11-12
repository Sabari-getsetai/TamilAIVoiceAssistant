# Organization API Documentation

## Overview

The Organization API provides comprehensive endpoints for managing organizations, members, and organization-scoped operations in the Tamil AI Voice Assistant platform. All endpoints require authentication and appropriate permissions.

## Base URL

```
http://localhost:8000/api
```

## Authentication

All API endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Organization Management

### Create Organization

Create a new organization. Authenticated users can create organizations and become the owner.

**Endpoint:** `POST /organizations`

**Request Body:**
```json
{
  "name": "My Organization",
  "description": "Organization description",
  "website": "https://example.com",
  "industry": "Technology",
  "size": "small"
}
```

**Response:**
```json
{
  "id": "org-123",
  "name": "My Organization",
  "description": "Organization description",
  "website": "https://example.com",
  "industry": "Technology",
  "size": "small",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "owner_id": "user-456",
  "member_count": 1,
  "settings": {
    "features_enabled": {
      "chat": true,
      "voice": true,
      "documents": true,
      "analytics": true
    },
    "quotas": {
      "max_members": 50,
      "max_documents": 1000,
      "max_storage_mb": 5000
    }
  }
}
```

**Status Codes:**
- `201` - Organization created successfully
- `400` - Invalid request data
- `401` - Authentication required
- `409` - Organization name already exists

### Get Organization

Retrieve organization details. User must be a member of the organization.

**Endpoint:** `GET /organizations/{org_id}`

**Response:**
```json
{
  "id": "org-123",
  "name": "My Organization",
  "description": "Organization description",
  "website": "https://example.com",
  "industry": "Technology",
  "size": "small",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "owner_id": "user-456",
  "member_count": 5,
  "current_user_role": "admin",
  "settings": {
    "features_enabled": {
      "chat": true,
      "voice": true,
      "documents": true,
      "analytics": true
    },
    "quotas": {
      "max_members": 50,
      "max_documents": 1000,
      "max_storage_mb": 5000
    }
  }
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Not a member of organization
- `404` - Organization not found

### Update Organization

Update organization details. Requires admin or owner role.

**Endpoint:** `PUT /organizations/{org_id}`

**Request Body:**
```json
{
  "name": "Updated Organization Name",
  "description": "Updated description",
  "website": "https://newwebsite.com",
  "industry": "Healthcare",
  "size": "medium"
}
```

**Response:**
```json
{
  "id": "org-123",
  "name": "Updated Organization Name",
  "description": "Updated description",
  "website": "https://newwebsite.com",
  "industry": "Healthcare",
  "size": "medium",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**
- `200` - Organization updated successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Admin access required
- `404` - Organization not found

### Delete Organization

Delete an organization. Only the owner can delete an organization.

**Endpoint:** `DELETE /organizations/{org_id}`

**Response:**
```json
{
  "message": "Organization deleted successfully"
}
```

**Status Codes:**
- `200` - Organization deleted successfully
- `401` - Authentication required
- `403` - Owner access required
- `404` - Organization not found

### List User Organizations

Get all organizations the current user is a member of.

**Endpoint:** `GET /organizations`

**Query Parameters:**
- `role` (optional): Filter by user's role in organizations (`member`, `admin`, `owner`)
- `limit` (optional): Number of results per page (default: 20)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "organizations": [
    {
      "id": "org-123",
      "name": "My Organization",
      "description": "Organization description",
      "current_user_role": "owner",
      "member_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "org-456",
      "name": "Another Organization",
      "description": "Another description",
      "current_user_role": "member",
      "member_count": 12,
      "created_at": "2024-01-02T00:00:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required

## Member Management

### Get Organization Members

Retrieve all members of an organization. User must be a member of the organization.

**Endpoint:** `GET /organizations/{org_id}/members`

**Query Parameters:**
- `role` (optional): Filter by role (`member`, `admin`, `owner`)
- `limit` (optional): Number of results per page (default: 20)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "members": [
    {
      "id": "member-123",
      "user_id": "user-456",
      "role": "owner",
      "joined_at": "2024-01-01T00:00:00Z",
      "user": {
        "id": "user-456",
        "full_name": "John Doe",
        "email": "john@example.com",
        "avatar_url": "https://example.com/avatar.jpg"
      }
    },
    {
      "id": "member-789",
      "user_id": "user-101",
      "role": "admin",
      "joined_at": "2024-01-02T00:00:00Z",
      "user": {
        "id": "user-101",
        "full_name": "Jane Smith",
        "email": "jane@example.com",
        "avatar_url": "https://example.com/avatar2.jpg"
      }
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Not a member of organization
- `404` - Organization not found

### Invite Member

Invite a new member to the organization. Requires admin or owner role.

**Endpoint:** `POST /organizations/{org_id}/invitations`

**Request Body:**
```json
{
  "email": "newmember@example.com",
  "role": "member",
  "message": "Welcome to our organization!"
}
```

**Response:**
```json
{
  "invitation_id": "inv-123",
  "message": "Invitation sent successfully",
  "expires_at": "2024-01-08T00:00:00Z"
}
```

**Status Codes:**
- `201` - Invitation sent successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Admin access required
- `409` - User already a member or invitation already exists

### Bulk Invite Members

Invite multiple members to the organization. Requires admin or owner role.

**Endpoint:** `POST /organizations/{org_id}/invitations/bulk`

**Request Body:**
```json
{
  "invitations": [
    {
      "email": "user1@example.com",
      "role": "member"
    },
    {
      "email": "user2@example.com",
      "role": "admin"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "email": "user1@example.com",
      "status": "sent",
      "invitation_id": "inv-124"
    },
    {
      "email": "user2@example.com",
      "status": "failed",
      "error": "User already a member"
    }
  ],
  "summary": {
    "total": 2,
    "sent": 1,
    "failed": 1
  }
}
```

**Status Codes:**
- `200` - Bulk invitation processed
- `400` - Invalid request data
- `401` - Authentication required
- `403` - Admin access required

### Update Member Role

Update a member's role in the organization. Requires admin or owner role.

**Endpoint:** `PUT /organizations/{org_id}/members/{member_id}/role`

**Request Body:**
```json
{
  "role": "admin"
}
```

**Response:**
```json
{
  "message": "Member role updated successfully",
  "member": {
    "id": "member-789",
    "user_id": "user-101",
    "role": "admin",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Role updated successfully
- `400` - Invalid role
- `401` - Authentication required
- `403` - Admin access required or insufficient permissions
- `404` - Member not found

### Remove Member

Remove a member from the organization. Requires admin or owner role.

**Endpoint:** `DELETE /organizations/{org_id}/members/{member_id}`

**Response:**
```json
{
  "message": "Member removed successfully"
}
```

**Status Codes:**
- `200` - Member removed successfully
- `401` - Authentication required
- `403` - Admin access required or cannot remove yourself
- `404` - Member not found

## Invitation Management

### Get Invitation Details

Get details of an invitation by invitation code. Public endpoint.

**Endpoint:** `GET /invitations/{invitation_code}`

**Response:**
```json
{
  "organization": {
    "id": "org-123",
    "name": "My Organization",
    "description": "Organization description",
    "member_count": 5
  },
  "role": "member",
  "invited_by": "John Doe",
  "expires_at": "2024-01-08T00:00:00Z"
}
```

**Status Codes:**
- `200` - Success
- `404` - Invalid or expired invitation

### Accept Invitation

Accept an organization invitation. Requires authentication.

**Endpoint:** `POST /invitations/{invitation_code}/accept`

**Response:**
```json
{
  "message": "Invitation accepted successfully",
  "organization_id": "org-123",
  "membership": {
    "id": "member-999",
    "role": "member",
    "joined_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Invitation accepted successfully
- `400` - Already a member of organization
- `401` - Authentication required
- `404` - Invalid or expired invitation

### List Organization Invitations

Get all pending invitations for an organization. Requires admin or owner role.

**Endpoint:** `GET /organizations/{org_id}/invitations`

**Response:**
```json
{
  "invitations": [
    {
      "id": "inv-123",
      "email": "pending@example.com",
      "role": "member",
      "invited_by": "John Doe",
      "created_at": "2024-01-01T00:00:00Z",
      "expires_at": "2024-01-08T00:00:00Z",
      "status": "pending"
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Admin access required

### Cancel Invitation

Cancel a pending invitation. Requires admin or owner role.

**Endpoint:** `DELETE /organizations/{org_id}/invitations/{invitation_id}`

**Response:**
```json
{
  "message": "Invitation cancelled successfully"
}
```

**Status Codes:**
- `200` - Invitation cancelled successfully
- `401` - Authentication required
- `403` - Admin access required
- `404` - Invitation not found

## Organization Settings

### Get Organization Settings

Retrieve organization settings. Requires admin or owner role.

**Endpoint:** `GET /organizations/{org_id}/settings`

**Response:**
```json
{
  "features_enabled": {
    "chat": true,
    "voice": true,
    "documents": true,
    "analytics": true,
    "api_access": false
  },
  "quotas": {
    "max_members": 50,
    "max_documents": 1000,
    "max_storage_mb": 5000,
    "max_api_calls_per_month": 10000
  },
  "security": {
    "require_2fa": false,
    "allowed_domains": [],
    "session_timeout_minutes": 480
  },
  "notifications": {
    "email_notifications": true,
    "member_join_notifications": true,
    "usage_alerts": true
  }
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Admin access required
- `404` - Organization not found

### Update Organization Settings

Update organization settings. Requires admin or owner role.

**Endpoint:** `PUT /organizations/{org_id}/settings`

**Request Body:**
```json
{
  "features_enabled": {
    "chat": true,
    "voice": true,
    "documents": true,
    "analytics": false
  },
  "security": {
    "require_2fa": true,
    "session_timeout_minutes": 240
  },
  "notifications": {
    "email_notifications": false
  }
}
```

**Response:**
```json
{
  "message": "Settings updated successfully",
  "settings": {
    "features_enabled": {
      "chat": true,
      "voice": true,
      "documents": true,
      "analytics": false,
      "api_access": false
    },
    "security": {
      "require_2fa": true,
      "session_timeout_minutes": 240
    }
  }
}
```

**Status Codes:**
- `200` - Settings updated successfully
- `400` - Invalid settings data
- `401` - Authentication required
- `403` - Admin access required

## Organization Analytics

### Get Organization Usage Statistics

Retrieve usage statistics for the organization. Requires admin or owner role.

**Endpoint:** `GET /organizations/{org_id}/analytics/usage`

**Query Parameters:**
- `period` (optional): Time period (`day`, `week`, `month`, `year`) (default: `month`)
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format

**Response:**
```json
{
  "period": "month",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "metrics": {
    "total_chat_messages": 1250,
    "total_voice_sessions": 85,
    "total_documents_uploaded": 45,
    "total_storage_used_mb": 2340,
    "active_members": 12,
    "api_calls_made": 5670
  },
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "chat_messages": 42,
      "voice_sessions": 3,
      "documents_uploaded": 2
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Admin access required
- `404` - Organization not found

### Get Member Activity

Retrieve member activity statistics. Requires admin or owner role.

**Endpoint:** `GET /organizations/{org_id}/analytics/members`

**Response:**
```json
{
  "member_activity": [
    {
      "user_id": "user-456",
      "full_name": "John Doe",
      "role": "owner",
      "last_active": "2024-01-01T12:00:00Z",
      "metrics": {
        "chat_messages": 150,
        "voice_sessions": 12,
        "documents_uploaded": 5,
        "total_session_time_minutes": 480
      }
    }
  ],
  "summary": {
    "total_active_members": 8,
    "average_session_time_minutes": 45,
    "most_active_feature": "chat"
  }
}
```

**Status Codes:**
- `200` - Success
- `401` - Authentication required
- `403` - Admin access required

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request data",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions",
  "required_role": "admin"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Organization not found"
}
```

### 409 Conflict
```json
{
  "error": "Conflict",
  "message": "Organization name already exists"
}
```

### 422 Validation Error
```json
{
  "error": "Validation Error",
  "message": "Request validation failed",
  "details": [
    {
      "field": "name",
      "message": "Organization name is required"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authentication endpoints**: 5 requests per minute per IP
- **Organization management**: 100 requests per hour per user
- **Member management**: 50 requests per hour per user
- **Analytics endpoints**: 20 requests per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

**Request:**
```
GET /organizations?limit=10&offset=20
```

**Response:**
```json
{
  "organizations": [...],
  "total": 150,
  "limit": 10,
  "offset": 20,
  "has_next": true,
  "has_previous": true
}
```

## Filtering and Sorting

Some endpoints support filtering and sorting:

**Organization Members:**
```
GET /organizations/{org_id}/members?role=admin&sort=joined_at&order=desc
```

**User Organizations:**
```
GET /organizations?role=owner&sort=created_at&order=asc
```

## Webhooks

Organizations can configure webhooks to receive real-time notifications:

### Webhook Events
- `member.invited` - Member invitation sent
- `member.joined` - Member accepted invitation
- `member.removed` - Member removed from organization
- `member.role_changed` - Member role updated
- `organization.updated` - Organization details updated
- `organization.deleted` - Organization deleted

### Webhook Payload Example
```json
{
  "event": "member.joined",
  "timestamp": "2024-01-01T12:00:00Z",
  "organization_id": "org-123",
  "data": {
    "member": {
      "id": "member-456",
      "user_id": "user-789",
      "role": "member",
      "joined_at": "2024-01-01T12:00:00Z"
    }
  }
}
```

## SDK Examples

### JavaScript/TypeScript

```typescript
import { OrganizationAPI } from '@tamil-ai/sdk';

const api = new OrganizationAPI({
  baseURL: 'http://localhost:8000/api',
  token: 'your-jwt-token'
});

// Create organization
const org = await api.organizations.create({
  name: 'My Organization',
  description: 'Organization description'
});

// Invite member
await api.organizations.inviteMember(org.id, {
  email: 'member@example.com',
  role: 'member'
});

// Get members
const members = await api.organizations.getMembers(org.id);
```

### Python

```python
from tamil_ai_sdk import OrganizationAPI

api = OrganizationAPI(
    base_url='http://localhost:8000/api',
    token='your-jwt-token'
)

# Create organization
org = api.organizations.create({
    'name': 'My Organization',
    'description': 'Organization description'
})

# Invite member
api.organizations.invite_member(org['id'], {
    'email': 'member@example.com',
    'role': 'member'
})

# Get members
members = api.organizations.get_members(org['id'])
```

### cURL Examples

```bash
# Create organization
curl -X POST "http://localhost:8000/api/organizations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Organization",
    "description": "Organization description"
  }'

# Invite member
curl -X POST "http://localhost:8000/api/organizations/org-123/invitations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@example.com",
    "role": "member"
  }'

# Get organization details
curl -X GET "http://localhost:8000/api/organizations/org-123" \
  -H "Authorization: Bearer $TOKEN"
```

## Testing

### Postman Collection

A Postman collection is available for testing all organization API endpoints:

```json
{
  "info": {
    "name": "Tamil AI Organization API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{jwt_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api"
    }
  ]
}
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_organization():
    response = client.post(
        "/api/organizations",
        json={
            "name": "Test Organization",
            "description": "Test description"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Organization"

def test_invite_member():
    response = client.post(
        f"/api/organizations/{org_id}/invitations",
        json={
            "email": "test@example.com",
            "role": "member"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
```

## Related Documentation

- [Authentication API](./auth-api.md)
- [Chat API](./chat-api.md)
- [Organization Management](../features/organization-management.md)
- [Member Management](../features/member-management.md)
- [Authentication System](../features/authentication.md)
- [API Rate Limiting](../reference/rate-limiting.md)
- [Webhook Configuration](../setup/webhook-setup.md)
