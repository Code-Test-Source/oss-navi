"""Configuration management for OSS-Navi."""

import os
import stat

from pydantic import ValidationError

from oss_navi.models.config import Config
from oss_navi.utils.cache import read_json, write_json
from oss_navi.utils.paths import CONFIG_FILE, TOKEN_FILE, ensure_directories


def load_config() -> Config | None:
    """Load configuration from disk.

    Returns:
        Config object or None if not configured
    """
    ensure_directories()

    data = read_json(CONFIG_FILE)
    if not data:
        return None

    try:
        return Config(**data)
    except ValidationError:
        return None


def save_config(config: Config) -> None:
    """Save configuration to disk.

    Args:
        config: Configuration to save
    """
    ensure_directories()
    write_json(CONFIG_FILE, config.model_dump())


def get_github_token() -> str | None:
    """Get GitHub token from environment, file, or config.

    Priority:
    1. GITHUB_TOKEN environment variable
    2. .token file in OSS_NAVI_HOME
    3. Config file

    Returns:
        GitHub token or None if not set
    """
    # Check environment variable first
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    # Check token file
    if TOKEN_FILE.exists():
        try:
            token = TOKEN_FILE.read_text().strip()
            if token:
                return token
        except OSError:
            pass

    # Check config
    config = load_config()
    if config and config.github_token:
        return config.github_token

    return None


def save_github_token(token: str) -> None:
    """Save GitHub token securely.

    Stores the token in a file with 0600 permissions.

    Args:
        token: GitHub personal access token
    """
    ensure_directories()

    # Write token file with restricted permissions
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600 permissions


def validate_github_username(username: str) -> bool:
    """Validate GitHub username format.

    Args:
        username: Username to validate

    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False
    # GitHub usernames: 1-39 chars, alphanumeric and hyphens, no consecutive hyphens
    import re

    # Check length
    if len(username) > 39:
        return False

    # Check for consecutive hyphens
    if "--" in username:
        return False

    # Check format: alphanumeric with hyphens, cannot start or end with hyphen
    pattern = r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"
    return bool(re.match(pattern, username))


def validate_github_token(token: str) -> bool:
    """Validate GitHub token format.

    Args:
        token: Token to validate

    Returns:
        True if format looks valid, False otherwise
    """
    if not token:
        return False
    # GitHub tokens start with specific prefixes
    # Classic tokens: 40 hex chars
    # Fine-grained tokens: github_pat_...
    # OAuth tokens: gho_, ghu_, ghs_, ghr_
    if token.startswith("github_pat_"):
        return True
    if token.startswith(("gho_", "ghu_", "ghs_", "ghr_")):
        return True
    if len(token) == 40 and all(c in "0123456789abcdef" for c in token.lower()):
        return True
    return False


def reset_config() -> None:
    """Reset configuration to defaults."""
    ensure_directories()
    write_json(CONFIG_FILE, {})
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def get_proxy_settings() -> dict[str, str | None]:
    """Get proxy settings with environment variable precedence.

    Priority:
    1. Environment variables (HTTP_PROXY, HTTPS_PROXY, NO_PROXY)
    2. Config file settings

    Returns:
        Dict with 'http_proxy', 'https_proxy', and 'no_proxy' keys
    """
    config = load_config()

    http_env = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_env = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    no_proxy_env = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")

    return {
        "http_proxy": http_env or (config.http_proxy if config and config.http_proxy else None),
        "https_proxy": https_env or (config.https_proxy if config and config.https_proxy else None),
        "no_proxy": no_proxy_env or (config.no_proxy if config and config.no_proxy else None),
    }


def should_verify_ssl() -> bool:
    """Check if SSL verification should be enabled.

    Set OSS_NAVI_VERIFY_SSL=false to disable SSL verification (useful for
    proxies with self-signed certificates). For better security, prefer
    configuring a custom CA bundle via the SSL_CERT_FILE or SSL_CERT_DIR
    environment variables rather than disabling verification entirely.

    Returns:
        True if SSL verification should be enabled, False otherwise
    """
    verify_ssl = os.environ.get("OSS_NAVI_VERIFY_SSL", "true").lower()
    return verify_ssl not in ("false", "0", "no")
