"""Tests for IssueStatus model."""

from datetime import UTC, datetime

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
            checked_at=datetime.now(UTC),
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
            checked_at=datetime.now(UTC),
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
            checked_at=datetime.now(UTC),
        )
        assert status.is_closed is True

    def test_issue_status_has_linked_pr(self) -> None:
        """Test IssueStatus when issue has linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/4",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=True,
            checked_at=datetime.now(UTC),
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
            checked_at=datetime.now(UTC),
        )
        assert status.in_progress_labels == ["in progress", "wip"]

    def test_is_available_true(self) -> None:
        """Test is_available returns True when issue is free."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/6",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is True

    def test_is_available_false_assigned(self) -> None:
        """Test is_available returns False when issue is assigned."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/7",
            is_assigned=True,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is False

    def test_is_available_false_closed(self) -> None:
        """Test is_available returns False when issue is closed."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/8",
            is_assigned=False,
            is_closed=True,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is False

    def test_is_available_false_has_pr(self) -> None:
        """Test is_available returns False when issue has linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/9",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=True,
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is False

    # T118: Tests for has_open_pr field
    def test_issue_status_has_open_pr_field(self) -> None:
        """Test IssueStatus with has_open_pr field for linked PR detection."""
        status = IssueStatus(
            issue_url="https://github.com/python/cpython/issues/110982",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            has_open_pr=True,
            linked_pr_url="https://github.com/python/cpython/pull/111000",
            checked_at=datetime.now(UTC),
        )
        assert status.has_open_pr is True
        assert status.linked_pr_url == "https://github.com/python/cpython/pull/111000"

    def test_issue_status_has_open_pr_defaults_false(self) -> None:
        """Test has_open_pr defaults to False."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/1",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.has_open_pr is False
        assert status.linked_pr_url is None

    # T119: Tests for is_available with linked PR
    def test_is_available_false_has_open_pr(self) -> None:
        """Test is_available returns False when issue has open linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/python/cpython/issues/110982",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            has_open_pr=True,
            linked_pr_url="https://github.com/python/cpython/pull/111000",
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is False

    def test_is_available_true_no_open_pr(self) -> None:
        """Test is_available returns True when issue has no open linked PR."""
        status = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/1",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            has_open_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.is_available is True

    # Real GitHub URL tests
    def test_issue_status_real_url_python_cpython(self) -> None:
        """Test IssueStatus with real GitHub URL from python/cpython."""
        status = IssueStatus(
            issue_url="https://github.com/python/cpython/issues/110982",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert "python/cpython" in status.issue_url

    def test_issue_status_assigned_real_url(self) -> None:
        """Test IssueStatus with assigned issue from real GitHub URL."""
        status = IssueStatus(
            issue_url="https://github.com/microsoft/vscode/issues/200000",
            is_assigned=True,
            assignee="maintainer456",
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(UTC),
        )
        assert status.is_assigned is True
        assert status.assignee == "maintainer456"
        assert status.is_available is False
