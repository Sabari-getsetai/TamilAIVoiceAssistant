# Member Management

## Overview

The Tamil AI Voice Assistant provides comprehensive member management capabilities for organizations. This system enables organization administrators to invite, manage, and control access for team members within their organization, ensuring proper role-based access control and seamless collaboration.

## Member Lifecycle

### 1. Member Invitation

#### Invitation Process
- **Email Invitations**: Send invitations via email with secure invitation links
- **Role Assignment**: Assign specific roles during invitation (member, admin, owner)
- **Expiration**: Invitations expire after 7 days for security
- **Bulk Invitations**: Invite multiple members simultaneously

#### Invitation API
```typescript
// Send invitation
POST /api/organizations/{orgId}/invitations
{
  "email": "user@example.com",
  "role": "member",
  "message": "Welcome to our organization!"
}

// Bulk invitations
POST /api/organizations/{orgId}/invitations/bulk
{
  "invitations": [
    { "email": "user1@example.com", "role": "member" },
    { "email": "user2@example.com", "role": "admin" }
  ]
}
```

### 2. Member Onboarding

#### Invitation Acceptance
- **Secure Links**: Unique invitation codes for each invitation
- **Account Creation**: New users can create accounts during invitation acceptance
- **Existing Users**: Existing users are automatically added to the organization
- **Welcome Flow**: Guided onboarding process for new members

#### Onboarding Components
```typescript
// Invitation acceptance page
/org/join/[inviteCode]

// Welcome flow for new members
/org/[orgId]/welcome
```

### 3. Member Management

#### Member Roles
- **Owner**: Full organization control, can delete organization
- **Admin**: Member management, organization settings, billing
- **Member**: Standard access to organization features

#### Role Permissions Matrix
| Permission | Owner | Admin | Member |
|------------|-------|-------|--------|
| View organization | ✓ | ✓ | ✓ |
| Use chat/voice features | ✓ | ✓ | ✓ |
| Upload documents | ✓ | ✓ | ✓ |
| View analytics | ✓ | ✓ | ✗ |
| Invite members | ✓ | ✓ | ✗ |
| Manage members | ✓ | ✓ | ✗ |
| Change member roles | ✓ | ✓ | ✗ |
| Remove members | ✓ | ✓ | ✗ |
| Organization settings | ✓ | ✓ | ✗ |
| Billing management | ✓ | ✓ | ✗ |
| Delete organization | ✓ | ✗ | ✗ |

## Frontend Components

### 1. Member List Component

```typescript
// app/nextjs/src/components/organization/MemberList.tsx
interface MemberListProps {
  organizationId: string;
  currentUserRole: OrganizationRole;
}

function MemberList({ organizationId, currentUserRole }: MemberListProps) {
  const { members, loading, error } = useMembers(organizationId);
  const { inviteMember, removeMember, updateMemberRole } = useMemberActions();

  return (
    <div>
      <MemberTable 
        members={members}
        onRoleChange={updateMemberRole}
        onRemove={removeMember}
        canManage={currentUserRole === 'owner' || currentUserRole === 'admin'}
      />
      <InviteMemberDialog onInvite={inviteMember} />
    </div>
  );
}
```

### 2. Member Invitation Dialog

```typescript
// app/nextjs/src/components/organization/InviteMemberDialog.tsx
interface InviteMemberDialogProps {
  open: boolean;
  onClose: () => void;
  onInvite: (invitation: MemberInvitation) => Promise<void>;
}

function InviteMemberDialog({ open, onClose, onInvite }: InviteMemberDialogProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<OrganizationRole>('member');
  const [message, setMessage] = useState('');

  const handleSubmit = async () => {
    await onInvite({ email, role, message });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Invite Member</DialogTitle>
      <DialogContent>
        <TextField
          label="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
          margin="normal"
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Role</InputLabel>
          <Select value={role} onChange={(e) => setRole(e.target.value)}>
            <MenuItem value="member">Member</MenuItem>
            <MenuItem value="admin">Admin</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Welcome Message (Optional)"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          multiline
          rows={3}
          fullWidth
          margin="normal"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          Send Invitation
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

### 3. Member Management Hooks

```typescript
// app/nextjs/src/hooks/useMembers.ts
export function useMembers(organizationId: string) {
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMembers();
  }, [organizationId]);

  const fetchMembers = async () => {
    try {
      setLoading(true);
      const response = await organizationApi.getMembers(organizationId);
      setMembers(response.data);
    } catch (err) {
      setError('Failed to fetch members');
    } finally {
      setLoading(false);
    }
  };

  return { members, loading, error, refetch: fetchMembers };
}

export function useMemberActions() {
  const inviteMember = async (organizationId: string, invitation: MemberInvitation) => {
    return await organizationApi.inviteMember(organizationId, invitation);
  };

  const removeMember = async (organizationId: string, memberId: string) => {
    return await organizationApi.removeMember(organizationId, memberId);
  };

  const updateMemberRole = async (
    organizationId: string, 
    memberId: string, 
    role: OrganizationRole
  ) => {
    return await organizationApi.updateMemberRole(organizationId, memberId, role);
  };

  return { inviteMember, removeMember, updateMemberRole };
}
```

## Backend API Endpoints

### Member Management Endpoints

```python
# backend/api/organization.py

@router.get("/organizations/{org_id}/members")
async def get_organization_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all members of an organization"""
    # Verify user is member of organization
    membership = get_user_organization_membership(db, current_user.id, org_id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    members = get_organization_members(db, org_id)
    return {"members": members}

@router.post("/organizations/{org_id}/invitations")
async def invite_member(
    org_id: str,
    invitation: MemberInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a new member to the organization"""
    # Verify user has admin access
    membership = get_user_organization_membership(db, current_user.id, org_id)
    if not membership or membership.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Create invitation
    invitation_code = generate_invitation_code()
    invitation_record = create_member_invitation(
        db, org_id, invitation.email, invitation.role, invitation_code
    )
    
    # Send invitation email
    await send_invitation_email(invitation.email, invitation_code, org_id)
    
    return {"invitation_id": invitation_record.id, "message": "Invitation sent"}

@router.post("/organizations/{org_id}/invitations/bulk")
async def bulk_invite_members(
    org_id: str,
    bulk_invitation: BulkMemberInvitation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite multiple members to the organization"""
    # Verify user has admin access
    membership = get_user_organization_membership(db, current_user.id, org_id)
    if not membership or membership.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = []
    for invitation in bulk_invitation.invitations:
        try:
            invitation_code = generate_invitation_code()
            invitation_record = create_member_invitation(
                db, org_id, invitation.email, invitation.role, invitation_code
            )
            await send_invitation_email(invitation.email, invitation_code, org_id)
            results.append({"email": invitation.email, "status": "sent"})
        except Exception as e:
            results.append({"email": invitation.email, "status": "failed", "error": str(e)})
    
    return {"results": results}

@router.delete("/organizations/{org_id}/members/{member_id}")
async def remove_member(
    org_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization"""
    # Verify user has admin access
    membership = get_user_organization_membership(db, current_user.id, org_id)
    if not membership or membership.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Cannot remove yourself
    if member_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    
    # Remove member
    remove_organization_member(db, org_id, member_id)
    return {"message": "Member removed successfully"}

@router.put("/organizations/{org_id}/members/{member_id}/role")
async def update_member_role(
    org_id: str,
    member_id: str,
    role_update: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a member's role in the organization"""
    # Verify user has admin access
    membership = get_user_organization_membership(db, current_user.id, org_id)
    if not membership or membership.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Only owners can assign owner role
    if role_update.role == 'owner' and membership.role != 'owner':
        raise HTTPException(status_code=403, detail="Only owners can assign owner role")
    
    # Update member role
    update_organization_member_role(db, org_id, member_id, role_update.role)
    return {"message": "Member role updated successfully"}
```

### Invitation Acceptance Endpoints

```python
@router.get("/invitations/{invitation_code}")
async def get_invitation_details(
    invitation_code: str,
    db: Session = Depends(get_db)
):
    """Get invitation details for display"""
    invitation = get_invitation_by_code(db, invitation_code)
    if not invitation or invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    organization = get_organization(db, invitation.organization_id)
    return {
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "description": organization.description
        },
        "role": invitation.role,
        "invited_by": invitation.invited_by_user.full_name
    }

@router.post("/invitations/{invitation_code}/accept")
async def accept_invitation(
    invitation_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept an organization invitation"""
    invitation = get_invitation_by_code(db, invitation_code)
    if not invitation or invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    # Check if user is already a member
    existing_membership = get_user_organization_membership(
        db, current_user.id, invitation.organization_id
    )
    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this organization")
    
    # Create membership
    membership = create_organization_membership(
        db, invitation.organization_id, current_user.id, invitation.role
    )
    
    # Mark invitation as accepted
    mark_invitation_accepted(db, invitation.id)
    
    return {"message": "Invitation accepted", "organization_id": invitation.organization_id}
```

## Email Templates

### Invitation Email Template

```html
<!-- templates/invitation_email.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Organization Invitation</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1>You're Invited to Join {{ organization_name }}</h1>
        
        <p>Hello,</p>
        
        <p>{{ invited_by_name }} has invited you to join <strong>{{ organization_name }}</strong> 
           as a {{ role }} on the Tamil AI Voice Assistant platform.</p>
        
        {% if custom_message %}
        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Personal message:</strong></p>
            <p>{{ custom_message }}</p>
        </div>
        {% endif %}
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ invitation_url }}" 
               style="background: #007bff; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Accept Invitation
            </a>
        </div>
        
        <p><strong>What you'll get access to:</strong></p>
        <ul>
            <li>AI-powered chat and voice assistant in Tamil</li>
            <li>Document upload and knowledge base features</li>
            <li>Collaborative workspace with your team</li>
            <li>Analytics and usage insights</li>
        </ul>
        
        <p><small>This invitation will expire in 7 days. If you don't have an account yet, 
           you can create one when accepting the invitation.</small></p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        
        <p><small>If you're having trouble with the button above, copy and paste this link into your browser:</small></p>
        <p><small>{{ invitation_url }}</small></p>
        
        <p><small>This email was sent to {{ recipient_email }}. If you believe this was sent in error, 
           please ignore this email.</small></p>
    </div>
</body>
</html>
```

## Security Considerations

### Invitation Security
- **Unique Codes**: Each invitation has a unique, cryptographically secure code
- **Expiration**: Invitations automatically expire after 7 days
- **Single Use**: Invitations can only be accepted once
- **Email Verification**: Invitations are tied to specific email addresses

### Access Control
- **Role Validation**: Strict validation of role assignments and changes
- **Permission Checks**: All member management operations require appropriate permissions
- **Audit Logging**: All member management actions are logged for security

### Data Protection
- **Member Privacy**: Member information is only visible to organization admins
- **Secure Deletion**: Proper cleanup when members are removed
- **GDPR Compliance**: Support for data export and deletion requests

## Usage Examples

### Inviting Members

```typescript
import { useMemberActions } from '@/hooks/useMembers';

function InviteMemberExample() {
  const { inviteMember } = useMemberActions();

  const handleInvite = async () => {
    try {
      await inviteMember('org-123', {
        email: 'newmember@example.com',
        role: 'member',
        message: 'Welcome to our team!'
      });
      // Show success message
    } catch (error) {
      // Handle error
    }
  };

  return (
    <button onClick={handleInvite}>
      Invite Member
    </button>
  );
}
```

### Managing Member Roles

```typescript
import { useMembers, useMemberActions } from '@/hooks/useMembers';

function MemberManagementExample() {
  const { members } = useMembers('org-123');
  const { updateMemberRole, removeMember } = useMemberActions();

  const handleRoleChange = async (memberId: string, newRole: string) => {
    await updateMemberRole('org-123', memberId, newRole);
  };

  const handleRemoveMember = async (memberId: string) => {
    if (confirm('Are you sure you want to remove this member?')) {
      await removeMember('org-123', memberId);
    }
  };

  return (
    <div>
      {members.map(member => (
        <div key={member.id}>
          <span>{member.user.full_name}</span>
          <select 
            value={member.role} 
            onChange={(e) => handleRoleChange(member.id, e.target.value)}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="owner">Owner</option>
          </select>
          <button onClick={() => handleRemoveMember(member.id)}>
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}
```

## Testing

### Manual Testing Checklist
- [ ] Send member invitation with valid email
- [ ] Send invitation with invalid email format
- [ ] Accept invitation with new user account
- [ ] Accept invitation with existing user account
- [ ] Try to accept expired invitation
- [ ] Try to accept invitation twice
- [ ] Update member role (admin to member, member to admin)
- [ ] Remove member from organization
- [ ] Try to remove yourself from organization
- [ ] Bulk invite multiple members
- [ ] Test permission restrictions for different roles

### API Testing
```bash
# Test invitation endpoints
curl -X POST "http://localhost:8000/api/organizations/org-123/invitations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "role": "member"}'

# Test member management
curl -X GET "http://localhost:8000/api/organizations/org-123/members" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Common Issues

**Issue: Invitation emails not being sent**
- Check email service configuration
- Verify SMTP settings in environment variables
- Check email service logs for errors

**Issue: Invitation links not working**
- Verify invitation code is valid and not expired
- Check frontend routing for invitation acceptance page
- Ensure invitation URL is correctly formatted

**Issue: Permission denied when managing members**
- Verify user has admin or owner role in organization
- Check authentication token is valid
- Ensure organization membership is active

**Issue: Cannot remove organization owner**
- Only owners can transfer ownership to another member
- Must have at least one owner in organization
- Transfer ownership before removing current owner

## Future Enhancements

1. **Advanced Permissions**
   - Custom role definitions
   - Granular permission settings
   - Department-based access control

2. **Member Analytics**
   - Member activity tracking
   - Usage statistics per member
   - Performance metrics

3. **Integration Features**
   - SCIM provisioning support
   - Active Directory integration
   - SSO-based member management

4. **User Experience**
   - Member onboarding workflows
   - Interactive tutorials for new members
   - Mobile app member management

## Related Documentation

- [Organization Management](./organization-management.md)
- [Authentication System](./authentication.md)
- [Organization API Documentation](../api/organization-api.md)
- [Security Best Practices](../reference/security.md)
- [Email Configuration](../setup/email-configuration.md)
