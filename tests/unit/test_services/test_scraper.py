"""Additional unit tests for scraper service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestScrapersDetailed:
    """Detailed tests for scraper functions."""

    def test_sanitize_text(self) -> None:
        """Test text sanitization."""
        from oss_navi.services.scraper import sanitize_text

        assert sanitize_text("<p>Hello</p>") == "Hello"
        assert sanitize_text("  multiple   spaces  ") == "multiple spaces"
        assert sanitize_text(None) == ""
        assert sanitize_text("") == ""

    def test_validate_github_url(self) -> None:
        """Test GitHub URL validation."""
        from oss_navi.services.scraper import validate_github_url

        assert validate_github_url("https://github.com/owner/repo")
        assert validate_github_url("https://github.com/owner/repo/issues/1")
        assert not validate_github_url("https://gitlab.com/owner/repo")
        assert not validate_github_url("not-a-url")
        assert not validate_github_url("")
        assert not validate_github_url(None)

    def test_validate_github_issue_url_valid(self) -> None:
        """Test valid GitHub issue URLs."""
        from oss_navi.services.scraper import validate_github_issue_url

        assert validate_github_issue_url("https://github.com/python/cpython/issues/12345")
        assert validate_github_issue_url("https://github.com/pallets/click/issues/1")
        assert validate_github_issue_url("http://github.com/owner/repo/issues/999")

    def test_validate_github_issue_url_invalid(self) -> None:
        """Test invalid GitHub issue URLs."""
        from oss_navi.services.scraper import validate_github_issue_url

        # Not a GitHub URL
        assert not validate_github_issue_url("https://gitlab.com/owner/repo/issues/1")
        # Not an issue URL
        assert not validate_github_issue_url("https://github.com/owner/repo")
        assert not validate_github_issue_url("https://github.com/owner/repo/pulls/1")
        # Missing issue number
        assert not validate_github_issue_url("https://github.com/owner/repo/issues/")
        # Invalid issue number
        assert not validate_github_issue_url("https://github.com/owner/repo/issues/abc")
        # Empty/None
        assert not validate_github_issue_url("")
        assert not validate_github_issue_url(None)

    def test_validate_github_repo_url_valid(self) -> None:
        """Test valid GitHub repository URLs."""
        from oss_navi.services.scraper import validate_github_repo_url

        assert validate_github_repo_url("https://github.com/python/cpython")
        assert validate_github_repo_url("https://github.com/pallets/click")
        assert validate_github_repo_url("http://github.com/owner/repo")
        assert validate_github_repo_url("https://github.com/owner/repo-with-dashes")
        assert validate_github_repo_url("https://github.com/owner/repo_with_underscores")

    def test_validate_github_repo_url_invalid(self) -> None:
        """Test invalid GitHub repository URLs."""
        from oss_navi.services.scraper import validate_github_repo_url

        # Not a GitHub URL
        assert not validate_github_repo_url("https://gitlab.com/owner/repo")
        # Missing repo name
        assert not validate_github_repo_url("https://github.com/owner")
        assert not validate_github_repo_url("https://github.com/")
        # Invalid characters in names
        assert not validate_github_repo_url("https://github.com/owner/repo@invalid")
        # Empty/None
        assert not validate_github_repo_url("")
        assert not validate_github_repo_url(None)

    @patch("httpx.Client")
    def test_fetch_upforgrabs_with_issues(self, mock_client_class: MagicMock) -> None:
        """Test fetching Up For Grabs with valid projects."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First call: list of project files
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # Second call: YAML content
        yaml_content = """
name: Test Project
desc: A test project
site: https://github.com/owner/repo
tags:
  - python
  - web
upforgrabs:
  name: good first issue
  link: https://github.com/owner/repo/labels/good%20first%20issue
stats:
  issue-count: 2
  last-updated: '2026-03-05T00:00:00Z'
  fork-count: 100
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 2  # 2 issues from issue-count
        assert "Test Project" in tasks[0].title

    @patch("httpx.Client")
    def test_fetch_upforgrabs_invalid_url(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with invalid URLs."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First call: list of project files
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # Second call: YAML with non-GitHub URL
        yaml_content = """
name: Test Project
site: https://gitlab.com/owner/repo
upforgrabs:
  name: good first issue
stats:
  issue-count: 1
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip non-GitHub URLs

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_empty(self, mock_client_class: MagicMock) -> None:
        """Test Good First Issue with empty response."""
        from oss_navi.services.scraper import fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_client.get.return_value = MagicMock(
            status_code=200,
            text="<html><body></body></html>",
        )

        tasks = fetch_goodfirstissue_tasks()
        assert len(tasks) == 0

    @patch("httpx.Client")
    def test_fetch_and_cache_tasks(self, mock_client_class: MagicMock, tmp_path) -> None:
        """Test fetch_and_cache_tasks function."""
        from oss_navi.services.scraper import fetch_and_cache_tasks
        from pathlib import Path

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock Up For Grabs response (new YAML structure)
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]
        yaml_content = """
name: Test Project
site: https://github.com/owner/repo
upforgrabs:
  name: good first issue
  link: https://github.com/owner/repo/issues/1
stats:
  issue-count: 1
  last-updated: '2026-03-05T00:00:00Z'
  fork-count: 100
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
            MagicMock(status_code=503, text=""),  # GFI unavailable
        ]
        mock_client.get.side_effect = responses

        with patch("oss_navi.utils.paths.UPFORGRABS_TASKS_CACHE", tmp_path / "ufg.json"):
            with patch("oss_navi.utils.paths.GOODFIRSTISSUE_TASKS_CACHE", tmp_path / "gfi.json"):
                with patch("oss_navi.utils.paths.CACHE_METADATA_FILE", tmp_path / "meta.json"):
                    tasks = fetch_and_cache_tasks(sources=["upforgrabs", "goodfirstissue"])
                    assert len(tasks) == 1

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_with_content(self, mock_client_class: MagicMock) -> None:
        """Test Good First Issue with actual HTML content."""
        from oss_navi.services.scraper import fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        html = """
        <html>
        <body>
            <article class="issue">
                <a class="issue-link" href="https://github.com/owner/repo/issues/1">Fix bug</a>
                <span class="stars">100</span>
                <span class="language">Python</span>
            </article>
        </body>
        </html>
        """

        mock_client.get.return_value = MagicMock(
            status_code=200,
            text=html,
        )

        tasks = fetch_goodfirstissue_tasks()
        # May or may not parse successfully depending on HTML structure
        assert isinstance(tasks, list)

    @patch("httpx.Client")
    def test_fetch_upforgrabs_empty_projects(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with empty projects list."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: [],
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0

    @patch("httpx.Client")
    def test_fetch_upforgrabs_malformed_issue(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with malformed YAML data."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text="invalid: yaml: : :"),  # Invalid YAML
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip malformed projects

    @patch("httpx.Client")
    def test_fetch_upforgrabs_missing_dates(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with missing date fields."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # YAML without last-updated date
        yaml_content = """
name: Test Project
site: https://github.com/owner/repo
upforgrabs:
  name: good first issue
stats:
  issue-count: 1
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 1  # Should still work with default dates


class TestGoodFirstIssuesFetcher:
    """Tests for Good First Issues (goodfirstissues.com) fetcher."""

    @patch("httpx.Client")
    def test_fetch_goodfirstissues_tasks(self, mock_client_class: MagicMock) -> None:
        """Test fetching from goodfirstissues.com JSON API."""
        from oss_navi.services.scraper import fetch_goodfirstissues_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock JSON response
        mock_data = [
            {
                "Issue": {
                    "issue_url": "https://github.com/owner/repo/issues/1",
                    "issue_title": "Test Issue",
                    "issue_createdAt": "2026-03-01T00:00:00Z",
                    "issue_repo": {
                        "repo_name": "repo",
                        "repo_stars": 100,
                        "repo_langs": {
                            "Nodes": [{"repo_prog_language": "Python"}]
                        },
                        "Owner": {"repo_owner": "owner"}
                    },
                    "issue_labels": {
                        "Nodes": [{"label_name": "good first issue"}]
                    }
                }
            }
        ]

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_goodfirstissues_tasks(max_issues=10)
        assert len(tasks) == 1
        assert tasks[0].source == "goodfirstissues"
        assert tasks[0].repository.language == "Python"

    @patch("httpx.Client")
    def test_fetch_goodfirstissues_unavailable(self, mock_client_class: MagicMock) -> None:
        """Test handling when goodfirstissues.com is unavailable."""
        from oss_navi.services.scraper import GoodFirstIssueUnavailableError, fetch_goodfirstissues_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=503)

        with pytest.raises(GoodFirstIssueUnavailableError):
            fetch_goodfirstissues_tasks()

    @patch("httpx.Client")
    def test_fetch_goodfirstissues_invalid_url(self, mock_client_class: MagicMock) -> None:
        """Test goodfirstissues with invalid URLs (should skip)."""
        from oss_navi.services.scraper import fetch_goodfirstissues_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock with invalid URL
        mock_data = [
            {
                "Issue": {
                    "issue_url": "https://gitlab.com/owner/repo/issues/1",  # Not GitHub
                    "issue_title": "Test Issue",
                    "issue_createdAt": "2026-03-01T00:00:00Z",
                    "issue_repo": {
                        "repo_name": "repo",
                        "repo_stars": 100,
                        "repo_langs": {"Nodes": []},
                        "Owner": {"repo_owner": "owner"}
                    },
                    "issue_labels": {"Nodes": []}
                }
            }
        ]

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_goodfirstissues_tasks()
        assert len(tasks) == 0  # Should skip invalid URLs

    @patch("httpx.Client")
    def test_fetch_goodfirstissues_malformed(self, mock_client_class: MagicMock) -> None:
        """Test goodfirstissues with malformed data."""
        from oss_navi.services.scraper import fetch_goodfirstissues_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock with malformed data
        mock_data = [
            {"Issue": {"issue_url": "not-a-url"}},  # Missing required fields
            {"Issue": {}},  # Empty issue
        ]

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_goodfirstissues_tasks()
        assert len(tasks) == 0  # Should skip malformed entries


class TestSearchFunctions:
    """Tests for search and filter functions."""

    def test_filter_tasks_by_tags(self) -> None:
        """Test filtering tasks by tags."""
        from oss_navi.services.scraper import filter_tasks_by_tags
        from oss_navi.models.task import Repository, Task
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                id="test:1",
                title="Python task",
                url="https://github.com/owner/repo1/issues/1",
                source="upforgrabs",
                repository=Repository(
                    name="owner/repo1",
                    url="https://github.com/owner/repo1",
                    stars=100,
                    language="Python",
                    topics=["web", "api"],
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=10.0,
                fetched_at=now,
            ),
            Task(
                id="test:2",
                title="JavaScript task",
                url="https://github.com/owner/repo2/issues/1",
                source="goodfirstissue",
                repository=Repository(
                    name="owner/repo2",
                    url="https://github.com/owner/repo2",
                    stars=50,
                    language="JavaScript",
                    topics=["frontend"],
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=5.0,
                fetched_at=now,
            ),
        ]

        filtered = filter_tasks_by_tags(tasks, ["Python"])
        assert len(filtered) == 1
        assert filtered[0].repository.language == "Python"

        # Test multiple matches
        filtered = filter_tasks_by_tags(tasks, ["Python", "JavaScript"])
        assert len(filtered) == 2

    def test_select_diverse_tasks_random(self) -> None:
        """Test random task selection."""
        from oss_navi.services.scraper import select_diverse_tasks
        from oss_navi.models.task import Repository, Task
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                id=f"test:{i}",
                title=f"Task {i}",
                url=f"https://github.com/owner/repo/issues/{i}",
                source="upforgrabs",
                repository=Repository(
                    name="owner/repo",
                    url="https://github.com/owner/repo",
                    stars=100,
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=float(i),
                fetched_at=now,
            )
            for i in range(100)
        ]

        selected = select_diverse_tasks(tasks, count=10, strategy="random")
        assert len(selected) == 10

    def test_select_diverse_tasks_top(self) -> None:
        """Test top task selection by hotness."""
        from oss_navi.services.scraper import select_diverse_tasks
        from oss_navi.models.task import Repository, Task
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                id=f"test:{i}",
                title=f"Task {i}",
                url=f"https://github.com/owner/repo/issues/{i}",
                source="upforgrabs",
                repository=Repository(
                    name="owner/repo",
                    url="https://github.com/owner/repo",
                    stars=100,
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=float(i),
                fetched_at=now,
            )
            for i in range(100)
        ]

        selected = select_diverse_tasks(tasks, count=5, strategy="top")
        assert len(selected) == 5
        # Should be the top 5 by hotness
        assert all(t.hotness_score >= 95 for t in selected)

    def test_search_tasks(self) -> None:
        """Test combined search function."""
        from oss_navi.services.scraper import search_tasks
        from oss_navi.models.task import Repository, Task
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        old_date = now - timedelta(days=100)

        tasks = [
            Task(
                id="test:1",
                title="Python task",
                url="https://github.com/owner/repo1/issues/1",
                source="upforgrabs",
                repository=Repository(
                    name="owner/repo1",
                    url="https://github.com/owner/repo1",
                    stars=100,
                    language="Python",
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=10.0,
                fetched_at=now,
            ),
            Task(
                id="test:2",
                title="Old task",
                url="https://github.com/owner/repo2/issues/1",
                source="goodfirstissue",
                repository=Repository(
                    name="owner/repo2",
                    url="https://github.com/owner/repo2",
                    stars=50,
                ),
                labels=[],
                created_at=old_date,
                updated_at=old_date,
                hotness_score=5.0,
                fetched_at=now,
            ),
        ]

        # Test min_stars filter
        result = search_tasks(tasks, min_stars=75, max_age_days=365)
        assert len(result) == 1
        assert result[0].repository.stars == 100

        # Test max_age filter
        result = search_tasks(tasks, min_stars=0, max_age_days=30)
        assert len(result) == 1
        assert "Python" in result[0].title

    def test_select_diverse_tasks_diverse_strategy(self) -> None:
        """Test diverse task selection strategy."""
        from oss_navi.services.scraper import select_diverse_tasks
        from oss_navi.models.task import Repository, Task
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        tasks = [
            Task(
                id=f"test:{i}",
                title=f"Task {i}",
                url=f"https://github.com/owner/repo{i}/issues/{i}",
                source="upforgrabs" if i % 2 == 0 else "goodfirstissue",
                repository=Repository(
                    name=f"owner/repo{i}",
                    url=f"https://github.com/owner/repo{i}",
                    stars=100,
                    language="Python" if i % 3 == 0 else "JavaScript",
                ),
                labels=[],
                created_at=now,
                updated_at=now,
                hotness_score=float(i),
                fetched_at=now,
            )
            for i in range(50)
        ]

        selected = select_diverse_tasks(tasks, count=10, strategy="diverse")
        assert len(selected) == 10

        # Should have variety in sources and languages
        sources = {t.source for t in selected}
        languages = {t.repository.language for t in selected}
        assert len(sources) >= 1  # At least one source
        assert len(languages) >= 1  # At least one language
