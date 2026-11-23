"""OAuth scope auditor for connectors (issue #385)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ScopeIssueSeverity(str, Enum):
    """Severity levels for scope-related issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ScopeIssueCategory(str, Enum):
    """Categories of scope issues."""

    MISSING_SCOPE = "missing_scope"
    DECLARED_BUT_UNUSED = "declared_but_unused"
    INVALID_SCOPE = "invalid_scope"


@dataclass
class ScopeIssue:
    """A scope-related issue found during auditing."""

    connector_id: str
    scope_name: str
    severity: ScopeIssueSeverity
    category: ScopeIssueCategory
    message: str
    required_by: str | None = None  # API or service that requires this scope
    remediation: str | None = None  # Suggested remediation step


@dataclass
class ScopeAuditResult:
    """Result of OAuth scope auditing."""

    connector_id: str
    declared_scopes: set[str]
    required_scopes: set[str]
    issues: list[ScopeIssue] = field(default_factory=list)
    missing_scopes: set[str] = field(default_factory=set)
    unused_scopes: set[str] = field(default_factory=set)
    extra_scopes: set[str] = field(default_factory=set)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == ScopeIssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == ScopeIssueSeverity.WARNING for i in self.issues)

    @property
    def has_missing(self) -> bool:
        return len(self.missing_scopes) > 0

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "declared_count": len(self.declared_scopes),
            "required_count": len(self.required_scopes),
            "missing_count": len(self.missing_scopes),
            "unused_count": len(self.unused_scopes),
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "has_missing": self.has_missing,
        }


def audit_scopes(
    connector_id: str,
    declared_scopes: list[str],
    required_scopes: list[str],
) -> ScopeAuditResult:
    """
    Check declared scopes against required API scopes for a connector.

    Args:
        connector_id: Identifier for the connector being audited
        declared_scopes: List of scopes declared by the connector
        required_scopes: List of scopes required by the API

    Returns:
        ScopeAuditResult with issues, missing, unused, and extra scopes
    """
    declared: set[str] = set(declared_scopes)
    required: set[str] = set(required_scopes)

    # Compute set differences
    missing_scopes: set[str] = required - declared
    unused_scopes: set[str] = declared - required

    issues: list[ScopeIssue] = []

    # Report missing scopes (required but not declared)
    for scope in sorted(missing_scopes):
        issues.append(
            ScopeIssue(
                connector_id=connector_id,
                scope_name=scope,
                severity=ScopeIssueSeverity.ERROR,
                category=ScopeIssueCategory.MISSING_SCOPE,
                message=f"Missing required scope: {scope}",
                remediation=f"Add scope '{scope}' to the connector's declared scopes",
            )
        )

    # Report unused/extra scopes (declared but not required)
    for scope in sorted(unused_scopes):
        issues.append(
            ScopeIssue(
                connector_id=connector_id,
                scope_name=scope,
                severity=ScopeIssueSeverity.WARNING,
                category=ScopeIssueCategory.DECLARED_BUT_UNUSED,
                message=f"Declared scope not required by API: {scope}",
                remediation=f"Consider removing unused scope '{scope}' from connector configuration",
            )
        )

    # Report invalid scopes (syntactically invalid or known bad)
    for scope in sorted(declared):
        if not _is_valid_scope_name(scope):
            issues.append(
                ScopeIssue(
                    connector_id=connector_id,
                    scope_name=scope,
                    severity=ScopeIssueSeverity.ERROR,
                    category=ScopeIssueCategory.INVALID_SCOPE,
                    message=f"Invalid scope name: {scope}",
                    remediation=f"Fix or remove invalid scope '{scope}'",
                )
            )

    result = ScopeAuditResult(
        connector_id=connector_id,
        declared_scopes=declared,
        required_scopes=required,
        issues=issues,
        missing_scopes=missing_scopes,
        unused_scopes=unused_scopes,
        extra_scopes=set()  # extra_scopes is same as unused_scopes conceptually
    )

    return result


def _is_valid_scope_name(scope: str) -> bool:
    """Validate an OAuth scope name format."""
    if not scope or not scope.strip():
        return False
    # OAuth scope names typically use dot-separated lowercase words
    # e.g., gmail.settings.basic, calendar.readonly, contacts.read
    import re
    pattern = r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*$"
    return bool(re.match(pattern, scope))
