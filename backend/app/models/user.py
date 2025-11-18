"""
User models for authentication and user management.

Uses Supabase Auth for authentication, these models represent the user data.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model with common attributes."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class UserUpdate(BaseModel):
    """Model for updating user information."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class User(UserBase):
    """User model for API responses."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # User statistics
    total_documents: int = 0
    total_queries: int = 0

    model_config = {"from_attributes": True}


class UserInDB(User):
    """User model as stored in database (includes sensitive data)."""
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None


class UserSettings(BaseModel):
    """User preferences and settings."""
    user_id: UUID
    preferences: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    # Example preferences:
    # {
    #     "theme": "dark",
    #     "language": "en",
    #     "notifications_enabled": true,
    #     "default_top_k": 5,
    #     "default_include_sources": true
    # }

    model_config = {"from_attributes": True}


class UserStats(BaseModel):
    """User statistics and usage metrics."""
    user_id: UUID
    total_documents: int = 0
    total_queries: int = 0
    total_storage_bytes: int = 0
    documents_by_type: dict = Field(default_factory=dict)
    recent_activity: list = Field(default_factory=list)
    created_at: datetime
