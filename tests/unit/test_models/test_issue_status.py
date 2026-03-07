"""Tests for IssueStatus model."""

from datetime import datetime, timezone

import pytest

from oss_navi.models.task import IssueStatus


class TestIssueStatus:
    """Tests for IssueStatus model validation."""

    def test_issue_status_creation_minimal(self) -> None:
        """Test creating IssueStatus with required fields only."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/1",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.issue_url == "https://github.com/owner/repo/issues/1"
        assert status.is_assigned is False
        assert status.is_closed is False
        assert status.has_linked_pr is False

    def test_issue_status_assigned(self) -> None:
        """Test IssueStatus when issue is assigned."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/2",
            is_assigned=True,
            assignee="developer123",
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_assigned is True
        assert status.assignee == "developer123"

    def test_issue_status_closed(self) -> None:
        """Test IssueStatus when issue is closed."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/3",
            is_assigned=False,
            is_closed=True,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_closed is True

    def test_issue_status_has_linked_pr(self) -> None:
        """Test IssueStatus when issue has linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/4",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=True,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.has_linked_pr is True

    def test_issue_status_in_progress_labels(self) -> None:
        """Test IssueStatus with in-progress labels."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/5",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            in_progress_labels=["in progress", "wip"],
            checked_at=datetime.now(timezone.utc),
        )
        assert status.in_progress_labels == ["in progress", "wip"]

    def test_is_available_true(self) -> None:
        """Test is_available returns True when issue is free."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/6",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_available is True

    def test_is_available_false_assigned(self) -> None:
        """Test is_available returns False when issue is assigned."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/7",
            is_assigned=True,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_available is False

    def test_is_available_false_closed(self) -> None:
        """Test is_available returns False when issue is closed."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/8",
            is_assigned=False,
            is_closed=True,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_available is False

    def test_is_available_false_has_pr(self) -> None:
        """Test is_available returns False when issue has linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/9",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=True,
            checked_at=datetime.now(timezone.utc),
        )
        assert status.is_available is False
