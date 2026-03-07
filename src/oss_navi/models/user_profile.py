"""User profile models for GitHub data."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Language(BaseModel):
    """Programming language statistics."""

    name: str
    bytes: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=1.0)


class Activity(BaseModel):
    """Recent GitHub activity entry."""

    type: str
    repo_name: str
    created_at: datetime
    details: Optional[dict[str, Any]] = None


class Repository(BaseModel):
    """GitHub repository information."""

    name: str
    url: str
    stars: int = Field(ge=0)
    language: Optional[str] = None
    description: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    is_archived: bool = False
    last_updated: Optional[datetime] = None


class UserProfile(BaseModel):
    """GitHub user profile data."""

    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = Field(ge=0)
    followers: int = Field(ge=0)
    following: int = Field(ge=0)
    languages: dict[str, float] = Field(default_factory=dict)
    recent_activity: list[Activity] = Field(default_factory=list)
    top_repos: list[Repository] = Field(default_factory=list)
    fetched_at: datetime
    expires_at: datetime
