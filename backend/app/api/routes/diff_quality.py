"""Diff quality analyzer API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.diff_quality_analyzer import (
    DiffAnalysisResult,
    DiffIssue,
    IssueSeverity,
    analyze_diff,
    analyze_diff_file,
)

router = APIRouter(prefix="/diff-quality", tags=["diff-quality"])


class DiffIssueResponse(BaseModel):
    """API response model for a diff issue."""

    file_path: str
    line_number: int | None
    severity: str
    category: str
    message: str
    context: str | None = None


class AnalyzeDiffRequest(BaseModel):
    """Request model for diff analysis."""

    diff_text: str = Field(..., description="Unified diff text to analyze")


class AnalyzeDiffResponse(BaseModel):
    """Response model for diff analysis."""

    issues: list[DiffIssueResponse]
    stats: dict
    has_errors: bool
    has_warnings: bool


def _issue_to_response(issue: DiffIssue) -> DiffIssueResponse:
    """Convert internal DiffIssue to API response model."""
    return DiffIssueResponse(
        file_path=issue.file_path,
        line_number=issue.line_number,
        severity=issue.severity.value,
        category=issue.category,
        message=issue.message,
        context=issue.context,
    )


@router.post("/analyze", response_model=AnalyzeDiffResponse)
async def analyze_diff_endpoint(request: AnalyzeDiffRequest) -> AnalyzeDiffResponse:
    """Analyze a unified diff for quality issues."""
    try:
        result: DiffAnalysisResult = analyze_diff(request.diff_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse diff: {e}")

    return AnalyzeDiffResponse(
        issues=[_issue_to_response(issue) for issue in result.issues],
        stats=result.stats,
        has_errors=result.has_errors,
        has_warnings=result.has_warnings,
    )


@router.get("/health")
async def diff_quality_health() -> dict:
    """Health check for diff quality analyzer service."""
    return {"status": "ok", "service": "diff-quality-analyzer"}
