"""Tests for LearningSession model."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from oss_navi.models.task import LearningSession


class TestLearningSession:
    """Tests for LearningSession model validation."""

    def test_learning_session_creation_minimal(self) -> None:
        """Test creating LearningSession with required fields only."""
        session = LearningSession(
            primary_interest="Python web development",
        )
        assert session.primary_interest == "Python web development"
        assert session.session_id is not None
        assert session.created_at is not None

    def test_learning_session_with_explore_fields(self) -> None:
        """Test creating LearningSession with explore_fields."""
        session = LearningSession(
            primary_interest="Machine learning",
            explore_fields=["deep learning", "NLP", "computer vision"],
        )
        assert len(session.explore_fields) == 3
        assert "deep learning" in session.explore_fields

    def test_learning_session_with_suggested_fields(self) -> None:
        """Test creating LearningSession with suggested_fields."""
        session = LearningSession(
            primary_interest="Rust",
            explore_fields=["systems programming"],
            suggested_fields=["web assembly", "embedded systems", "CLI tools"],
        )
        assert len(session.suggested_fields) == 3
        assert "web assembly" in session.suggested_fields

    def test_learning_session_session_id_is_uuid(self) -> None:
        """Test that session_id is a valid UUID."""
        session = LearningSession(
            primary_interest="TypeScript",
        )
        # Should be able to parse as UUID
        UUID(session.session_id)  # Will raise if invalid

    def test_learning_session_created_at_auto(self) -> None:
        """Test that created_at is automatically set."""
        before = datetime.now(timezone.utc)
        session = LearningSession(
            primary_interest="Go",
        )
        after = datetime.now(timezone.utc)

        assert before <= session.created_at <= after

    def test_learning_session_empty_explore_fields(self) -> None:
        """Test that explore_fields can be empty."""
        session = LearningSession(
            primary_interest="Python",
            explore_fields=[],
        )
        assert session.explore_fields == []

    def test_learning_session_empty_suggested_fields(self) -> None:
        """Test that suggested_fields can be empty."""
        session = LearningSession(
            primary_interest="Java",
            suggested_fields=[],
        )
        assert session.suggested_fields == []

    def test_learning_session_full(self) -> None:
        """Test creating LearningSession with all fields."""
        session = LearningSession(
            primary_interest="Rust",
            explore_fields=["systems programming", "web assembly"],
            suggested_fields=["embedded systems", "CLI tools"],
        )
        assert session.primary_interest == "Rust"
        assert len(session.explore_fields) == 2
        assert len(session.suggested_fields) == 2
