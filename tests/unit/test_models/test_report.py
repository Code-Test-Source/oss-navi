"""Unit tests for AnalysisReport model."""

from datetime import datetime

import pytest

from oss_navi.models.report import AnalysisReport


class TestAnalysisReport:
    """Tests for AnalysisReport model."""

    def test_create_analysis_report(self) -> None:
        """Test creating an AnalysisReport with required fields."""
        report = AnalysisReport(
            id="20260307_100000",
            created_at=datetime(2026, 3, 7, 10, 0, 0),
            content="# Test Report\n\nThis is a test report.",
            file_path="/tmp/report.md",
        )
        assert report.id == "20260307_100000"
        assert report.content.startswith("# Test Report")
        assert report.learning_focus is None
        assert report.recommended_projects == []

    def test_analysis_report_with_learning_focus(self) -> None:
        """Test creating an AnalysisReport with learning focus."""
        report = AnalysisReport(
            id="20260307_100000",
            created_at=datetime(2026, 3, 7, 10, 0, 0),
            content="# Test Report",
            file_path="/tmp/report.md",
            learning_focus="python",
        )
        assert report.learning_focus == "python"

    def test_analysis_report_with_recommendations(self) -> None:
        """Test creating an AnalysisReport with recommended projects."""
        report = AnalysisReport(
            id="20260307_100000",
            created_at=datetime(2026, 3, 7, 10, 0, 0),
            content="# Test Report",
            file_path="/tmp/report.md",
            recommended_projects=["python/cpython", "pallets/click"],
        )
        assert len(report.recommended_projects) == 2
        assert "python/cpython" in report.recommended_projects

    def test_generate_report_id(self) -> None:
        """Test generating a timestamp-based report ID."""
        report_id = AnalysisReport.generate_report_id()
        assert len(report_id) == 15  # YYYYMMDD_HHMMSS format
        assert "_" in report_id
        # Verify format matches expected pattern
        parts = report_id.split("_")
        assert len(parts) == 2
        assert len(parts[0]) == 8  # Date
        assert len(parts[1]) == 6  # Time
