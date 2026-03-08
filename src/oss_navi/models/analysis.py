"""Code analysis models for detailed repository analysis."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from oss_navi.models.learning import Difficulty
from oss_navi.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    pass


class KeyFile(BaseModel):
    """A key file in a repository for understanding the codebase."""

    path: str = Field(..., description="File path relative to repository root")
    purpose: str = Field(..., description="Brief description of the file's purpose")
    lines_of_code: int | None = Field(None, description="Approximate lines of code")


class ContributionArea(BaseModel):
    """An area of the codebase suitable for contributions."""

    area: str = Field(..., description="Area name, e.g., 'API endpoints', 'Data models'")
    description: str | None = Field(None, description="Brief description")
    difficulty: Difficulty = Field(..., description="Contribution difficulty")
    good_for_beginners: bool = Field(default=False, description="Whether suitable for beginners")
    suggested_issues: list[str] = Field(
        default_factory=list,
        description="Suggested issue types for this area"
    )
    key_files: list[str] = Field(
        default_factory=list,
        description="Key files to understand this area"
    )


class CodeAnalysis(BaseModel):
    """Detailed analysis of a repository."""

    analysis_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique analysis identifier"
    )
    repository: str = Field(..., description="Repository name (owner/repo)")
    architecture_overview: str = Field(..., description="High-level architecture description")
    key_files: list[KeyFile] = Field(
        default_factory=list,
        description="Important files to understand the codebase"
    )
    contribution_areas: list[ContributionArea] = Field(
        default_factory=list,
        description="Areas suitable for contributions"
    )
    code_reading_hints: list[str] = Field(
        default_factory=list,
        description="Hints for reading the code"
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Technologies used"
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Prerequisites for contributing"
    )
    generated_at: datetime = Field(default_factory=utc_now)

    def to_markdown(self) -> str:
        """Convert analysis to markdown format."""
        lines = [
            f"# Code Analysis: {self.repository}",
            "",
            "## Architecture Overview",
            "",
            self.architecture_overview,
            "",
            "## Tech Stack",
            "",
            ", ".join(self.tech_stack) if self.tech_stack else "Not analyzed",
            "",
        ]

        if self.prerequisites:
            lines.extend([
                "## Prerequisites",
                "",
            ])
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")

        if self.key_files:
            lines.extend([
                "## Key Files",
                "",
            ])
            for kf in self.key_files:
                lines.append(f"- **`{kf.path}`**: {kf.purpose}")
                if kf.lines_of_code:
                    lines.append(f"  - ~{kf.lines_of_code} lines")
            lines.append("")

        if self.contribution_areas:
            lines.extend([
                "## Contribution Areas",
                "",
            ])
            for area in self.contribution_areas:
                beginner_tag = " ✓ beginner-friendly" if area.good_for_beginners else ""
                lines.append(f"### {area.area} ({area.difficulty.value}){beginner_tag}")
                if area.description:
                    lines.append(f"\n{area.description}\n")
                if area.suggested_issues:
                    lines.append("\n**Suggested issues:**")
                    for issue in area.suggested_issues:
                        lines.append(f"- {issue}")
                if area.key_files:
                    lines.append("\n**Key files:**")
                    for file in area.key_files:
                        lines.append(f"- `{file}`")
                lines.append("")

        if self.code_reading_hints:
            lines.extend([
                "## Code Reading Hints",
                "",
            ])
            for hint in self.code_reading_hints:
                lines.append(f"- {hint}")
            lines.append("")

        lines.append(f"\n*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M')}*")

        return "\n".join(lines)


class AnalysisRequest(BaseModel):
    """Request for detailed code analysis."""

    repository: str = Field(..., description="Repository to analyze (owner/repo)")
    focus_areas: list[str] | None = Field(
        None,
        description="Specific areas to focus on"
    )
    skill_level: Difficulty = Field(
        default=Difficulty.INTERMEDIATE,
        description="Target skill level for suggestions"
    )


class AnalysisSummary(BaseModel):
    """Summary of a code analysis for a session report."""

    repository: str = Field(..., description="Repository name")
    stars: int = Field(default=0, description="Repository stars")
    language: str = Field(default="Unknown", description="Primary language")
    key_areas: list[str] = Field(default_factory=list, description="Key contribution areas")
    beginner_friendly: bool = Field(default=False, description="Has beginner-friendly areas")
    analysis_id: str = Field(..., description="Full analysis ID for reference")

    def to_markdown(self) -> str:
        """Convert summary to markdown."""
        lines = [
            f"### {self.repository}",
            f"- Language: {self.language} | Stars: {self.stars:,}",
        ]
        if self.key_areas:
            lines.append(f"- Key areas: {', '.join(self.key_areas[:3])}")
        if self.beginner_friendly:
            lines.append("- ✓ Beginner-friendly contributions available")
        lines.append(f"- [View full analysis](#{self.analysis_id})")
        return "\n".join(lines)
