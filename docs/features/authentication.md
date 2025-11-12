# Authentication System

## Overview

The Tamil AI Voice Assistant implements a comprehensive JWT-based authentication system with organization-based multi-tenancy and role-based access control (RBAC). The system supports both individual user authentication and organization-scoped access control, enabling secure multi-tenant operations with complete data isolation between organizations.

**Key Requirement**: Users must be part of an organization to access the application features. After successful login, users without an active organization are redirected to create or join an organization.

## Organization-Based Authentication

### Multi-Tenant Architecture
The authentication system is designed around organizations as the primary tenant boundary:

- **Organization Context**: All authenticated operations occur within an organization context
- **Data Isolation**: Complete separation of data between organizations
- **Role Hierarchy**: Dual-level roles (system-level and organization-level)
- **Self-Service**: Organizations can manage their own members and permissions

### Organization Roles
- **Owner**: Full organization control, can delete organization
- **Admin**: Organization administration, member management, settings
- **Member**: Standard organization access, can use all features within organization scope

### System Roles
- **admin**: Full system access across all organizations
- **organization_admin**: Can create and manage organizations
- **user**: Standard user, must be invited to organizations

## Architecture

### Backend Components

#### Authentication API (`backend/api/auth.py`)
- **Endpoints:**
  - `POST /auth/register` - User registration
  - `POST /auth/login` - User login with JWT token generation
  - `POST /auth/refresh` - Refresh access token using refresh token
  - `POST /auth/logout` - User logout
  - `GET /auth/me` - Get current user profile
  - `PUT /auth/me` - Update user profile

- **Features:**
  - Password hashing with bcrypt
  - JWT token generation (access + refresh tokens)
  - Token expiration handling
  - Role-based access control
  - Email validation
  - Username uniqueness validation

#### System-Level Roles
- `admin` - Full system access across all organizations
- `organization_admin` - Can create organizations and has admin access to owned organizations
- `user` - Standard user access, requires organization membership

#### Organization-Level Roles
- `owner` - Full organization control including deletion
- `admin` - Organization administration and member management
- `member` - Standard organization access and feature usage

### Frontend Components

#### 1. Authentication Types (`app/nextjs/src/types/auth.ts`)
Defines TypeScript interfaces for:
- User model
- Login/Register requests
- Token responses
- Authentication context
- Error handling

#### 2. Authentication API Service (`app/nextjs/src/services/api/authApi.ts`)
- **TokenStorage Class:**
  - Manages access and refresh tokens in localStorage
  - Provides methods for token retrieval and storage
  - Handles token cleanup on logout

- **Axios Interceptors:**
  - Automatically injects access tokens into requests
  - Handles 401 errors with automatic token refresh
  - Redirects to login on authentication failure

- **API Methods:**
  - `register()` - User registration
  - `login()` - User authentication
  - `getCurrentUser()` - Fetch user profile
  - `refreshToken()` - Refresh access token
  - `logout()` - Clear tokens and logout
  - `updateProfile()` - Update user information

#### 3. Authentication Context (`app/nextjs/src/contexts/AuthContext.tsx`)
- **AuthProvider Component:**
  - Global authentication state management
  - Organization context management
  - Automatic token validation on app load
  - User session persistence
  - Organization switching support

- **useAuth Hook:**
  - Access authentication state and methods
  - Check authentication status
  - Perform login/logout operations
  - Organization context access
  - Organization switching

- **ProtectedRoute Component:**
  - HOC for route protection
  - Supports authentication requirements
  - Supports admin-only access
  - Organization membership validation
  - Automatic redirection for unauthorized access

- **usePermissions Hook:**
  - Check user permissions
  - Role-based access control helpers
  - Organization-level permission checking
  - System-level permission checking

- **useOrganization Hook:**
  - Access current organization context
  - Organization switching functionality
  - Organization membership management

#### 4. Login Page (`app/nextjs/src/app/login/page.tsx`)
- Professional Material-UI design
- Form validation
- Password visibility toggle
- Error handling with snackbar notifications
- Responsive layout with gradient background
- Automatic redirect after successful login

#### 5. Registration Page (`app/nextjs/src/app/register/page.tsx`)
- Comprehensive registration form
- Real-time password strength validation
- Password requirements display
- Email and username validation
- Password confirmation matching
- Visual feedback with chips and progress indicators
- Auto-login after successful registration

#### 6. AppBar Component (`app/nextjs/src/components/layout/AppBar.tsx`)
- User profile display with avatar
- Role badge (admin/organization_admin/user)
- User menu with:
  - Display name and email
  - Logout option
- Login button for unauthenticated users

## Protected Routes

All pages are protected with the `ProtectedRoute` component supporting both authentication and organization context:

```typescript
// System admin only
<ProtectedRoute requireAuth={true} requireAdmin={true}>
  <SystemAdminPage />
</ProtectedRoute>

// Organization member required
<ProtectedRoute requireAuth={true} requireOrganization={true}>
  <OrganizationPage />
</ProtectedRoute>

// Organization admin required
<ProtectedRoute requireAuth={true} requireOrganization={true} requireOrgAdmin={true}>
  <OrgAdminPage />
</ProtectedRoute>
```

### Protected Pages:

#### System-Level Pages:
- `/admin` - System Admin Dashboard (system admin only)
- `/admin/organizations` - Organization Management (system admin only)
- `/admin/users` - User Management (system admin only)
- `/admin/system-settings` - System Settings (system admin only)

#### Organization-Level Pages:
- `/org/[orgId]/dashboard` - Organization Dashboard (organization member)
- `/org/[orgId]/chat` - Chat Interface (organization member)
- `/org/[orgId]/voice` - Voice Assistant (organization member)
- `/org/[orgId]/documents` - Document Management (organization member)
- `/org/[orgId]/settings` - Organization Settings (organization admin)
- `/org/[orgId]/members` - Member Management (organization admin)
- `/org/[orgId]/analytics` - Organization Analytics (organization admin)

#### Public Pages:
- `/login` - User Login
- `/register` - User Registration
- `/org/create` - Organization Creation (authenticated users)
- `/org/join/[inviteCode]` - Organization Invitation (authenticated users)

## Token Management

### Access Token
- Short-lived (15 minutes default)
- Used for API authentication
- Contains user ID, system role, and current organization context
- Automatically refreshed when expired

### Refresh Token
- Long-lived (7 days default)
- Used to obtain new access tokens
- Stored securely in localStorage

### Organization Context Token
- Contains current organization ID and user's role within that organization
- Updated when user switches organizations
- Included in all API requests for organization-scoped operations

### Token Flow
1. User logs in → Receives access + refresh tokens
2. User selects organization → Token updated with organization context
3. Access token stored in localStorage with organization context
4. Access token automatically added to API requests
5. On 401 error → Attempt token refresh
6. If refresh succeeds → Retry original request
7. If refresh fails → Redirect to login
8. On organization switch → Update token with new organization context

## Admin API Integration

The `adminApi.ts` service has been updated to:
- Automatically inject authentication tokens
- Handle token refresh on 401 errors
- Redirect to login on authentication failure

```typescript
// Request interceptor adds token
api.interceptors.request.use((config) => {
  const token = TokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor handles token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      // Retry original request
    }
    return Promise.reject(error);
  }
);
```

## Usage Examples

### Using Authentication in Components

```typescript
import { useAuth, useOrganization } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  const { currentOrganization, switchOrganization } = useOrganization();

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  if (!currentOrganization) {
    return <div>Please select an organization</div>;
  }

  return (
    <div>
      <p>Welcome, {user.full_name}!</p>
      <p>Organization: {currentOrganization.name}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Checking Permissions

```typescript
import { usePermissions } from '@/contexts/AuthContext';

function AdminFeature() {
  const { 
    hasSystemAdminAccess, 
    hasOrgAdminAccess, 
    isSystemAdmin,
    isOrgAdmin,
    isOrgMember 
  } = usePermissions();

  if (!hasOrgAdminAccess) {
    return <div>Organization admin access required</div>;
  }

  return <div>Organization admin content</div>;
}
```

### Organization Context

```typescript
import { useOrganization } from '@/contexts/AuthContext';

function OrganizationSelector() {
  const { 
    currentOrganization, 
    userOrganizations, 
    switchOrganization,
    isLoading 
  } = useOrganization();

  return (
    <select 
      value={currentOrganization?.id || ''} 
      onChange={(e) => switchOrganization(e.target.value)}
    >
      {userOrganizations.map(org => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </select>
  );
}
```

### Protecting Routes

```typescript
import { ProtectedRoute } from '@/contexts/AuthContext';

// System admin only
export default function SystemAdminPage() {
  return (
    <ProtectedRoute requireAuth={true} requireAdmin={true}>
      <div>System admin content</div>
    </ProtectedRoute>
  );
}

// Organization member required
export default function OrganizationPage() {
  return (
    <ProtectedRoute requireAuth={true} requireOrganization={true}>
      <div>Organization content</div>
    </ProtectedRoute>
  );
}

// Organization admin required
export default function OrgAdminPage() {
  return (
    <ProtectedRoute 
      requireAuth={true} 
      requireOrganization={true} 
      requireOrgAdmin={true}
    >
      <div>Organization admin content</div>
    </ProtectedRoute>
  );
}
```

### Organization Invitation Flow

```typescript
import { useAuth } from '@/contexts/AuthContext';

function InvitationPage({ inviteCode }: { inviteCode: string }) {
  const { acceptInvitation } = useAuth();

  const handleAcceptInvitation = async () => {
    try {
      await acceptInvitation(inviteCode);
      // Redirect to organization dashboard
    } catch (error) {
      // Handle invitation error
    }
  };

  return (
    <div>
      <h1>Organization Invitation</h1>
      <button onClick={handleAcceptInvitation}>
        Accept Invitation
      </button>
    </div>
  );
}
```

## Security Considerations

1. **Password Security:**
   - Passwords hashed with bcrypt
   - Minimum password requirements enforced
   - Password strength validation on frontend

2. **Token Security:**
   - Tokens stored in localStorage (consider httpOnly cookies for production)
   - Short-lived access tokens
   - Automatic token refresh
   - Tokens cleared on logout

3. **API Security:**
   - All admin endpoints require authentication
   - Role-based access control
   - Token validation on every request

4. **Frontend Security:**
   - Protected routes with automatic redirection
   - Permission-based UI rendering
   - Secure token storage and management

## Testing

### Manual Testing Checklist
- [ ] User registration with valid data
- [ ] User registration with invalid data (duplicate email/username)
- [ ] User login with correct credentials
- [ ] User login with incorrect credentials
- [ ] Access protected routes while authenticated
- [ ] Access protected routes while unauthenticated
- [ ] Token refresh on expiration
- [ ] Logout functionality
- [ ] Admin-only access control
- [ ] User profile display in AppBar
- [ ] Password strength validation

### API Testing
Use the provided test script:
```bash
python test_auth_endpoints.py
```

## Organization-Specific Features

### Organization Creation
- Self-service organization creation for authenticated users
- Organization name uniqueness validation
- Automatic owner role assignment
- Initial organization setup wizard

### Member Management
- Invite members via email
- Role-based access control within organizations
- Member removal and role changes
- Bulk member operations

### Organization Settings
- Organization profile management
- Feature toggles and quotas
- Billing and subscription management
- Data retention policies

### Organization Analytics
- Member activity tracking
- Usage statistics and quotas
- Audit logs for security
- Performance metrics

## Future Enhancements

1. **Security:**
   - Implement httpOnly cookies for token storage
   - Add CSRF protection
   - Implement rate limiting on auth endpoints
   - Add two-factor authentication (2FA)
   - Organization-level security policies
   - SSO integration for organizations

2. **Features:**
   - Password reset functionality
   - Email verification
   - Remember me option
   - Session management (view/revoke active sessions)
   - OAuth integration (Google, GitHub, etc.)
   - Organization-level API keys
   - Custom organization domains

3. **User Experience:**
   - Social login options
   - Profile picture upload
   - User preferences
   - Activity log
   - Organization switching UI improvements
   - Mobile app support

4. **Organization Features:**
   - Organization templates
   - Custom branding per organization
   - Advanced member permissions
   - Organization hierarchies (sub-organizations)
   - Cross-organization collaboration

## Troubleshooting

### Common Issues

**Issue: "Token expired" errors**
- Solution: Token refresh should happen automatically. Check browser console for errors.

**Issue: Redirected to login after successful authentication**
- Solution: Check if tokens are being stored correctly in localStorage.

**Issue: 401 errors on API calls**
- Solution: Verify that the Authorization header is being added to requests.

**Issue: Cannot access admin pages**
- Solution: Ensure user has admin or organization_admin role.

## Related Documentation

- [Organization Management](./organization-management.md)
- [Member Management](./member-management.md)
- [Organization API Documentation](../api/organization-api.md)
- [Backend API Documentation](../api/auth-api.md)
- [Organization Setup Guide](../getting-started/organization-setup.md)
- [Security Best Practices](../reference/security.md)
- [Migration Guide](../migration/single-to-multi-tenant.md)
