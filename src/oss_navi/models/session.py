"""Session models for multi-round interactive recommendations."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from oss_navi.models.preferences import UserPreferences
from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    pass


class FeedbackType(StrEnum):
    """Type of user feedback on a recommendation."""

    ACCEPT = "accept"
    REJECT = "reject"
    REQUEST_ALTERNATIVE = "request_alternative"


class SectionType(StrEnum):
    """Type of report section."""

    RECOMMENDATION = "recommendation"
    CODE_ANALYSIS = "code_analysis"
    LEARNING_PATH = "learning_path"
    SUMMARY = "summary"
    CUSTOM = "custom"


class SessionStatus(StrEnum):
    """Status of a recommendation session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class UserFeedback(BaseModel):
    """User feedback on a specific recommendation."""

    recommendation_id: str = Field(..., description="ID of the recommendation")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    reason: str | None = Field(None, description="Optional reason for feedback")
    timestamp: datetime = Field(default_factory=utc_now, description="When feedback was given")


class RecommendationRound(BaseModel):
    """A single round of recommendations in a session."""

    round_number: int = Field(..., description="Round number (1-indexed)")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommendations in this round"
    )
    user_feedback: list[UserFeedback] = Field(
        default_factory=list, description="User feedback for this round"
    )
    selected_for_analysis: list[str] = Field(
        default_factory=list, description="Recommendation IDs selected for detailed analysis"
    )
    generated_at: datetime = Field(default_factory=utc_now, description="When round was generated")


class ReportSection(BaseModel):
    """A section of the interactive report."""

    section_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    section_type: SectionType = Field(..., description="Type of section")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Markdown content")
    order: int = Field(default=0, description="Display order")
    created_at: datetime = Field(default_factory=utc_now)
    modified_at: datetime = Field(default_factory=utc_now)

    def to_markdown(self) -> str:
        """Convert section to markdown."""
        return f"\n## {self.title}\n\n{self.content}\n"


class RecommendationSession(BaseModel):
    """A multi-round recommendation session."""

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique session identifier"
    )
    mode: RecommendationMode = Field(
        default=RecommendationMode.NORMAL,
        description="Recommendation mode for this session"
    )
    user_preferences: UserPreferences = Field(
        ..., description="User preferences for this session"
    )
    rounds: list[RecommendationRound] = Field(
        default_factory=list, description="Recommendation rounds"
    )
    report_sections: list[ReportSection] = Field(
        default_factory=list, description="Report sections"
    )
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Session status"
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def add_round(self, round_data: RecommendationRound) -> None:
        """Add a new recommendation round."""
        self.rounds.append(round_data)
        self.updated_at = utc_now()

    def add_feedback(self, feedback: UserFeedback) -> None:
        """Add user feedback to the current round."""
        if self.rounds:
            self.rounds[-1].user_feedback.append(feedback)
            self.updated_at = utc_now()

    def get_all_rejected_ids(self) -> set[str]:
        """Get IDs of all rejected recommendations."""
        rejected = set()
        for round_data in self.rounds:
            for feedback in round_data.user_feedback:
                if feedback.feedback_type == FeedbackType.REJECT:
                    rejected.add(feedback.recommendation_id)
        return rejected

    def get_all_accepted_ids(self) -> set[str]:
        """Get IDs of all accepted recommendations."""
        accepted = set()
        for round_data in self.rounds:
            for feedback in round_data.user_feedback:
                if feedback.feedback_type == FeedbackType.ACCEPT:
                    accepted.add(feedback.recommendation_id)
        return accepted

    def get_all_recommendations(self) -> list[Recommendation]:
        """Get all recommendations across all rounds."""
        all_recs = []
        for round_data in self.rounds:
            all_recs.extend(round_data.recommendations)
        return all_recs

    def get_recommendation_by_id(self, rec_id: str) -> Recommendation | None:
        """Get a recommendation by ID."""
        for rec in self.get_all_recommendations():
            if rec.recommendation_id == rec_id:
                return rec
        return None

    def add_report_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        section.order = len(self.report_sections)
        self.report_sections.append(section)
        self.updated_at = utc_now()

    def remove_report_section(self, section_id: str) -> bool:
        """Remove a section from the report."""
        for i, section in enumerate(self.report_sections):
            if section.section_id == section_id:
                self.report_sections.pop(i)
                self.updated_at = utc_now()
                return True
        return False

    def reorder_sections(self, section_ids: list[str]) -> None:
        """Reorder report sections."""
        id_to_section = {s.section_id: s for s in self.report_sections}
        self.report_sections = []
        for order, section_id in enumerate(section_ids):
            if section_id in id_to_section:
                id_to_section[section_id].order = order
                self.report_sections.append(id_to_section[section_id])
        self.updated_at = utc_now()

    def get_current_round_number(self) -> int:
        """Get the current round number."""
        return len(self.rounds)

    def is_max_rounds_reached(self, max_rounds: int = 3) -> bool:
        """Check if maximum rounds reached."""
        return len(self.rounds) >= max_rounds

    def finalize(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.updated_at = utc_now()

    def abandon(self) -> None:
        """Mark session as abandoned."""
        self.status = SessionStatus.ABANDONED
        self.updated_at = utc_now()

    def to_markdown_report(self) -> str:
        """Generate full markdown report."""
        lines = [
            "# OSS-Navi Analysis Report",
            "",
            f"**Session**: {self.session_id}",
            f"**Mode**: {self.mode.value}",
            f"**Status**: {self.status.value}",
            f"**Rounds**: {len(self.rounds)}",
            "",
        ]

        # Add report sections
        for section in sorted(self.report_sections, key=lambda s: s.order):
            lines.append(section.to_markdown())

        # Add accepted recommendations summary
        accepted_ids = self.get_all_accepted_ids()
        if accepted_ids:
            lines.append("\n## Accepted Recommendations\n")
            for rec in self.get_all_recommendations():
                if rec.recommendation_id in accepted_ids:
                    lines.append(f"- [{rec.project_name}]({rec.project_url})")

        return "\n".join(lines)
