"""Organization request and response models."""

from backend.api.request_response.OrganizationBaseModel import OrganizationBase

from typing import Optional

from pydantic import BaseModel, Field
from datetime import datetime
from backend.database.models import OrganizationRole

class CreateOrganizationRequest(OrganizationBase):
    """Request model for creating a new organization."""
    pass


class UpdateOrganizationRequest(BaseModel):
    """Request model for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = None
    timezone: Optional[str] = None
    billing_email: Optional[str] = Field(None, max_length=255)
    settings: Optional[dict] = None


class OrganizationResponse(BaseModel):
    """Response model for organization data."""
    id: str
    name: str
    description: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    size: str
    timezone: str
    is_active: bool
    settings: Optional[dict]
    billing_email: Optional[str]
    subscription_plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    user_role: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True  # Serialize enums as their values


class OrganizationMemberResponse(BaseModel):
    """Response model for organization member data."""
    id: str
    user_id: str
    username: str
    full_name: Optional[str]
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class SwitchOrganizationRequest(BaseModel):
    """Request model for switching active organization."""
    organization_id: str


class InviteMemberRequest(BaseModel):
    """Request model for inviting a new member."""
    email: str = Field(..., max_length=255, description="Email address of user to invite")
    role: OrganizationRole = Field(OrganizationRole.MEMBER, description="Role to assign to the new member")


class UpdateMemberRoleRequest(BaseModel):
    """Request model for updating a member's role."""
    role: OrganizationRole = Field(..., description="New role to assign to the member")


class RemoveMemberRequest(BaseModel):
    """Request model for removing a member from organization."""
    user_id: str = Field(..., description="ID of user to remove from organization")