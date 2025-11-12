# Organization Dashboard System

## Overview

The Organization Dashboard is the central hub for users to manage their organization memberships and ownership. It implements a dashboard-first approach where users are redirected to the organization dashboard after login/registration instead of being forced into a single organization setup flow.

## Key Features

### Multi-Level Role System
- **App Level Roles**: USER, ADMIN, ORGANIZATION_ADMIN
- **Organization Level Roles**: OWNER, MEMBER

### Business Rules
1. **Ownership Limit**: Each user can own maximum 1 organization
2. **Membership Limit**: Each user can be a member of maximum 5 organizations total
3. **Free Creation**: Users can create organizations freely (subject to ownership limit)
4. **Ownership Transfer**: Organization owners can transfer ownership to existing members

## Dashboard Layout

### Main Sections

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

### Organization Cards

#### Owned Organization Card
```typescript
interface OwnedOrgCardProps {
  organization: Organization;
  memberCount: number;
  onEnter: () => void;
  onManage: () => void;
  onTransferOwnership: () => void;
  onDelete: () => void;
}
```

#### Member Organization Card
```typescript
interface MemberOrgCardProps {
  organization: Organization;
  userRole: OrganizationRole;
  memberCount: number;
  joinedAt: Date;
  onEnter: () => void;
  onLeave: () => void;
}
```

## User Flows

### New User Flow
1. User registers → Redirected to organization dashboard
2. Dashboard shows empty state with "Create Organization" option
3. User creates organization → Becomes owner → Dashboard updates

### Existing User Flow
1. User logs in → Redirected to organization dashboard
2. Dashboard shows owned org + member orgs
3. User can switch between organizations or create new one (if eligible)

### Organization Switching
1. User clicks "Enter" on any organization card
2. System updates `active_organization_id` in user profile
3. User is redirected to main app with selected organization context

## Validation Messages

### Popup Messages
- **Ownership Limit**: "You can only own one organization. Transfer or delete your current organization first."
- **Membership Limit**: "You can only be a member of up to 5 organizations."
- **Organization Deleted**: "The organization has been deleted. All members have been removed."
- **Removed from Organization**: "You have been removed from [Organization Name]."

## Component Architecture

### Page Structure
```
/organizations (OrganizationDashboard)
├── OwnedOrganizationSection
│   └── OwnedOrganizationCard
├── MemberOrganizationsSection
│   └── MemberOrganizationGrid
│       └── MemberOrganizationCard[]
├── CreateOrganizationSection
│   └── CreateOrganizationButton
└── PendingInvitationsSection
    └── InvitationCard[]
```

### Key Components

#### OrganizationDashboard
- Main dashboard page component
- Fetches user's organization data
- Manages dashboard state and actions

#### OwnedOrganizationCard
- Displays owned organization details
- Handles ownership-specific actions
- Shows management options

#### MemberOrganizationGrid
- Grid layout for member organizations
- Responsive design (1-3 columns based on screen size)
- Empty state when no memberships

#### CreateOrganizationButton
- Conditional rendering based on ownership status
- Opens organization creation modal
- Validates ownership limits

#### OrganizationSwitcher (Header Component)
- Dropdown in app header/sidebar
- Shows current active organization
- Allows quick switching between organizations

## State Management

### Dashboard Data Structure
```typescript
interface OrganizationDashboardData {
  ownedOrganization: Organization | null;
  memberOrganizations: OrganizationMembership[];
  pendingInvitations: OrganizationInvitation[];
  canCreateOrganization: boolean;
  canJoinMoreOrganizations: boolean;
}
```

### API Integration
- Single dashboard API call: `GET /organizations/dashboard`
- Real-time updates for invitations and membership changes
- Optimistic updates for better UX

## Responsive Design

### Desktop (1200px+)
- 3-column grid for member organizations
- Side-by-side layout for owned org and create button
- Full-width pending invitations

### Tablet (768px - 1199px)
- 2-column grid for member organizations
- Stacked layout for main sections
- Compact organization cards

### Mobile (< 768px)
- Single column layout
- Full-width organization cards
- Collapsible sections for better navigation

## Accessibility

### ARIA Labels
- Proper labeling for all interactive elements
- Screen reader friendly organization cards
- Keyboard navigation support

### Color Contrast
- High contrast for organization status indicators
- Clear visual hierarchy
- Color-blind friendly design

## Performance Considerations

### Data Loading
- Lazy loading for organization details
- Cached organization data
- Optimized API calls

### Image Optimization
- Organization logos with proper sizing
- Lazy loading for non-critical images
- Fallback avatars for organizations

## Security

### Access Control
- User can only see their own dashboard data
- Organization details filtered by membership
- Secure organization switching validation

### Data Validation
- Client-side and server-side validation
- Rate limiting for organization creation
- Input sanitization for organization data

## Future Enhancements

### Phase 2 Features
- Organization search and discovery
- Public organization directory
- Organization templates
- Bulk member management

### Phase 3 Features
- Organization analytics dashboard
- Advanced member permissions
- Organization branding customization
- Integration with external services
