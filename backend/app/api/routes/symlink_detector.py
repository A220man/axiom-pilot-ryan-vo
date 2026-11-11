"""Symlink detector API routes."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pathlib import Path

from app.services.symlink_detector import (
    SymlinkIssue,
    SymlinkScanResult,
    scan_for_symlinks,
    get_default_plugins_path,
)

router = APIRouter(prefix="/symlinks", tags=["symlink-detector"])


class SymlinkIssueResponse(BaseModel):
    """API response model for a symlink issue."""

    plugin_name: str
    plugin_path: str
    issue_type: str
    message: str
    target_path: str | None = None
    suggestion: str | None = None


class ScanSymlinksRequest(BaseModel):
    """Request model for symlink scanning."""

    plugins_path: str | None = Field(
        None, description="Custom path to scan (defaults to ~/.cursor/plugins/local)"
    )


class ScanSymlinksResponse(BaseModel):
    """Response model for symlink scan."""

    scanned_path: str
    total_plugins: int
    symlinked_plugins: list[str]
    broken_symlinks: list[str]
    issues: list[SymlinkIssueResponse]
    has_issues: bool
    has_symlinks: bool
    has_broken: bool


def _issue_to_response(issue: SymlinkIssue) -> SymlinkIssueResponse:
    """Convert internal SymlinkIssue to API response model."""
    return SymlinkIssueResponse(
        plugin_name=issue.plugin_name,
        plugin_path=issue.plugin_path,
        issue_type=issue.issue_type,
        message=issue.message,
        target_path=issue.target_path,
        suggestion=issue.suggestion,
    )


@router.post("/scan", response_model=ScanSymlinksResponse)
async def scan_symlinks_endpoint(request: ScanSymlinksRequest) -> ScanSymlinksResponse:
    """Scan the local plugins directory for symlinks."""
    try:
        plugins_path = Path(request.plugins_path) if request.plugins_path else None
        result: SymlinkScanResult = scan_for_symlinks(plugins_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scan for symlinks: {e}")

    return ScanSymlinksResponse(
        scanned_path=result.scanned_path,
        total_plugins=result.total_plugins,
        symlinked_plugins=result.symlinked_plugins,
        broken_symlinks=result.broken_symlinks,
        issues=[_issue_to_response(issue) for issue in result.issues],
        has_issues=result.has_issues,
        has_symlinks=result.has_symlinks,
        has_broken=result.has_broken,
    )


@router.get("/health")
async def symlink_detector_health() -> dict:
    """Health check for symlink detector service."""
    return {"status": "ok", "service": "symlink-detector"}
