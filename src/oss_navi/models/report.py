"""Analysis report models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisReport(BaseModel):
    """Generated Markdown report with recommendations."""

    id: str  # Format: YYYYMMDD_HHMMSS
    created_at: datetime
    content: str
    file_path: str
    learning_focus: Optional[str] = None
    recommended_projects: list[str] = Field(default_factory=list)

    @staticmethod
    def generate_report_id() -> str:
        """Generate a timestamp-based report ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
