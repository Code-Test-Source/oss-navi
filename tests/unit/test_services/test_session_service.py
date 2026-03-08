"""Tests for session service."""

from pathlib import Path

import pytest

from oss_navi.models.preferences import LanguageProfile, LanguageType, SkillLevel, UserPreferences
from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.models.session import (
    FeedbackType,
    RecommendationRound,
    ReportSection,
    SectionType,
    SessionStatus,
    UserFeedback,
)
from oss_navi.services.session import PreferencesService, SessionService


class TestSessionService:
    """Tests for SessionService."""

    @pytest.fixture
    def session_service(self, tmp_path: Path) -> SessionService:
        """Create a SessionService with temp directory."""
        return SessionService(sessions_dir=tmp_path / "sessions")

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
        )

    def test_create_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test create_session method."""
        session = session_service.create_session(
            user_preferences=user_prefs,
            mode=RecommendationMode.FAST,
        )
        assert session.session_id
        assert session.status == SessionStatus.ACTIVE
        assert session.mode == RecommendationMode.FAST

    def test_get_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test get_session method."""
        created = session_service.create_session(user_prefs)
        retrieved = session_service.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_session_not_found(self, session_service: SessionService) -> None:
        """Test get_session returns None for non-existent session."""
        result = session_service.get_session("nonexistent")
        assert result is None

    def test_save_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test save_session method."""
        session = session_service.create_session(user_prefs)
        session.add_round(RecommendationRound(round_number=1))
        session_service.save_session(session)

        # Verify persistence
        retrieved = session_service.get_session(session.session_id)
        assert retrieved is not None
        assert len(retrieved.rounds) == 1

    def test_delete_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test delete_session method."""
        session = session_service.create_session(user_prefs)
        assert session_service.delete_session(session.session_id) is True
        assert session_service.get_session(session.session_id) is None
        assert session_service.delete_session("nonexistent") is False

    def test_list_sessions(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test list_sessions method."""
        session_service.create_session(user_prefs)
        session2 = session_service.create_session(user_prefs)
        session2.finalize()
        session_service.save_session(session2)

        all_sessions = session_service.list_sessions()
        assert len(all_sessions) == 2

        active = session_service.list_sessions(status=SessionStatus.ACTIVE)
        assert len(active) == 1

        completed = session_service.list_sessions(status=SessionStatus.COMPLETED)
        assert len(completed) == 1

    def test_list_active_sessions(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test list_active_sessions method."""
        session = session_service.create_session(user_prefs)
        active = session_service.list_active_sessions()
        assert len(active) == 1
        assert active[0].session_id == session.session_id

    def test_add_round_to_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test add_round_to_session method."""
        session = session_service.create_session(user_prefs)
        round_data = RecommendationRound(round_number=1)
        updated = session_service.add_round_to_session(session.session_id, round_data)
        assert updated is not None
        assert len(updated.rounds) == 1

    def test_add_feedback_to_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test add_feedback_to_session method."""
        session = session_service.create_session(user_prefs)
        session.add_round(RecommendationRound(round_number=1))
        session_service.save_session(session)

        feedback = UserFeedback(
            recommendation_id="rec-1",
            feedback_type=FeedbackType.ACCEPT,
        )
        updated = session_service.add_feedback_to_session(session.session_id, feedback)
        assert updated is not None
        assert len(updated.rounds[0].user_feedback) == 1

    def test_add_section_to_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test add_section_to_session method."""
        session = session_service.create_session(user_prefs)
        section = ReportSection(
            section_type=SectionType.SUMMARY,
            title="Summary",
            content="Test",
        )
        updated = session_service.add_section_to_session(session.session_id, section)
        assert updated is not None
        assert len(updated.report_sections) == 1

    def test_finalize_session(
        self, session_service: SessionService, user_prefs: UserPreferences
    ) -> None:
        """Test finalize_session method."""
        session = session_service.create_session(user_prefs)
        updated = session_service.finalize_session(session.session_id)
        assert updated is not None
        assert updated.status == SessionStatus.COMPLETED

    def test_export_session_report(
        self, session_service: SessionService, user_prefs: UserPreferences, tmp_path: Path
    ) -> None:
        """Test export_session_report method."""
        session = session_service.create_session(user_prefs)
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
        session.add_round(RecommendationRound(round_number=1, recommendations=[rec]))
        session_service.save_session(session)

        output_path = tmp_path / "report.md"
        report = session_service.export_session_report(
            session.session_id, output_path=output_path
        )
        assert report is not None
        assert "# OSS-Navi Analysis Report" in report
        assert output_path.exists()

    def test_export_session_report_not_found(self, session_service: SessionService) -> None:
        """Test export_session_report returns None for non-existent session."""
        result = session_service.export_session_report("nonexistent")
        assert result is None


class TestPreferencesService:
    """Tests for PreferencesService."""

    @pytest.fixture
    def prefs_service(self, tmp_path: Path) -> PreferencesService:
        """Create a PreferencesService with temp file."""
        return PreferencesService(prefs_file=tmp_path / "preferences.json")

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
        )

    def test_save_and_get_preferences(
        self, prefs_service: PreferencesService, user_prefs: UserPreferences
    ) -> None:
        """Test save_preferences and get_preferences methods."""
        prefs_service.save_preferences(user_prefs)
        retrieved = prefs_service.get_preferences()
        assert retrieved is not None
        assert len(retrieved.languages) == 1

    def test_get_preferences_not_set(self, prefs_service: PreferencesService) -> None:
        """Test get_preferences returns None when not set."""
        result = prefs_service.get_preferences()
        assert result is None

    def test_export_preferences(
        self, prefs_service: PreferencesService, user_prefs: UserPreferences, tmp_path: Path
    ) -> None:
        """Test export_preferences method."""
        prefs_service.save_preferences(user_prefs)
        export_path = tmp_path / "exported.json"
        prefs_service.export_preferences(export_path)
        assert export_path.exists()

    def test_import_preferences(
        self, prefs_service: PreferencesService, user_prefs: UserPreferences, tmp_path: Path
    ) -> None:
        """Test import_preferences method."""
        # Create import file
        import_path = tmp_path / "import.json"
        import_path.write_text(user_prefs.model_dump_json())

        imported = prefs_service.import_preferences(import_path)
        assert imported is not None
        assert len(imported.languages) == 1

    def test_import_preferences_invalid(
        self, prefs_service: PreferencesService, tmp_path: Path
    ) -> None:
        """Test import_preferences with invalid file."""
        import_path = tmp_path / "invalid.json"
        import_path.write_text("not valid json")
        result = prefs_service.import_preferences(import_path)
        assert result is None
