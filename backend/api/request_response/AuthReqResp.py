
"""Authentication and Authorization request/response schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from backend.database.models import UserRole, OrganizationRole

class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)

    @validator("username")
    def validate_username(cls, v):
        """Validate username format"""
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        return v.lower()

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """User login request schema"""
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds


class UserResponse(BaseModel):
    """User profile response schema"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class OrganizationCreateRequest(BaseModel):
    """Organization creation request schema"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: str = Field("startup", pattern="^(startup|small|medium|large|enterprise)$")
    timezone: str = Field("UTC", max_length=50)

    @validator("name")
    def validate_name(cls, v):
        """Validate organization name format"""
        if not v.strip():
            raise ValueError("Organization name cannot be empty")
        return v.strip()


class OrganizationResponse(BaseModel):
    """Organization response schema"""
    id: str
    name: str
    description: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    size: str
    timezone: str
    creator_id: str
    is_active: bool
    subscription_plan: str
    subscription_status: str
    created_at: datetime
    current_user_role: Optional[OrganizationRole] = None

    class Config:
        from_attributes = True


class SetActiveOrganizationRequest(BaseModel):
    """Set active organization request schema"""
    organization_id: str
