"""Task models for open source contribution opportunities."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


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
    source: str  # "upforgrabs" or "goodfirstissues"
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
        allowed = {"upforgrabs", "goodfirstissues"}
        if v not in allowed:
            raise ValueError(f"Source must be one of: {', '.join(allowed)}")
        return v


class IssueStatus(BaseModel):
    """Real-time status of an issue (checked on-demand, not cached)."""

    issue_url: str
    is_assigned: bool
    assignee: Optional[str] = None
    is_closed: bool
    has_linked_pr: bool
    has_open_pr: bool = False  # NEW: Has separate open PR linked via timeline
    linked_pr_url: Optional[str] = None  # NEW: URL of linked PR if has_open_pr is true
    in_progress_labels: list[str] = Field(default_factory=list)
    checked_at: datetime

    @property
    def is_available(self) -> bool:
        """Check if issue is available for contribution."""
        return (
            not self.is_assigned
            and not self.is_closed
            and not self.has_linked_pr
            and not self.has_open_pr  # NEW condition
        )


class RatingBreakdown(BaseModel):
    """Detailed scoring components for a recommendation.

    Weights: language_match (30%), hotness (20%), availability (15%),
    learning (15%), skill (10%), topic (10%)
    """

    language_match: float = Field(ge=0.0, le=10.0)
    hotness_score: float = Field(ge=0.0, le=10.0)
    issue_availability: float = Field(ge=0.0, le=10.0)
    learning_alignment: float = Field(ge=0.0, le=10.0)
    skill_level_fit: float = Field(ge=0.0, le=10.0)
    topic_relevance: float = Field(ge=0.0, le=10.0)

    @model_validator(mode="after")
    def calculate_weighted_total(self) -> "RatingBreakdown":
        """Calculate and set the weighted total score."""
        self.weighted_total = round(
            self.language_match * 0.30
            + self.hotness_score * 0.20
            + self.issue_availability * 0.15
            + self.learning_alignment * 0.15
            + self.skill_level_fit * 0.10
            + self.topic_relevance * 0.10,
            2,
        )
        return self

    weighted_total: float = Field(default=0.0, ge=0.0, le=10.0)


class Recommendation(BaseModel):
    """A scored recommendation for a specific task/issue."""

    task: Task
    rating: float = Field(ge=1.0, le=10.0)
    rating_breakdown: RatingBreakdown
    reason: str = Field(min_length=10)  # Why this fits the user
    code_analysis: str = Field(min_length=10)  # Brief analysis of project
    status: IssueStatus


class GreatProject(BaseModel):
    """An excellent open source project for learning (not necessarily beginner-friendly)."""

    name: str
    url: str
    stars: int = Field(ge=0)
    language: str
    why_great: str  # Why this is a great project to study
    architecture_overview: str
    key_patterns: list[str] = Field(default_factory=list)
    contribution_areas: list[str] = Field(default_factory=list)
    relevance_reason: str  # Why relevant to user's skills/goals

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is a valid GitHub URL."""
        if not v.startswith("https://github.com/"):
            raise ValueError("URL must be a valid GitHub URL (https://github.com/...)")
        return v


class LearningSession(BaseModel):
    """Captured during interactive analysis."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    primary_interest: str  # What user is currently learning
    explore_fields: list[str] = Field(default_factory=list)
    suggested_fields: list[str] = Field(default_factory=list)


def calculate_hotness_score(stars: int, age_in_days: int) -> float:
    """Calculate hotness score: stars / age_in_days.

    Higher score = more popular and newer issue.
    """
    if age_in_days <= 0:
        age_in_days = 1
    return round(stars / age_in_days, 2)
