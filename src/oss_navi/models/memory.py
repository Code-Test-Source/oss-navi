"""Long-term memory models for tracking user's OSS journey."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillSnapshot(BaseModel):
    """Point-in-time skill assessment."""

    date: datetime
    languages: dict[str, float] = Field(default_factory=dict)
    top_repos: list[str] = Field(default_factory=list, max_length=5)
    focus_areas: list[str] = Field(default_factory=list)


class GitHubProfileSummary(BaseModel):
    """Cached summary of user's GitHub profile for quick reference."""

    username: str
    primary_languages: dict[str, float] = Field(default_factory=dict)
    total_repos: int = 0
    last_fetched: datetime


class PastRecommendation(BaseModel):
    """Record of a previous project recommendation."""

    date: datetime
    project: str  # Format: owner/repo
    issue_url: str
    reason: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    status: Optional[str] = None  # "viewed", "attempted", "completed"


class GreatProjectSummary(BaseModel):
    """Brief record of a great project shown to user."""

    name: str
    shown_at: datetime
    reason: str


class FieldExploration(BaseModel):
    """Record of field exploration advice given."""

    date: datetime
    current_interest: str
    suggested_fields: list[str] = Field(default_factory=list)
    rationale: str


class LongTermMemory(BaseModel):
    """Accumulated insights about the user's OSS journey."""

    version: int = Field(default=3, ge=1)  # Version 3 with new fields
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    skill_history: list[SkillSnapshot] = Field(default_factory=list)
    past_recommendations: list[PastRecommendation] = Field(default_factory=list)
    learning_goals: list[str] = Field(default_factory=list)
    great_projects_discovered: list[GreatProjectSummary] = Field(default_factory=list)
    field_exploration_history: list[FieldExploration] = Field(default_factory=list)
    # NEW fields for enhanced memory
    github_profile: Optional[GitHubProfileSummary] = None
    last_analysis_date: Optional[datetime] = None
    analysis_count: int = 0

    def add_skill_snapshot(self, snapshot: SkillSnapshot) -> None:
        """Add a new skill snapshot to history."""
        self.skill_history.append(snapshot)
        self.updated_at = datetime.now()

    def add_recommendation(self, recommendation: PastRecommendation) -> None:
        """Add a new recommendation to history."""
        self.past_recommendations.append(recommendation)
        self.updated_at = datetime.now()

    def add_learning_goal(self, goal: str) -> None:
        """Add a learning goal if not already present."""
        if goal and goal not in self.learning_goals:
            self.learning_goals.append(goal)
            self.updated_at = datetime.now()

    def add_great_project(self, summary: GreatProjectSummary) -> None:
        """Add a great project to discovered history."""
        self.great_projects_discovered.append(summary)
        self.updated_at = datetime.now()

    def add_field_exploration(self, exploration: FieldExploration) -> None:
        """Add field exploration advice to history."""
        self.field_exploration_history.append(exploration)
        self.updated_at = datetime.now()
