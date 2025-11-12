# Organization Management

## Overview

The Tamil AI Voice Assistant supports a comprehensive multi-tenant organization management system with a dashboard-first approach. Users are redirected to an organization dashboard after login/registration where they can manage their organization ownership and memberships.

## Key Features

### Dashboard-First Approach
- Users redirected to organization dashboard after login/registration
- Central hub for managing organization ownership and memberships
- No forced single-organization setup flow
- Intuitive organization switching and management

### Business Rules
1. **Ownership Limit**: Each user can own maximum 1 organization
2. **Membership Limit**: Each user can be a member of maximum 5 organizations total
3. **Free Creation**: Users can create organizations freely (subject to ownership limit)
4. **Ownership Transfer**: Organization owners can transfer ownership to existing members

### Multi-Level Role System
- **App Level Roles**: USER, ADMIN, ORGANIZATION_ADMIN
- **Organization Level Roles**: OWNER, MEMBER

## Organization Dashboard

### Dashboard Sections

#### 1. Owned Organization Card
- Displays the single organization owned by the user (if any)
- Shows organization details: name, description, member count
- Quick actions: Enter, Manage, Transfer Ownership, Delete
- Only visible if user owns an organization

#### 2. Member Organizations Grid
- Grid layout showing up to 5 organizations where user is a member
- Each card shows: org name, description, user's role, member count
- Quick actions: Enter, Leave Organization
- Sorted by join date (most recent first)

#### 3. Create Organization Section
- Large "Create Organization" button
- Only visible if user doesn't own an organization
- Opens organization creation modal/form

#### 4. Pending Invitations
- List of pending organization invitations
- Actions: Accept, Decline
- Shows invitation details: org name, invited by, invitation date

## Organization Creation

### Creation Process
1. User clicks "Create Organization" button on dashboard
2. System validates user can create organization (ownership limit check)
3. User fills organization creation form
4. Email verification required (6-digit OTP)
5. Organization created and user becomes owner
6. Dashboard updates to show new owned organization

### Organization Details
```typescript
interface CreateOrganizationRequest {
  name: string;              // Required: Organization name (must be unique globally)
  description?: string;      // Optional: Organization description
  website?: string;          // Optional: Organization website
  industry?: string;         // Optional: Industry type
  size?: string;            // Optional: Organization size (startup, small, medium, large, enterprise)
  timezone?: string;        // Optional: Default timezone
  billing_email?: string;   // Optional: Billing contact email
}
```

### Validation Rules
- **Organization Name Uniqueness**: Names must be globally unique across platform
- **Ownership Validation**: User cannot create if they already own an organization
- **Email Verification**: Required for organization creation
- **Name Requirements**: 3-100 characters, special characters allowed

## Member Management

### Invitation System
- Email-based invitation system
- Invitation links with 7-day expiration
- Role assignment during invitation (MEMBER only for now)
- Professional email templates

### Membership Limits
- Maximum 5 organization memberships per user
- Validation during invitation acceptance
- Clear error messages when limits exceeded

### Member Roles
- **OWNER**: Full control, can transfer ownership, delete organization
- **MEMBER**: Basic access to organization resources

## Organization Switching

### Active Organization Context
- Users have one "active" organization at a time
- All operations performed in context of active organization
- Seamless switching without re-authentication

### Switching Process
1. User clicks "Enter" on any organization card in dashboard
2. System updates `active_organization_id` in user profile
3. User redirected to main app with selected organization context
4. Organization switcher in header shows current active organization

## Data Isolation

### Organization-Scoped Data
- Documents and conversations are organization-specific
- Users can only access data from their current active organization
- Vector embeddings isolated by organization
- Search results filtered by organization membership

### Security Measures
- API endpoints validate organization membership
- Database queries include organization filters
- File storage organized by organization
- Audit logs track organization-specific actions

## Organization Deletion

### Deletion Process
1. Only organization owner can delete organization
2. Confirmation dialog with organization name verification
3. All members automatically removed from organization
4. Organization data marked for deletion
5. Members notified of organization deletion

### Data Handling
- User accounts preserved after organization deletion
- Users can create new organizations or join existing ones
- Deleted organization data follows retention policies
- Audit trail maintained for compliance

## Ownership Transfer

### Transfer Process
1. Owner selects "Transfer Ownership" from organization management
2. Owner selects existing member as new owner
3. Confirmation required from both parties
4. Roles updated: old owner becomes member, new member becomes owner
5. All members notified of ownership change

### Transfer Requirements
- New owner must be existing organization member
- Cannot transfer to external users
- Original owner becomes regular member after transfer
- Transfer is irreversible once confirmed

## Validation Messages

### User-Friendly Error Messages
- **Ownership Limit**: "You can only own one organization. Transfer or delete your current organization first."
- **Membership Limit**: "You can only be a member of up to 5 organizations."
- **Organization Deleted**: "The organization has been deleted. All members have been removed."
- **Removed from Organization**: "You have been removed from [Organization Name]."

## API Endpoints

### Dashboard API
```bash
# Get organization dashboard data
GET /organizations/dashboard
Response: {
  ownedOrganization: Organization | null,
  memberOrganizations: OrganizationMembership[],
  pendingInvitations: OrganizationInvitation[],
  canCreateOrganization: boolean,
  canJoinMoreOrganizations: boolean
}
```

### Organization Management
```bash
# Create organization (with validation)
POST /organizations
Body: CreateOrganizationRequest

# Update organization
PUT /organizations/{id}
Body: UpdateOrganizationRequest

# Delete organization (owner only)
DELETE /organizations/{id}

# Switch active organization
POST /organizations/{id}/switch

# Transfer ownership
PUT /organizations/{id}/transfer-ownership
Body: { newOwnerId: string }
```

### Member Management
```bash
# List organization members
GET /organizations/{id}/members

# Invite member
POST /organizations/{id}/invite
Body: { email: string, role: OrganizationRole }

# Remove member
DELETE /organizations/{id}/members/{userId}

# Leave organization
POST /organizations/{id}/leave
```

## Email Verification System

### Organization Creation Verification
When creating an organization, users must verify their email address:

1. User submits organization creation form
2. System sends 6-digit OTP to user's email
3. User enters OTP within 10 minutes
4. Organization is created upon successful verification
5. User becomes the organization owner

### OTP Details
- **Format**: 6-digit numeric code
- **Expiration**: 10 minutes
- **Delivery**: Email to user's registered address
- **Rate Limiting**: Max 3 attempts per 10-minute window

## Email Configuration

### SMTP Settings
Required environment variables for email functionality:

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com
SMTP_FROM_NAME=Tamil AI Assistant

# Email Features
EMAIL_VERIFICATION_ENABLED=true
ORGANIZATION_INVITATIONS_ENABLED=true
```

### Email Templates
- Organization creation verification
- Member invitation emails
- Organization deletion notifications
- Ownership transfer notifications
- Member removal notifications

## Database Schema

### Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    website VARCHAR(255),
    industry VARCHAR(100),
    size VARCHAR(50) DEFAULT 'startup',
    timezone VARCHAR(50) DEFAULT 'UTC',
    creator_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    billing_email VARCHAR(255),
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Organization Members Table
```sql
CREATE TABLE organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    role organization_role NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited_by UUID REFERENCES users(id),
    UNIQUE(organization_id, user_id)
);
```

### User Model Updates
```sql
-- Add active organization reference to users table
ALTER TABLE users ADD COLUMN active_organization_id UUID REFERENCES organizations(id);
```

## Security Considerations

### Access Control
- All API endpoints validate organization membership
- Role-based permissions enforced at API level
- Database queries include organization filters
- File access restricted by organization

### Data Protection
- Organization data encrypted at rest
- Secure email delivery for invitations
- Rate limiting on organization creation
- Audit logging for organization changes

### Privacy
- Organization member lists only visible to members
- Email addresses protected in invitations
- Organization settings private to members
- Data deletion compliance (GDPR)

## Best Practices

### Organization Setup
1. Choose descriptive, unique organization names
2. Set up proper email configuration before creating organizations
3. Assign appropriate roles to members
4. Regularly review member access and permissions

### Member Management
1. Use email invitations for adding members
2. Monitor membership limits
3. Regularly audit organization membership
4. Remove inactive members promptly

### Security
1. Enable email verification for organization creation
2. Monitor organization access logs
3. Use strong passwords and 2FA
4. Regularly review organization settings

## Troubleshooting

### Common Issues

#### Cannot Create Organization
- Check if user already owns an organization
- Verify email verification is working
- Ensure organization name is unique
- Check user permissions

#### Membership Limit Reached
- User can only join 5 organizations maximum
- Review current memberships
- Leave unused organizations
- Contact admin for limit increase

#### Organization Name Conflicts
- Organization names must be globally unique
- Try variations or add descriptive terms
- Check for similar existing names
- Contact support for assistance

#### Email Verification Issues
- Check SMTP configuration
- Verify email server connectivity
- Check spam/junk folders
- Ensure email address is valid

## Future Enhancements

### Planned Features
- Organization templates and presets
- Advanced member permission management
- Organization analytics and reporting
- Integration with external identity providers
- Bulk member import/export
- Organization branding and customization

### Dashboard Improvements
- Real-time updates for organization changes
- Advanced filtering and search
- Organization activity feeds
- Member activity tracking
- Usage analytics and insights

### API Improvements
- GraphQL support for complex queries
- Webhook notifications for organization events
- Advanced filtering and search capabilities
- Rate limiting and quota management
- Bulk operations support

---

The organization management system provides a robust foundation for multi-tenant collaboration with a user-friendly dashboard-first approach while maintaining security, performance, and scalability standards.
