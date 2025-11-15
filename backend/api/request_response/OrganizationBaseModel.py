""""Organization base model schemas for request and response handling."""

from typing import Optional
from pydantic import BaseModel, Field

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    website: Optional[str] = Field(None, max_length=255, description="Organization website URL")
    industry: Optional[str] = Field(None, max_length=100, description="Industry type")
    size: str = Field("startup", description="Organization size")
    timezone: str = Field("UTC", description="Organization timezone")
    billing_email: Optional[str] = Field(None, max_length=255, description="Billing email address")