"""Recommendation models for intelligent project suggestions."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from oss_navi.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    pass


class RecommendationMode(StrEnum):
    """Recommendation algorithm mode with different trade-offs."""

    FAST = "fast"  # Content-based only, <30s
    NORMAL = "normal"  # Enhanced content-based, <60s
    THINKING = "thinking"  # LightFM + Apriori, <180s


class ModeConfig(BaseModel):
    """Configuration for a recommendation mode."""

    mode: RecommendationMode = Field(..., description="The recommendation mode")
    max_time_seconds: int = Field(..., description="Maximum time allowed for recommendations")
    max_memory_mb: int = Field(..., description="Maximum memory allowed in MB")
    algorithms: list[str] = Field(..., description="Algorithms used in this mode")
    requires_numpy: bool = Field(default=False, description="Whether numpy is required")
    requires_lightfm: bool = Field(default=False, description="Whether LightFM is required")


# Predefined configurations for each mode
MODE_CONFIGS: dict[RecommendationMode, ModeConfig] = {
    RecommendationMode.FAST: ModeConfig(
        mode=RecommendationMode.FAST,
        max_time_seconds=30,
        max_memory_mb=50,
        algorithms=["content_based"],
        requires_numpy=False,
        requires_lightfm=False,
    ),
    RecommendationMode.NORMAL: ModeConfig(
        mode=RecommendationMode.NORMAL,
        max_time_seconds=60,
        max_memory_mb=100,
        algorithms=["enhanced_content_based", "similarity_clustering"],
        requires_numpy=False,
        requires_lightfm=False,
    ),
    RecommendationMode.THINKING: ModeConfig(
        mode=RecommendationMode.THINKING,
        max_time_seconds=180,
        max_memory_mb=500,
        algorithms=["lightfm", "apriori"],
        requires_numpy=True,
        requires_lightfm=True,
    ),
}


def get_mode_config(mode: RecommendationMode) -> ModeConfig:
    """Get configuration for a recommendation mode."""
    return MODE_CONFIGS[mode]


def check_mode_availability(mode: RecommendationMode) -> tuple[bool, list[str]]:
    """Check if a mode's dependencies are available.

    Returns:
        Tuple of (is_available, missing_dependencies)
    """
    config = MODE_CONFIGS[mode]
    missing = []

    if config.requires_numpy:
        try:
            import numpy  # noqa: F401
        except ImportError:
            missing.append("numpy")

    if config.requires_lightfm:
        try:
            from lightfm import LightFM  # noqa: F401
        except ImportError:
            missing.append("lightfm")

    return len(missing) == 0, missing


class Recommendation(BaseModel):
    """A single project recommendation with reasoning and skill analysis."""

    recommendation_id: str = Field(..., description="Unique identifier for this recommendation")
    project_name: str = Field(..., description="Full project name (owner/repo)")
    project_url: str = Field(..., description="GitHub URL for the project")
    language: str = Field(..., description="Primary programming language")
    relevance_score: int = Field(..., ge=1, le=10, description="Relevance score on 1-10 scale")
    reasoning: str = Field(..., description="Why this project matches the user")
    skill_gap_analysis: list[str] = Field(
        default_factory=list, description="Skills the user will develop"
    )
    learning_prerequisites: list[str] = Field(
        default_factory=list, description="Prerequisites if language not matched"
    )
    issue_url: str | None = Field(None, description="URL to a good first issue")
    issue_title: str | None = Field(None, description="Title of the suggested issue")
    stars: int = Field(default=0, description="Number of GitHub stars")
    is_great_project: bool = Field(
        default=False, description="True for 'great projects' section"
    )
    algorithm_source: str = Field(..., description="Which algorithm generated this")
    mode: RecommendationMode = Field(..., description="Which mode generated this")
    confidence_score: float | None = Field(
        None, ge=0.0, le=1.0, description="Algorithm confidence (0.0-1.0)"
    )
    generated_at: datetime = Field(default_factory=utc_now, description="When this was generated")

    def to_markdown(self) -> str:
        """Convert recommendation to markdown format."""
        lines = [
            f"### {self.project_name} (Score: {self.relevance_score}/10",
        ]
        if self.confidence_score is not None:
            lines[0] += f", Confidence: {self.confidence_score:.2f}"
        lines[0] += ")"

        lines.extend([
            f"- **URL**: {self.project_url}",
            f"- **Language**: {self.language} | Stars: {self.stars:,}",
            f"- **Why**: {self.reasoning}",
        ])

        if self.skill_gap_analysis:
            lines.append(f"- **Skills you'll develop**: {', '.join(self.skill_gap_analysis)}")

        if self.learning_prerequisites:
            lines.append(f"- **Prerequisites**: {', '.join(self.learning_prerequisites)}")

        if self.issue_url and self.issue_title:
            lines.append(f"- **Issue**: [{self.issue_title}]({self.issue_url})")

        lines.append(f"- **Algorithm**: {self.algorithm_source} ({self.mode.value} mode)")

        return "\n".join(lines)


class RecommendationPattern(BaseModel):
    """A discovered association between skills, languages, and successful contributions."""

    pattern_id: str = Field(..., description="Unique identifier for this pattern")
    antecedent: list[str] = Field(
        ..., description="Input conditions, e.g., ['python', 'web']"
    )
    consequent: list[str] = Field(
        ..., description="Recommended items, e.g., ['django', 'fastapi']"
    )
    support: float = Field(..., ge=0.0, le=1.0, description="Frequency of pattern")
    confidence: float = Field(..., ge=0.0, le=1.0, description="P(consequent | antecedent)")
    algorithm: str = Field(..., description="Algorithm used: 'apriori' or 'fpgrowth'")
    created_at: datetime = Field(default_factory=utc_now, description="When pattern was discovered")

    def to_dict(self) -> dict:
        """Convert pattern to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "antecedent": self.antecedent,
            "consequent": self.consequent,
            "support": self.support,
            "confidence": self.confidence,
            "algorithm": self.algorithm,
            "created_at": self.created_at.isoformat(),
        }
