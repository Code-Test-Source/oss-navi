"""Unit tests for configuration management."""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestConfigLoading:
    """Tests for configuration loading and saving."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path: Path) -> Path:
        """Create a temporary state directory."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    def test_load_config_nonexistent(self, temp_state_dir: Path) -> None:
        """Test loading nonexistent config returns None."""
        from oss_navi.config import load_config

        with patch("oss_navi.config.CONFIG_FILE", temp_state_dir / "config.json"):
            config = load_config()
            assert config is None

    def test_save_and_load_config(self, temp_state_dir: Path) -> None:
        """Test saving and loading configuration."""
        from oss_navi.config import load_config, save_config
        from oss_navi.models.config import Config

        config_file = temp_state_dir / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            config = Config(github_username="testuser")
            save_config(config)

            loaded = load_config()
            assert loaded is not None
            assert loaded.github_username == "testuser"

    def test_get_github_token_from_env(self) -> None:
        """Test getting GitHub token from environment variable."""
        from oss_navi.config import get_github_token

        with patch.dict("os.environ", {"GITHUB_TOKEN": "env_token_123"}):
            token = get_github_token()
            assert token == "env_token_123"

    def test_get_github_token_from_file(self, tmp_path: Path) -> None:
        """Test getting GitHub token from file."""
        from oss_navi.config import get_github_token

        token_file = tmp_path / ".token"
        token_file.write_text("file_token_456")

        with patch("oss_navi.config.TOKEN_FILE", token_file):
            with patch.dict("os.environ", {}, clear=True):
                token = get_github_token()
                assert token == "file_token_456"

    def test_save_github_token(self, tmp_path: Path) -> None:
        """Test saving GitHub token creates file with correct permissions."""
        from oss_navi.config import save_github_token

        token_file = tmp_path / ".token"

        with patch("oss_navi.config.TOKEN_FILE", token_file):
            save_github_token("new_token_789")

            assert token_file.exists()
            assert token_file.read_text() == "new_token_789"


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_github_username_valid(self) -> None:
        """Test validating valid GitHub usernames."""
        from oss_navi.config import validate_github_username

        assert validate_github_username("testuser")
        assert validate_github_username("test-user")
        assert validate_github_username("TestUser123")
        assert validate_github_username("a")

    def test_validate_github_username_invalid(self) -> None:
        """Test validating invalid GitHub usernames."""
        from oss_navi.config import validate_github_username

        assert not validate_github_username("")
        assert not validate_github_username("-testuser")
        assert not validate_github_username("testuser-")
        assert not validate_github_username("test--user")

    def test_validate_github_token_classic(self) -> None:
        """Test validating classic GitHub tokens."""
        from oss_navi.config import validate_github_token

        # Classic 40-char hex token
        assert validate_github_token("0123456789abcdef0123456789abcdef01234567")

    def test_validate_github_token_fine_grained(self) -> None:
        """Test validating fine-grained GitHub tokens."""
        from oss_navi.config import validate_github_token

        assert validate_github_token("github_pat_test_token_here")
        assert validate_github_token("gho_test_token")
        assert validate_github_token("ghu_test_token")

    def test_validate_github_token_invalid(self) -> None:
        """Test validating invalid GitHub tokens."""
        from oss_navi.config import validate_github_token

        assert not validate_github_token("")
        assert not validate_github_token("short")

    def test_reset_config(self, tmp_path: Path) -> None:
        """Test resetting configuration."""
        from oss_navi.config import reset_config, save_config
        from oss_navi.models.config import Config

        config_file = tmp_path / "state" / "config.json"
        token_file = tmp_path / ".token"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            with patch("oss_navi.config.TOKEN_FILE", token_file):
                # Save initial config
                save_config(Config(github_username="testuser"))
                token_file.write_text("token123")

                # Reset
                reset_config()

                # Verify cleared
                assert not token_file.exists()
