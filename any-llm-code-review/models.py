"""Data models for code review."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ReviewComment(BaseModel):
    """A single code review comment."""

    path: str = Field(description="File path where the comment applies")
    line: int = Field(description="Line number for the comment")
    severity: Literal["info", "warning", "error"] = Field(
        description="Severity level of the issue"
    )
    category: str = Field(description="Category of the issue (e.g., 'bug', 'performance', 'security')")
    message: str = Field(description="The review comment message")
    suggestion: Optional[str] = Field(
        default=None, description="Optional suggested fix for the issue"
    )


class CodeReviewResponse(BaseModel):
    """Response from the AI code reviewer."""

    summary: str = Field(description="Overall summary of the code changes")
    comments: list[ReviewComment] = Field(
        default_factory=list, description="List of review comments"
    )
    approved: bool = Field(
        description="Whether the changes are approved (true if no errors found)"
    )
