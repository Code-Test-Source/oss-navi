"""User profile models for GitHub data."""

from datetime import datetime
from typing import Any

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
    details: dict[str, Any] | None = None


class Repository(BaseModel):
    """GitHub repository information."""

    name: str
    url: str
    stars: int = Field(ge=0)
    language: str | None = None
    description: str | None = None
    topics: list[str] = Field(default_factory=list)
    is_archived: bool = False
    last_updated: datetime | None = None


class UserProfile(BaseModel):
    """GitHub user profile data."""

    username: str
    name: str | None = None
    bio: str | None = None
    public_repos: int = Field(ge=0)
    followers: int = Field(ge=0)
    following: int = Field(ge=0)
    languages: dict[str, float] = Field(default_factory=dict)
    recent_activity: list[Activity] = Field(default_factory=list)
    top_repos: list[Repository] = Field(default_factory=list)
    fetched_at: datetime
    expires_at: datetime
