"""Unit tests for cache utilities."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCacheUtilities:
    """Tests for cache utility functions."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return cache_dir

    def test_read_json_existing_file(self, temp_cache_dir: Path) -> None:
        """Test reading JSON from an existing file."""
        from oss_navi.utils.cache import read_json

        test_file = temp_cache_dir / "test.json"
        test_file.write_text('{"key": "value"}')

        result = read_json(test_file)
        assert result == {"key": "value"}

    def test_read_json_nonexistent_file(self, temp_cache_dir: Path) -> None:
        """Test reading JSON from a nonexistent file."""
        from oss_navi.utils.cache import read_json

        result = read_json(temp_cache_dir / "nonexistent.json")
        assert result is None

    def test_read_json_invalid_json(self, temp_cache_dir: Path) -> None:
        """Test reading invalid JSON returns None."""
        from oss_navi.utils.cache import read_json

        test_file = temp_cache_dir / "invalid.json"
        test_file.write_text("not valid json")

        result = read_json(test_file)
        assert result is None

    def test_write_json_creates_file(self, temp_cache_dir: Path) -> None:
        """Test writing JSON creates a new file."""
        from oss_navi.utils.cache import write_json

        test_file = temp_cache_dir / "new.json"
        write_json(test_file, {"test": "data"})

        assert test_file.exists()
        import json

        assert json.loads(test_file.read_text()) == {"test": "data"}

    def test_write_json_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test writing JSON creates parent directories."""
        from oss_navi.utils.cache import write_json

        test_file = tmp_path / "subdir" / "deep" / "test.json"
        write_json(test_file, {"nested": True})

        assert test_file.exists()

    def test_update_cache_metadata(self, temp_cache_dir: Path) -> None:
        """Test updating cache metadata."""
        from oss_navi.utils.cache import read_json, update_cache_metadata

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            update_cache_metadata("test_cache", count=42)

            metadata = read_json(temp_cache_dir / "metadata.json")
            assert metadata is not None
            assert "caches" in metadata
            assert "test_cache" in metadata["caches"]
            assert metadata["caches"]["test_cache"]["count"] == 42

    def test_is_cache_valid_fresh(self, temp_cache_dir: Path) -> None:
        """Test cache validation for fresh cache."""
        from oss_navi.utils.cache import is_cache_valid, update_cache_metadata

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            update_cache_metadata("fresh_cache")
            assert is_cache_valid("fresh_cache")

    def test_is_cache_valid_expired(self, temp_cache_dir: Path) -> None:
        """Test cache validation for expired cache."""
        from oss_navi.utils.cache import is_cache_valid, write_json

        metadata_file = temp_cache_dir / "metadata.json"

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", metadata_file):
            # Create expired cache entry
            now = datetime.now(UTC)
            expired = now - timedelta(hours=25)  # Past 24-hour expiration

            metadata = {
                "version": 1,
                "caches": {
                    "expired_cache": {
                        "fetched_at": expired.isoformat(),
                        "expires_at": expired.isoformat(),
                        "is_valid": True,
                    }
                },
            }
            write_json(metadata_file, metadata)

            assert not is_cache_valid("expired_cache")

    def test_is_cache_valid_nonexistent(self, temp_cache_dir: Path) -> None:
        """Test cache validation for nonexistent cache."""
        from oss_navi.utils.cache import is_cache_valid

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            assert not is_cache_valid("nonexistent_cache")

    def test_get_cache_age_hours(self, temp_cache_dir: Path) -> None:
        """Test getting cache age in hours."""
        from oss_navi.utils.cache import get_cache_age_hours, update_cache_metadata

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            update_cache_metadata("age_test")

            age = get_cache_age_hours("age_test")
            assert age is not None
            assert age < 1  # Should be very fresh

    def test_clear_cache_specific(self, temp_cache_dir: Path) -> None:
        """Test clearing specific cache."""
        from oss_navi.utils.cache import clear_cache, is_cache_valid, update_cache_metadata

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            update_cache_metadata("cache1")
            update_cache_metadata("cache2")

            clear_cache("cache1")

            assert not is_cache_valid("cache1")
            assert is_cache_valid("cache2")

    def test_clear_cache_all(self, temp_cache_dir: Path) -> None:
        """Test clearing all caches."""
        from oss_navi.utils.cache import clear_cache, is_cache_valid, update_cache_metadata

        with patch("oss_navi.utils.cache.CACHE_METADATA_FILE", temp_cache_dir / "metadata.json"):
            update_cache_metadata("cache1")
            update_cache_metadata("cache2")

            clear_cache()  # Clear all

            assert not is_cache_valid("cache1")
            assert not is_cache_valid("cache2")
