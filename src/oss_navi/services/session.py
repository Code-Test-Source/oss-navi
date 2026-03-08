"""Session service for managing recommendation sessions."""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from oss_navi.models.preferences import UserPreferences
from oss_navi.models.recommendation import RecommendationMode
from oss_navi.models.session import (
    RecommendationRound,
    RecommendationSession,
    ReportSection,
    SessionStatus,
    UserFeedback,
)
from oss_navi.utils.datetime_utils import utc_now
from oss_navi.utils.paths import STATE_DIR

if TYPE_CHECKING:
    pass

SESSIONS_DIR = STATE_DIR / "sessions"
PREFERENCES_FILE = STATE_DIR / "preferences.json"


class SessionService:
    """Service for managing recommendation sessions.

    Handles:
    - Session creation and retrieval
    - Session persistence (JSON storage)
    - Preferences persistence
    """

    def __init__(self, sessions_dir: Path | None = None):
        """Initialize session service.

        Args:
            sessions_dir: Directory for session storage (default: ~/.oss-navi/state/sessions/)
        """
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        user_preferences: UserPreferences,
        mode: RecommendationMode = RecommendationMode.NORMAL,
    ) -> RecommendationSession:
        """Create a new recommendation session.

        Args:
            user_preferences: User's preferences
            mode: Recommendation mode

        Returns:
            New RecommendationSession
        """
        session = RecommendationSession(
            user_preferences=user_preferences,
            mode=mode,
        )
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> RecommendationSession | None:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            RecommendationSession or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file) as f:
                data = json.load(f)
            return RecommendationSession(**data)
        except Exception:
            return None

    def save_session(self, session: RecommendationSession) -> None:
        """Save a session to storage.

        Args:
            session: Session to save
        """
        session_file = self.sessions_dir / f"{session.session_id}.json"
        session.updated_at = utc_now()

        with open(session_file, "w") as f:
            json.dump(
                session.model_dump(mode="json"),
                f,
                indent=2,
                default=self._json_serializer,
            )

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False

    def list_sessions(
        self,
        status: SessionStatus | None = None,
    ) -> list[RecommendationSession]:
        """List all sessions, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of sessions
        """
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                session = RecommendationSession(**data)
                if status is None or session.status == status:
                    sessions.append(session)
            except Exception:
                continue

        # Sort by created_at descending
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def list_active_sessions(self) -> list[RecommendationSession]:
        """List all active sessions.

        Returns:
            List of active sessions
        """
        return self.list_sessions(status=SessionStatus.ACTIVE)

    def add_round_to_session(
        self,
        session_id: str,
        round_data: RecommendationRound,
    ) -> RecommendationSession | None:
        """Add a round to a session.

        Args:
            session_id: Session identifier
            round_data: Round to add

        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        session.add_round(round_data)
        self.save_session(session)
        return session

    def add_feedback_to_session(
        self,
        session_id: str,
        feedback: UserFeedback,
    ) -> RecommendationSession | None:
        """Add feedback to a session.

        Args:
            session_id: Session identifier
            feedback: Feedback to add

        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        session.add_feedback(feedback)
        self.save_session(session)
        return session

    def add_section_to_session(
        self,
        session_id: str,
        section: ReportSection,
    ) -> RecommendationSession | None:
        """Add a report section to a session.

        Args:
            session_id: Session identifier
            section: Section to add

        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        session.add_report_section(section)
        self.save_session(session)
        return session

    def finalize_session(self, session_id: str) -> RecommendationSession | None:
        """Mark a session as completed.

        Args:
            session_id: Session identifier

        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        session.finalize()
        self.save_session(session)
        return session

    def export_session_report(
        self,
        session_id: str,
        output_path: Path | None = None,
    ) -> str | None:
        """Export session report as markdown.

        Args:
            session_id: Session identifier
            output_path: Optional output file path

        Returns:
            Markdown report or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        report = session.to_markdown_report()

        if output_path:
            output_path.write_text(report)

        return report

    def _json_serializer(self, obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class PreferencesService:
    """Service for managing user preferences."""

    def __init__(self, prefs_file: Path | None = None):
        """Initialize preferences service.

        Args:
            prefs_file: Path to preferences file (default: ~/.oss-navi/state/preferences.json)
        """
        self.prefs_file = prefs_file or PREFERENCES_FILE
        self.prefs_file.parent.mkdir(parents=True, exist_ok=True)

    def get_preferences(self) -> UserPreferences | None:
        """Get user preferences.

        Returns:
            UserPreferences or None if not set
        """
        if not self.prefs_file.exists():
            return None

        try:
            with open(self.prefs_file) as f:
                data = json.load(f)
            return UserPreferences(**data)
        except Exception:
            return None

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Save user preferences.

        Args:
            preferences: Preferences to save
        """
        preferences.updated_at = utc_now()

        with open(self.prefs_file, "w") as f:
            json.dump(
                preferences.model_dump(mode="json"),
                f,
                indent=2,
                default=self._json_serializer,
            )

    def export_preferences(self, output_path: Path) -> None:
        """Export preferences to a file.

        Args:
            output_path: Output file path
        """
        prefs = self.get_preferences()
        if prefs:
            with open(output_path, "w") as f:
                json.dump(
                    prefs.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=self._json_serializer,
                )

    def import_preferences(self, input_path: Path) -> UserPreferences | None:
        """Import preferences from a file.

        Args:
            input_path: Input file path

        Returns:
            Imported preferences or None if invalid
        """
        try:
            with open(input_path) as f:
                data = json.load(f)
            prefs = UserPreferences(**data)
            self.save_preferences(prefs)
            return prefs
        except Exception:
            return None

    def _json_serializer(self, obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Singleton instances
_session_service: SessionService | None = None
_preferences_service: PreferencesService | None = None


def get_session_service() -> SessionService:
    """Get the singleton SessionService instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service


def get_preferences_service() -> PreferencesService:
    """Get the singleton PreferencesService instance."""
    global _preferences_service
    if _preferences_service is None:
        _preferences_service = PreferencesService()
    return _preferences_service
