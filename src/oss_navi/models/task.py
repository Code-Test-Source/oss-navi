"""Task models for open source contribution opportunities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Repository(BaseModel):
    """GitHub repository information for a task."""

    name: str
    url: str
    stars: int = Field(ge=0)
    language: Optional[str] = None
    description: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    is_archived: bool = False
    last_updated: Optional[datetime] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is a well-formed GitHub URL."""
        if not v.startswith("https://github.com/"):
            raise ValueError("URL must be a valid GitHub URL (https://github.com/...)")
        return v


class Task(BaseModel):
    """Open source contribution opportunity."""

    id: str
    title: str
    description: Optional[str] = Field(default=None, max_length=500)
    url: str
    source: str  # "upforgrabs" or "goodfirstissue"
    repository: Repository
    labels: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    hotness_score: float = Field(ge=0.0)
    fetched_at: datetime

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is a well-formed GitHub URL."""
        if not v.startswith("https://github.com/"):
            raise ValueError("URL must be a valid GitHub URL (https://github.com/...)")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate that source is one of the allowed values."""
        allowed = {"upforgrabs", "goodfirstissue", "goodfirstissues"}
        if v not in allowed:
            raise ValueError(f"Source must be one of: {', '.join(allowed)}")
        return v


def calculate_hotness_score(stars: int, age_in_days: int) -> float:
    """Calculate hotness score: stars / age_in_days.

    Higher score = more popular and newer issue.
    """
    if age_in_days <= 0:
        age_in_days = 1
    return round(stars / age_in_days, 2)
