"""OAuth scope auditor API routes (issue #385)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.oauth_scope_auditor import (
    ScopeIssue,
    ScopeIssueCategory,
    ScopeIssueSeverity,
    ScopeAuditResult,
    _is_valid_scope_name,
    audit_scopes,
)


router = APIRouter(prefix="/oauth-scope", tags=["oauth-scope"])


class ScopeIssueResponse(BaseModel):
    """API response model for a scope issue."""

    connector_id: str
    scope_name: str
    severity: str
    category: str
    message: str
    required_by: str | None = None
    remediation: str | None = None


class AuditScopesRequest(BaseModel):
    """Request model for scope auditing."""

    connector_id: str = Field(..., description="Connector identifier")
    declared_scopes: list[str] = Field(
        ..., description="List of scopes declared by the connector"
    )
    required_scopes: list[str] = Field(
        ..., description="List of scopes required by the API"
    )


class AuditScopesResponse(BaseModel):
    """Response model for scope audit results."""

    result: ScopeAuditResult
    issues: list[ScopeIssueResponse]


def _issue_to_response(issue: ScopeIssue) -> ScopeIssueResponse:
    """Convert internal ScopeIssue to API response model."""
    return ScopeIssueResponse(
        connector_id=issue.connector_id,
        scope_name=issue.scope_name,
        severity=issue.severity.value,
        category=issue.category.value,
        message=issue.message,
        required_by=issue.required_by,
        remediation=issue.remediation,
    )


@router.post("/audit", response_model=AuditScopesResponse)
async def audit_scopes_endpoint(request: AuditScopesRequest) -> AuditScopesResponse:
    """Audit declared scopes against required API scopes for a connector."""
    try:
        result: ScopeAuditResult = audit_scopes(
            connector_id=request.connector_id,
            declared_scopes=request.declared_scopes,
            required_scopes=request.required_scopes,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to audit scopes: {e}"
        )

    return AuditScopesResponse(
        result=result,
        issues=[_issue_to_response(issue) for issue in result.issues],
    )


@router.get("/health")
async def oauth_scope_health() -> dict:
    """Health check for OAuth scope auditor service."""
    return {"status": "ok", "service": "oauth-scope-auditor"}
