"""Unit tests for Config and Filters models."""

import pytest
from pydantic import ValidationError

from oss_navi.models.config import Config, Filters, validate_github_token


class TestFilters:
    """Tests for Filters model."""

    def test_create_filters_defaults(self) -> None:
        """Test creating Filters with default values."""
        filters = Filters()
        assert filters.min_stars == 50
        assert filters.max_age_days == 90
        assert filters.limit == 100

    def test_create_filters_custom(self) -> None:
        """Test creating Filters with custom values."""
        filters = Filters(min_stars=100, max_age_days=30, limit=50)
        assert filters.min_stars == 100
        assert filters.max_age_days == 30
        assert filters.limit == 50

    def test_filters_validation_min_stars(self) -> None:
        """Test min_stars validation."""
        with pytest.raises(ValidationError):
            Filters(min_stars=-1)

    def test_filters_validation_max_age(self) -> None:
        """Test max_age_days validation."""
        with pytest.raises(ValidationError):
            Filters(max_age_days=0)


class TestConfig:
    """Tests for Config model."""

    def test_create_config_minimal(self) -> None:
        """Test creating Config with minimal required fields."""
        config = Config()
        assert config.github_username is None
        assert config.blog_repo_path is None

    def test_create_config_with_username(self) -> None:
        """Test creating Config with GitHub username."""
        config = Config(github_username="testuser")
        assert config.github_username == "testuser"

    def test_config_invalid_username_hyphen_start(self) -> None:
        """Test that username cannot start with hyphen."""
        with pytest.raises(ValidationError):
            Config(github_username="-testuser")

    def test_config_invalid_username_hyphen_end(self) -> None:
        """Test that username cannot end with hyphen."""
        with pytest.raises(ValidationError):
            Config(github_username="testuser-")

    def test_config_invalid_username_consecutive_hyphens(self) -> None:
        """Test that username cannot have consecutive hyphens."""
        with pytest.raises(ValidationError):
            Config(github_username="test--user")

    def test_config_invalid_username_too_long(self) -> None:
        """Test that username cannot exceed 39 characters."""
        with pytest.raises(ValidationError):
            Config(github_username="a" * 40)


class TestValidateGitHubToken:
    """Tests for GitHub token validation."""

    def test_validate_fine_grained_token(self) -> None:
        """Test validating fine-grained token."""
        token = validate_github_token("github_pat_test_token_here")
        assert token == "github_pat_test_token_here"

    def test_validate_oauth_token(self) -> None:
        """Test validating OAuth token."""
        token = validate_github_token("gho_test_token")
        assert token == "gho_test_token"

    def test_validate_classic_hex_token(self) -> None:
        """Test validating classic hex token."""
        token = validate_github_token("0123456789abcdef0123456789abcdef01234567")
        assert token == "0123456789abcdef0123456789abcdef01234567"

    def test_validate_empty_token(self) -> None:
        """Test that empty token raises error."""
        with pytest.raises(ValueError):
            validate_github_token("")

    def test_validate_invalid_token_format(self) -> None:
        """Test that invalid token format raises error."""
        with pytest.raises(ValueError):
            validate_github_token("invalid_token_format")
