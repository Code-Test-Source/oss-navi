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


class PastRecommendation(BaseModel):
    """Record of a previous project recommendation."""

    date: datetime
    project: str  # Format: owner/repo
    issue_url: str
    reason: Optional[str] = None
    status: Optional[str] = None  # "viewed", "attempted", "completed"


class LongTermMemory(BaseModel):
    """Accumulated insights about the user's OSS journey."""

    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    skill_history: list[SkillSnapshot] = Field(default_factory=list)
    past_recommendations: list[PastRecommendation] = Field(default_factory=list)
    learning_goals: list[str] = Field(default_factory=list)

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
