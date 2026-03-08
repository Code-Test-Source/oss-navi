"""Tests for session models."""

import pytest

from oss_navi.models.preferences import LanguageProfile, LanguageType, SkillLevel, UserPreferences
from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.models.session import (
    FeedbackType,
    RecommendationRound,
    RecommendationSession,
    ReportSection,
    SectionType,
    SessionStatus,
    UserFeedback,
)


class TestFeedbackType:
    """Tests for FeedbackType enum."""

    def test_feedback_type_values(self) -> None:
        """Test FeedbackType enum values."""
        assert FeedbackType.ACCEPT.value == "accept"
        assert FeedbackType.REJECT.value == "reject"
        assert FeedbackType.REQUEST_ALTERNATIVE.value == "request_alternative"


class TestSectionType:
    """Tests for SectionType enum."""

    def test_section_type_values(self) -> None:
        """Test SectionType enum values."""
        assert SectionType.RECOMMENDATION.value == "recommendation"
        assert SectionType.CODE_ANALYSIS.value == "code_analysis"
        assert SectionType.LEARNING_PATH.value == "learning_path"
        assert SectionType.SUMMARY.value == "summary"
        assert SectionType.CUSTOM.value == "custom"


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_session_status_values(self) -> None:
        """Test SessionStatus enum values."""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ABANDONED.value == "abandoned"


class TestUserFeedback:
    """Tests for UserFeedback model."""

    def test_create_user_feedback(self) -> None:
        """Test creating a UserFeedback."""
        feedback = UserFeedback(
            recommendation_id="rec-123",
            feedback_type=FeedbackType.ACCEPT,
            reason="Good match",
        )
        assert feedback.recommendation_id == "rec-123"
        assert feedback.feedback_type == FeedbackType.ACCEPT

    def test_user_feedback_auto_timestamp(self) -> None:
        """Test that timestamp is auto-generated."""
        feedback = UserFeedback(
            recommendation_id="rec-123",
            feedback_type=FeedbackType.REJECT,
        )
        assert feedback.timestamp is not None


class TestRecommendationRound:
    """Tests for RecommendationRound model."""

    def test_create_round(self) -> None:
        """Test creating a RecommendationRound."""
        round_data = RecommendationRound(
            round_number=1,
            recommendations=[
                Recommendation(
                    recommendation_id="rec-123",
                    project_name="owner/repo",
                    project_url="https://github.com/owner/repo",
                    language="Python",
                    relevance_score=8,
                    reasoning="Good match",
                    algorithm_source="content_based",
                    mode=RecommendationMode.FAST,
                ),
            ],
        )
        assert round_data.round_number == 1
        assert len(round_data.recommendations) == 1

    def test_round_defaults(self) -> None:
        """Test RecommendationRound defaults."""
        round_data = RecommendationRound(round_number=1)
        assert round_data.recommendations == []
        assert round_data.user_feedback == []
        assert round_data.selected_for_analysis == []


class TestReportSection:
    """Tests for ReportSection model."""

    def test_create_section(self) -> None:
        """Test creating a ReportSection."""
        section = ReportSection(
            section_type=SectionType.RECOMMENDATION,
            title="Top Recommendations",
            content="1. Project A\n2. Project B",
            order=1,
        )
        assert section.title == "Top Recommendations"
        assert section.order == 1

    def test_to_markdown(self) -> None:
        """Test to_markdown method."""
        section = ReportSection(
            section_type=SectionType.CUSTOM,
            title="Notes",
            content="Some important notes here.",
        )
        md = section.to_markdown()
        assert "## Notes" in md
        assert "Some important notes here" in md


class TestRecommendationSession:
    """Tests for RecommendationSession model."""

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[
                LanguageProfile(
                    language="python",
                    type=LanguageType.PRIMARY,
                    skill_level=SkillLevel.ADVANCED,
                ),
            ],
        )

    @pytest.fixture
    def sample_session(self, user_prefs: UserPreferences) -> RecommendationSession:
        """Create a test session."""
        return RecommendationSession(
            user_preferences=user_prefs,
            mode=RecommendationMode.FAST,
        )

    def test_create_session(self, user_prefs: UserPreferences) -> None:
        """Test creating a RecommendationSession."""
        session = RecommendationSession(user_preferences=user_prefs)
        assert session.status == SessionStatus.ACTIVE
        assert len(session.session_id) == 8

    def test_add_round(self, sample_session: RecommendationSession) -> None:
        """Test add_round method."""
        round_data = RecommendationRound(round_number=1)
        sample_session.add_round(round_data)
        assert len(sample_session.rounds) == 1

    def test_add_feedback(self, sample_session: RecommendationSession) -> None:
        """Test add_feedback method."""
        # Add a round first
        round_data = RecommendationRound(round_number=1)
        sample_session.add_round(round_data)

        # Add feedback
        feedback = UserFeedback(
            recommendation_id="rec-1",
            feedback_type=FeedbackType.ACCEPT,
        )
        sample_session.add_feedback(feedback)
        assert len(sample_session.rounds[0].user_feedback) == 1

    def test_get_all_rejected_ids(self, sample_session: RecommendationSession) -> None:
        """Test get_all_rejected_ids method."""
        round_data = RecommendationRound(
            round_number=1,
            user_feedback=[
                UserFeedback(
                    recommendation_id="rec-1",
                    feedback_type=FeedbackType.REJECT,
                ),
                UserFeedback(
                    recommendation_id="rec-2",
                    feedback_type=FeedbackType.ACCEPT,
                ),
                UserFeedback(
                    recommendation_id="rec-3",
                    feedback_type=FeedbackType.REJECT,
                ),
            ],
        )
        sample_session.add_round(round_data)
        rejected = sample_session.get_all_rejected_ids()
        assert rejected == {"rec-1", "rec-3"}

    def test_get_all_accepted_ids(self, sample_session: RecommendationSession) -> None:
        """Test get_all_accepted_ids method."""
        round_data = RecommendationRound(
            round_number=1,
            user_feedback=[
                UserFeedback(
                    recommendation_id="rec-1",
                    feedback_type=FeedbackType.ACCEPT,
                ),
                UserFeedback(
                    recommendation_id="rec-2",
                    feedback_type=FeedbackType.REJECT,
                ),
            ],
        )
        sample_session.add_round(round_data)
        accepted = sample_session.get_all_accepted_ids()
        assert accepted == {"rec-1"}

    def test_get_all_recommendations(self, sample_session: RecommendationSession) -> None:
        """Test get_all_recommendations method."""
        rec1 = Recommendation(
            recommendation_id="rec-1",
            project_name="owner/repo1",
            project_url="https://github.com/owner/repo1",
            language="Python",
            relevance_score=8,
            reasoning="Good",
            algorithm_source="content_based",
            mode=RecommendationMode.FAST,
        )
        rec2 = Recommendation(
            recommendation_id="rec-2",
            project_name="owner/repo2",
            project_url="https://github.com/owner/repo2",
            language="Python",
            relevance_score=7,
            reasoning="Good",
            algorithm_source="content_based",
            mode=RecommendationMode.FAST,
        )
        sample_session.add_round(RecommendationRound(round_number=1, recommendations=[rec1]))
        sample_session.add_round(RecommendationRound(round_number=2, recommendations=[rec2]))
        all_recs = sample_session.get_all_recommendations()
        assert len(all_recs) == 2

    def test_get_recommendation_by_id(self, sample_session: RecommendationSession) -> None:
        """Test get_recommendation_by_id method."""
        rec = Recommendation(
            recommendation_id="test-rec-123",
            project_name="owner/repo",
            project_url="https://github.com/owner/repo",
            language="Python",
            relevance_score=8,
            reasoning="Good",
            algorithm_source="content_based",
            mode=RecommendationMode.FAST,
        )
        sample_session.add_round(RecommendationRound(round_number=1, recommendations=[rec]))
        found = sample_session.get_recommendation_by_id("test-rec-123")
        assert found is not None
        assert found.project_name == "owner/repo"

        not_found = sample_session.get_recommendation_by_id("nonexistent")
        assert not_found is None

    def test_add_report_section(self, sample_session: RecommendationSession) -> None:
        """Test add_report_section method."""
        section = ReportSection(
            section_type=SectionType.SUMMARY,
            title="Summary",
            content="Test summary",
        )
        sample_session.add_report_section(section)
        assert len(sample_session.report_sections) == 1
        assert sample_session.report_sections[0].order == 0

    def test_remove_report_section(self, sample_session: RecommendationSession) -> None:
        """Test remove_report_section method."""
        section = ReportSection(
            section_id="sec-123",
            section_type=SectionType.SUMMARY,
            title="Summary",
            content="Test",
        )
        sample_session.add_report_section(section)
        assert sample_session.remove_report_section("sec-123") is True
        assert len(sample_session.report_sections) == 0
        assert sample_session.remove_report_section("nonexistent") is False

    def test_reorder_sections(self, sample_session: RecommendationSession) -> None:
        """Test reorder_sections method."""
        s1 = ReportSection(section_id="s1", section_type=SectionType.SUMMARY, title="S1", content="1")
        s2 = ReportSection(section_id="s2", section_type=SectionType.SUMMARY, title="S2", content="2")
        s3 = ReportSection(section_id="s3", section_type=SectionType.SUMMARY, title="S3", content="3")
        sample_session.add_report_section(s1)
        sample_session.add_report_section(s2)
        sample_session.add_report_section(s3)

        # Reorder: s3, s1, s2
        sample_session.reorder_sections(["s3", "s1", "s2"])
        assert sample_session.report_sections[0].section_id == "s3"
        assert sample_session.report_sections[1].section_id == "s1"
        assert sample_session.report_sections[2].section_id == "s2"

    def test_get_current_round_number(self, sample_session: RecommendationSession) -> None:
        """Test get_current_round_number method."""
        assert sample_session.get_current_round_number() == 0
        sample_session.add_round(RecommendationRound(round_number=1))
        assert sample_session.get_current_round_number() == 1

    def test_is_max_rounds_reached(self, sample_session: RecommendationSession) -> None:
        """Test is_max_rounds_reached method."""
        assert sample_session.is_max_rounds_reached(3) is False
        sample_session.add_round(RecommendationRound(round_number=1))
        sample_session.add_round(RecommendationRound(round_number=2))
        sample_session.add_round(RecommendationRound(round_number=3))
        assert sample_session.is_max_rounds_reached(3) is True

    def test_finalize(self, sample_session: RecommendationSession) -> None:
        """Test finalize method."""
        sample_session.finalize()
        assert sample_session.status == SessionStatus.COMPLETED

    def test_abandon(self, sample_session: RecommendationSession) -> None:
        """Test abandon method."""
        sample_session.abandon()
        assert sample_session.status == SessionStatus.ABANDONED

    def test_to_markdown_report(self, sample_session: RecommendationSession) -> None:
        """Test to_markdown_report method."""
        rec = Recommendation(
            recommendation_id="rec-1",
            project_name="owner/repo",
            project_url="https://github.com/owner/repo",
            language="Python",
            relevance_score=8,
            reasoning="Good",
            algorithm_source="content_based",
            mode=RecommendationMode.FAST,
        )
        round_data = RecommendationRound(
            round_number=1,
            recommendations=[rec],
            user_feedback=[
                UserFeedback(
                    recommendation_id="rec-1",
                    feedback_type=FeedbackType.ACCEPT,
                )
            ],
        )
        sample_session.add_round(round_data)

        md = sample_session.to_markdown_report()
        assert "# OSS-Navi Analysis Report" in md
        assert "**Session**" in md
        assert "**Mode**: fast" in md
        assert "## Accepted Recommendations" in md
        assert "owner/repo" in md
