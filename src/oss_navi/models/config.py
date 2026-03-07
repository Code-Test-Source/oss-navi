"""Configuration models for OSS-Navi."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# GitHub token prefixes
GITHUB_TOKEN_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_", "github_pat_")


class Filters(BaseModel):
    """Task filtering configuration."""

    min_stars: int = Field(default=50, ge=0, le=1000000)
    max_age_days: int = Field(default=90, ge=1, le=365)
    limit: int = Field(default=100, ge=1, le=1000)


class Config(BaseModel):
    """User configuration for OSS-Navi."""

    github_username: str | None = None
    github_token: str | None = Field(default=None, exclude=True)  # Never serialize token
    blog_repo_path: str | None = None
    filters: Filters = Field(default_factory=Filters)
    # Proxy settings
    http_proxy: str | None = None
    https_proxy: str | None = None
    no_proxy: str | None = None  # Comma-separated list of hosts to bypass proxy
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("github_username")
    @classmethod
    def validate_github_username(cls, v: str | None) -> str | None:
        """Validate GitHub username format.

        Rules:
        - 1-39 characters
        - Alphanumeric and hyphens only
        - Cannot start or end with hyphen
        - No consecutive hyphens
        """
        if v is None:
            return None
        if len(v) > 39:
            raise ValueError("GitHub username must be 39 characters or less")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("GitHub username cannot start or end with a hyphen")
        if "--" in v:
            raise ValueError("GitHub username cannot contain consecutive hyphens")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError(
                "GitHub username must contain only alphanumeric characters and hyphens"
            )
        return v

    @field_validator("blog_repo_path")
    @classmethod
    def validate_blog_repo_path(cls, v: str | None) -> str | None:
        """Validate blog repository path if provided."""
        if v is None:
            return None
        # Allow path validation to be optional during creation
        return v


def validate_github_token(token: str) -> str:
    """Validate GitHub token format.

    Raises:
        ValueError: If token format is invalid
    """
    if not token:
        raise ValueError("GitHub token cannot be empty")
    # Accept various token formats
    valid_prefixes = GITHUB_TOKEN_PREFIXES
    # Also accept classic 40-char hex tokens
    is_hex_token = len(token) == 40 and all(c in "0123456789abcdefABCDEF" for c in token)
    if not token.startswith(valid_prefixes) and not is_hex_token:
        raise ValueError(
            f"Invalid GitHub token format. Token must start with one of: {', '.join(valid_prefixes)} "
            "or be a 40-character hex token"
        )
    return token
