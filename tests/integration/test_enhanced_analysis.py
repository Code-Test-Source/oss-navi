"""Integration tests for enhanced analysis features."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oss_navi.models.task import GreatProject, IssueStatus, Recommendation, Repository, Task


class TestEnhancedAnalysisIntegration:
    """End-to-end integration tests for enhanced analysis."""

    @pytest.fixture
    def mock_profile(self) -> dict:
        """Create mock profile data."""
        return {
            "username": "testuser",
            "languages": {"Python": 0.6, "TypeScript": 0.3, "Go": 0.1},
            "public_repos": 42,
        }

    @pytest.fixture
    def mock_tasks(self) -> list[Task]:
        """Create mock tasks for testing."""
        now = datetime.now(timezone.utc)
        tasks = []
        for i in range(15):
            task = Task(
                id=f"test:{i}",
                title=f"Issue {i}: Fix bug in authentication",
                url=f"https://github.com/owner/repo{i}/issues/{i}",
                source="upforgrabs",
                repository=Repository(
                    name=f"owner/repo{i}",
                    url=f"https://github.com/owner/repo{i}",
                    stars=100 * (i + 1),
                    language="Python" if i % 2 == 0 else "TypeScript",
                    topics=["web", "api"] if i % 3 == 0 else ["cli", "tools"],
                ),
                labels=["good first issue", "bug"],
                created_at=now,
                updated_at=now,
                hotness_score=10.0 * (i + 1),
                fetched_at=now,
            )
            tasks.append(task)
        return tasks

    def test_generate_recommendations_integration(
        self, mock_profile: dict, mock_tasks: list[Task]
    ) -> None:
        """Test full recommendation generation pipeline."""
        from oss_navi.services.analyzer import generate_recommendations

        with patch("oss_navi.services.analyzer.check_issue_status") as mock_check:
            mock_check.return_value = IssueStatus(
                issue_url="https://github.com/owner/repo/issues/1",
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(timezone.utc),
            )

            recommendations = generate_recommendations(
                tasks=mock_tasks,
                user_languages=mock_profile["languages"],
                learning_focus="Python",
                count=7,
            )

        # Should return 5-10 recommendations
        assert 5 <= len(recommendations) <= 10

        # Each recommendation should have required fields
        for rec in recommendations:
            assert rec.task is not None
            assert 1.0 <= rec.rating <= 10.0
            assert rec.rating_breakdown is not None
            assert len(rec.reason) >= 10
            assert len(rec.code_analysis) >= 10
            assert rec.status is not None

        # Should be sorted by rating (descending)
        ratings = [r.rating for r in recommendations]
        assert ratings == sorted(ratings, reverse=True)

    def test_find_great_projects_integration(
        self, mock_profile: dict
    ) -> None:
        """Test great project discovery pipeline."""
        from oss_navi.services.analyzer import find_great_projects

        with patch("oss_navi.services.analyzer.GitHubClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.search_repositories.return_value = [
                {
                    "full_name": "python/cpython",
                    "html_url": "https://github.com/python/cpython",
                    "stargazers_count": 60000,
                    "language": "Python",
                    "description": "The Python programming language",
                    "topics": ["python", "interpreter"],
                },
                {
                    "full_name": "pallets/flask",
                    "html_url": "https://github.com/pallets/flask",
                    "stargazers_count": 65000,
                    "language": "Python",
                    "description": "The Python micro framework",
                    "topics": ["python", "web", "flask"],
                },
            ]

            projects = find_great_projects(
                user_languages=mock_profile["languages"],
                learning_focus="Python",
                count=3,
            )

        # Should return projects with all required fields
        assert len(projects) >= 1
        for proj in projects:
            assert proj.name
            assert proj.url.startswith("https://github.com/")
            assert proj.stars > 0
            assert proj.language
            assert len(proj.why_great) > 0
            assert len(proj.architecture_overview) > 0

    def test_suggest_adjacent_fields_integration(self) -> None:
        """Test field suggestion pipeline."""
        from oss_navi.services.analyzer import suggest_adjacent_fields

        suggestions = suggest_adjacent_fields(
            current_interest="Python",
            user_languages={"Python": 0.7, "JavaScript": 0.3},
        )

        # Should return 2-4 suggestions
        assert 2 <= len(suggestions) <= 5

        # Suggestions should be relevant to Python
        assert any("web" in s.lower() or "data" in s.lower() or "devops" in s.lower() for s in suggestions)

    def test_full_analysis_pipeline(
        self, mock_profile: dict, mock_tasks: list[Task], tmp_path: Path
    ) -> None:
        """Test complete analysis pipeline from data to recommendations."""
        from oss_navi.services.analyzer import (
            calculate_rating_breakdown,
            find_great_projects,
            generate_recommendations,
            suggest_adjacent_fields,
        )

        # Step 1: Calculate ratings for a task
        sample_task = mock_tasks[0]
        breakdown = calculate_rating_breakdown(
            task=sample_task,
            user_languages=mock_profile["languages"],
            learning_focus="Python",
        )
        assert breakdown.weighted_total > 0

        # Step 2: Generate recommendations
        with patch("oss_navi.services.analyzer.check_issue_status") as mock_check:
            mock_check.return_value = IssueStatus(
                issue_url=sample_task.url,
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(timezone.utc),
            )
            recommendations = generate_recommendations(
                tasks=mock_tasks,
                user_languages=mock_profile["languages"],
                learning_focus="Python",
                count=5,
            )
        assert len(recommendations) >= 5

        # Step 3: Get field suggestions
        fields = suggest_adjacent_fields("Python", mock_profile["languages"])
        assert len(fields) >= 2

        # Step 4: Find great projects
        with patch("oss_navi.services.analyzer.GitHubClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.search_repositories.return_value = [
                {
                    "full_name": "python/cpython",
                    "html_url": "https://github.com/python/cpython",
                    "stargazers_count": 60000,
                    "language": "Python",
                    "description": "The Python programming language",
                    "topics": ["python"],
                },
            ]
            projects = find_great_projects(
                user_languages=mock_profile["languages"],
                learning_focus="Python",
                count=2,
            )
        assert len(projects) >= 1


class TestReportStructure:
    """Tests for enhanced report structure."""

    def test_recommendation_has_all_fields(self) -> None:
        """Test that recommendations include all required fields."""
        from oss_navi.models.task import RatingBreakdown

        now = datetime.now(timezone.utc)
        task = Task(
            id="test:1",
            title="Test issue",
            url="https://github.com/owner/repo/issues/1",
            source="upforgrabs",
            repository=Repository(
                name="owner/repo",
                url="https://github.com/owner/repo",
                stars=100,
                language="Python",
            ),
            labels=["good first issue"],
            created_at=now,
            updated_at=now,
            hotness_score=10.0,
            fetched_at=now,
        )

        breakdown = RatingBreakdown(
            language_match=8.0,
            hotness_score=5.0,
            issue_availability=10.0,
            learning_alignment=9.0,
            skill_level_fit=8.0,
            topic_relevance=6.0,
        )

        status = IssueStatus(
            issue_url=task.url,
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=now,
        )

        rec = Recommendation(
            task=task,
            rating=breakdown.weighted_total,
            rating_breakdown=breakdown,
            reason="This matches your Python expertise and is beginner-friendly.",
            code_analysis="This Python project has 100 stars and focuses on web development.",
            status=status,
        )

        # Verify all fields are present
        assert rec.task == task
        assert rec.rating > 0
        assert rec.rating_breakdown.language_match == 8.0
        assert len(rec.reason) >= 10
        assert len(rec.code_analysis) >= 10
        assert rec.status.is_available is True

    def test_great_project_has_all_fields(self) -> None:
        """Test that great projects include all required fields."""
        project = GreatProject(
            name="python/cpython",
            url="https://github.com/python/cpython",
            stars=60000,
            language="Python",
            why_great="Highly popular with strong community.",
            architecture_overview="Uses src/ layout with Python modules.",
            key_patterns=["object-oriented design", "decorators"],
            contribution_areas=["documentation", "testing"],
            relevance_reason="Matches your Python expertise.",
        )

        # Verify all fields are present
        assert project.name == "python/cpython"
        assert project.stars == 60000
        assert len(project.key_patterns) >= 1
        assert len(project.contribution_areas) >= 1

    def test_issue_status_availability(self) -> None:
        """Test issue status availability logic."""
        now = datetime.now(timezone.utc)

        # Available issue
        available = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/1",
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=now,
        )
        assert available.is_available is True

        # Assigned issue
        assigned = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/2",
            is_assigned=True,
            assignee="developer",
            is_closed=False,
            has_linked_pr=False,
            checked_at=now,
        )
        assert assigned.is_available is False

        # Closed issue
        closed = IssueStatus(
            issue_url="https://github.com/owner/repo/issues/3",
            is_assigned=False,
            is_closed=True,
            has_linked_pr=False,
            checked_at=now,
        )
        assert closed.is_available is False
