"""Unit tests for path utilities."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestPaths:
    """Tests for path utility functions."""

    def test_get_oss_navi_home_default(self) -> None:
        """Test default OSS_NAVI_HOME path."""
        from oss_navi.utils.paths import get_oss_navi_home

        with patch.dict(os.environ, {}, clear=True):
            home = get_oss_navi_home()
            assert home == Path.home() / ".oss-navi"

    def test_get_oss_navi_home_custom(self) -> None:
        """Test custom OSS_NAVI_HOME path from environment."""
        from oss_navi.utils.paths import get_oss_navi_home

        custom_path = "/custom/path"
        with patch.dict(os.environ, {"OSS_NAVI_HOME": custom_path}):
            home = get_oss_navi_home()
            assert home == Path(custom_path)

    def test_ensure_directories(self, tmp_path: Path) -> None:
        """Test ensuring all directories are created."""
        from oss_navi.utils.paths import ensure_directories

        with patch("oss_navi.utils.paths.OSS_NAVI_HOME", tmp_path):
            with patch("oss_navi.utils.paths.CACHE_DIR", tmp_path / "cache"):
                with patch("oss_navi.utils.paths.STATE_DIR", tmp_path / "state"):
                    with patch("oss_navi.utils.paths.TEMP_DIR", tmp_path / "temp"):
                        with patch("oss_navi.utils.paths.REPORTS_DIR", tmp_path / "state" / "reports"):
                            ensure_directories()

                            assert (tmp_path / "cache").exists()
                            assert (tmp_path / "state").exists()
                            assert (tmp_path / "temp").exists()

    def test_get_report_path(self, tmp_path: Path) -> None:
        """Test getting report path by ID."""
        from oss_navi.utils.paths import get_report_path

        with patch("oss_navi.utils.paths.REPORTS_DIR", tmp_path):
            path = get_report_path("20260307_120000")
            assert path == tmp_path / "report_20260307_120000.md"

    def test_get_current_report_path(self, tmp_path: Path) -> None:
        """Test getting current report path."""
        from oss_navi.utils.paths import get_current_report_path

        with patch("oss_navi.utils.paths.TEMP_DIR", tmp_path):
            path = get_current_report_path()
            assert path == tmp_path / "current_report.md"
