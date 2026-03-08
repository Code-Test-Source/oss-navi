"""Tests for preferences models."""

import pytest

from oss_navi.models.preferences import (
    BlockingRule,
    BlockType,
    DomainInterest,
    LanguageProfile,
    LanguageType,
    SkillLevel,
    UserPreferences,
)


class TestSkillLevel:
    """Tests for SkillLevel enum."""

    def test_skill_level_values(self) -> None:
        """Test SkillLevel enum values."""
        assert SkillLevel.BEGINNER.value == "beginner"
        assert SkillLevel.INTERMEDIATE.value == "intermediate"
        assert SkillLevel.ADVANCED.value == "advanced"


class TestLanguageType:
    """Tests for LanguageType enum."""

    def test_language_type_values(self) -> None:
        """Test LanguageType enum values."""
        assert LanguageType.PRIMARY.value == "primary"
        assert LanguageType.SECONDARY.value == "secondary"
        assert LanguageType.LEARNING.value == "learning"


class TestBlockType:
    """Tests for BlockType enum."""

    def test_block_type_values(self) -> None:
        """Test BlockType enum values."""
        assert BlockType.PROJECT.value == "project"
        assert BlockType.MAINTAINER.value == "maintainer"
        assert BlockType.ORGANIZATION.value == "organization"
        assert BlockType.TOPIC.value == "topic"
        assert BlockType.LANGUAGE.value == "language"


class TestLanguageProfile:
    """Tests for LanguageProfile model."""

    def test_create_language_profile(self) -> None:
        """Test creating a LanguageProfile."""
        profile = LanguageProfile(
            language="python",
            type=LanguageType.PRIMARY,
            skill_level=SkillLevel.ADVANCED,
        )
        assert profile.language == "python"
        assert profile.type == LanguageType.PRIMARY
        assert profile.skill_level == SkillLevel.ADVANCED


class TestDomainInterest:
    """Tests for DomainInterest model."""

    def test_create_domain_interest(self) -> None:
        """Test creating a DomainInterest."""
        interest = DomainInterest(
            domain="web",
            interest_level=8,
        )
        assert interest.domain == "web"
        assert interest.interest_level == 8

    def test_interest_level_validation(self) -> None:
        """Test interest_level must be 1-10."""
        from pydantic_core import ValidationError

        with pytest.raises(ValidationError):
            DomainInterest(domain="web", interest_level=0)

        with pytest.raises(ValidationError):
            DomainInterest(domain="web", interest_level=11)


class TestBlockingRule:
    """Tests for BlockingRule model."""

    def test_create_blocking_rule(self) -> None:
        """Test creating a BlockingRule."""
        rule = BlockingRule(
            block_type=BlockType.LANGUAGE,
            value="java",
            reason="Not interested",
        )
        assert rule.block_type == BlockType.LANGUAGE
        assert rule.value == "java"
        assert rule.reason == "Not interested"

    def test_matches_project(self) -> None:
        """Test matches method for different block types."""
        # Use nested repository structure (actual data format)
        project = {
            "repository": {
                "name": "octocat/Hello-World",
                "language": "Python",
                "topics": ["web", "api"],
            }
        }

        # PROJECT type
        rule = BlockingRule(block_type=BlockType.PROJECT, value="octocat/Hello-World")
        assert rule.matches(project) is True

        # Case insensitive
        rule = BlockingRule(block_type=BlockType.PROJECT, value="OCTOCAT/hello-world")
        assert rule.matches(project) is True

        # MAINTAINER type
        rule = BlockingRule(block_type=BlockType.MAINTAINER, value="octocat")
        assert rule.matches(project) is True

        # ORGANIZATION type
        rule = BlockingRule(block_type=BlockType.ORGANIZATION, value="octocat")
        assert rule.matches(project) is True

        # TOPIC type
        rule = BlockingRule(block_type=BlockType.TOPIC, value="web")
        assert rule.matches(project) is True

        # LANGUAGE type
        rule = BlockingRule(block_type=BlockType.LANGUAGE, value="python")
        assert rule.matches(project) is True

    def test_matches_no_match(self) -> None:
        """Test matches returns False when no match."""
        project = {
            "repository": {
                "name": "octocat/Hello-World",
                "language": "Python",
                "topics": ["web"],
            }
        }
        rule = BlockingRule(block_type=BlockType.LANGUAGE, value="java")
        assert rule.matches(project) is False


class TestUserPreferences:
    """Tests for UserPreferences model."""

    def test_create_user_preferences(self) -> None:
        """Test creating UserPreferences."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(
                    language="python",
                    type=LanguageType.PRIMARY,
                    skill_level=SkillLevel.ADVANCED,
                ),
            ],
            domain_interests=[
                DomainInterest(domain="web", interest_level=7),
            ],
            default_mode="fast",
        )
        assert len(prefs.languages) == 1
        assert len(prefs.domain_interests) == 1
        assert prefs.default_mode == "fast"

    def test_get_primary_languages(self) -> None:
        """Test get_primary_languages method."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
                LanguageProfile(language="javascript", type=LanguageType.SECONDARY, skill_level=SkillLevel.INTERMEDIATE),
                LanguageProfile(language="rust", type=LanguageType.LEARNING, skill_level=SkillLevel.BEGINNER),
            ],
        )
        primary = prefs.get_primary_languages()
        assert primary == ["python"]

    def test_get_secondary_languages(self) -> None:
        """Test get_secondary_languages method."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
                LanguageProfile(language="javascript", type=LanguageType.SECONDARY, skill_level=SkillLevel.INTERMEDIATE),
            ],
        )
        secondary = prefs.get_secondary_languages()
        assert secondary == ["javascript"]

    def test_get_learning_languages(self) -> None:
        """Test get_learning_languages method."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(language="rust", type=LanguageType.LEARNING, skill_level=SkillLevel.BEGINNER),
            ],
        )
        learning = prefs.get_learning_languages()
        assert learning == ["rust"]

    def test_get_all_languages(self) -> None:
        """Test get_all_languages method."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
                LanguageProfile(language="rust", type=LanguageType.LEARNING, skill_level=SkillLevel.BEGINNER),
            ],
        )
        all_langs = prefs.get_all_languages()
        assert set(all_langs) == {"python", "rust"}

    def test_get_language_skill(self) -> None:
        """Test get_language_skill method."""
        prefs = UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
            ],
        )
        assert prefs.get_language_skill("python") == SkillLevel.ADVANCED
        assert prefs.get_language_skill("java") is None
        # Case insensitive
        assert prefs.get_language_skill("PYTHON") == SkillLevel.ADVANCED

    def test_is_blocked(self) -> None:
        """Test is_blocked method."""
        prefs = UserPreferences(
            blocking_rules=[
                BlockingRule(block_type=BlockType.LANGUAGE, value="java"),
            ],
        )
        blocked_project = {"owner": "test", "name": "project", "language": "Java"}
        allowed_project = {"owner": "test", "name": "project", "language": "Python"}

        assert prefs.is_blocked(blocked_project) is True
        assert prefs.is_blocked(allowed_project) is False

    def test_get_block_reason(self) -> None:
        """Test get_block_reason method."""
        prefs = UserPreferences(
            blocking_rules=[
                BlockingRule(
                    block_type=BlockType.LANGUAGE,
                    value="java",
                    reason="Not interested in Java",
                ),
            ],
        )
        project = {"owner": "test", "name": "project", "language": "Java"}
        reason = prefs.get_block_reason(project)
        assert reason == "Not interested in Java"

    def test_get_block_reason_no_reason(self) -> None:
        """Test get_block_reason with no custom reason."""
        prefs = UserPreferences(
            blocking_rules=[
                BlockingRule(block_type=BlockType.LANGUAGE, value="java"),
            ],
        )
        project = {"owner": "test", "name": "project", "language": "Java"}
        reason = prefs.get_block_reason(project)
        assert "language" in reason.lower()
        assert "java" in reason.lower()
