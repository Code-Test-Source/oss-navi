"""User preferences models for personalization."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from oss_navi.utils.datetime_utils import utc_now


class SkillLevel(StrEnum):
    """User skill level for a language."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LanguageType(StrEnum):
    """Type of language in user profile."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    LEARNING = "learning"


class BlockType(StrEnum):
    """Type of blocking rule."""

    PROJECT = "project"  # Block specific repository
    MAINTAINER = "maintainer"  # Block by maintainer username
    ORGANIZATION = "organization"  # Block by org name
    TOPIC = "topic"  # Block by topic/tag
    LANGUAGE = "language"  # Block by language


class LanguageProfile(BaseModel):
    """User's profile for a specific language."""

    language: str = Field(..., description="Programming language name, e.g., 'python', 'rust'")
    type: LanguageType = Field(..., description="How the language relates to the user")
    skill_level: SkillLevel = Field(..., description="User's skill level in this language")


class DomainInterest(BaseModel):
    """User's interest in a specific domain."""

    domain: str = Field(..., description="Domain name, e.g., 'web', 'ml', 'systems', 'devops'")
    interest_level: int = Field(..., ge=1, le=10, description="Interest level on 1-10 scale")


class BlockingRule(BaseModel):
    """A rule to exclude specific projects from recommendations."""

    block_type: BlockType = Field(..., description="Type of blocking rule")
    value: str = Field(..., description="The value to block")
    reason: str | None = Field(None, description="Optional user-provided reason for blocking")
    created_at: datetime = Field(default_factory=utc_now, description="When the rule was created")

    def matches(self, project: dict) -> bool:
        """Check if a project matches this blocking rule.

        Args:
            project: Project dictionary with 'owner', 'name', 'language', 'topics' keys

        Returns:
            True if the project matches this blocking rule
        """
        match self.block_type:
            case BlockType.PROJECT:
                full_name = f"{project.get('owner', '')}/{project.get('name', '')}"
                return self.value.lower() == full_name.lower()
            case BlockType.MAINTAINER:
                return self.value.lower() == project.get("owner", "").lower()
            case BlockType.ORGANIZATION:
                return self.value.lower() == project.get("owner", "").lower()
            case BlockType.TOPIC:
                topics = [t.lower() for t in project.get("topics", [])]
                return self.value.lower() in topics
            case BlockType.LANGUAGE:
                project_lang = project.get("language", "").lower()
                return self.value.lower() == project_lang
            case _:
                return False


class UserPreferences(BaseModel):
    """User's preferences including languages, interests, and blocking rules."""

    languages: list[LanguageProfile] = Field(default_factory=list, description="User's language profiles")
    domain_interests: list[DomainInterest] = Field(default_factory=list, description="User's domain interests")
    blocking_rules: list[BlockingRule] = Field(default_factory=list, description="User's blocking rules")
    default_mode: str = Field(default="normal", description="Default recommendation mode")
    created_at: datetime = Field(default_factory=utc_now, description="When preferences were created")
    updated_at: datetime = Field(default_factory=utc_now, description="When preferences were last updated")

    def get_primary_languages(self) -> list[str]:
        """Get list of primary language names."""
        return [lp.language for lp in self.languages if lp.type == LanguageType.PRIMARY]

    def get_secondary_languages(self) -> list[str]:
        """Get list of secondary language names."""
        return [lp.language for lp in self.languages if lp.type == LanguageType.SECONDARY]

    def get_learning_languages(self) -> list[str]:
        """Get list of learning language names."""
        return [lp.language for lp in self.languages if lp.type == LanguageType.LEARNING]

    def get_all_languages(self) -> list[str]:
        """Get all language names from the profile."""
        return [lp.language for lp in self.languages]

    def get_language_skill(self, language: str) -> SkillLevel | None:
        """Get skill level for a specific language."""
        for lp in self.languages:
            if lp.language.lower() == language.lower():
                return lp.skill_level
        return None

    def is_blocked(self, project: dict) -> bool:
        """Check if a project is blocked by any rule.

        Args:
            project: Project dictionary with 'owner', 'name', 'language', 'topics' keys

        Returns:
            True if the project is blocked by any rule
        """
        return any(rule.matches(project) for rule in self.blocking_rules)

    def get_block_reason(self, project: dict) -> str | None:
        """Get the reason a project is blocked, if any."""
        for rule in self.blocking_rules:
            if rule.matches(project):
                return rule.reason or f"Blocked by {rule.block_type.value}: {rule.value}"
        return None
