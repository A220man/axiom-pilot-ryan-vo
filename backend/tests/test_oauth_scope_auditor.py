"""Tests for OAuth scope auditor service."""
from __future__ import annotations

import pytest

from app.services.oauth_scope_auditor import (
    ScopeIssue,
    ScopeIssueCategory,
    ScopeIssueSeverity,
    ScopeAuditResult,
    _is_valid_scope_name,
    audit_scopes,
)


class TestScopeIssue:
    """Tests for ScopeIssue dataclass."""

    def test_scope_issue_creation(self) -> None:
        """Test creating a ScopeIssue instance."""
        issue = ScopeIssue(
            connector_id="test-connector",
            scope_name="gmail.readonly",
            severity=ScopeIssueSeverity.ERROR,
            category=ScopeIssueCategory.MISSING_SCOPE,
            message="Test message",
        )
        assert issue.connector_id == "test-connector"
        assert issue.scope_name == "gmail.readonly"
        assert issue.severity == ScopeIssueSeverity.ERROR
        assert issue.category == ScopeIssueCategory.MISSING_SCOPE
        assert issue.message == "Test message"
        assert issue.required_by is None
        assert issue.remediation is None

    def test_scope_issue_with_remediation(self) -> None:
        """Test creating a ScopeIssue with remediation."""
        issue = ScopeIssue(
            connector_id="test-connector",
            scope_name="gmail.settings.basic",
            severity=ScopeIssueSeverity.ERROR,
            category=ScopeIssueCategory.MISSING_SCOPE,
            message="Missing required scope: gmail.settings.basic",
            required_by="Google Gmail API",
            remediation="Add scope 'gmail.settings.basic' to the connector's declared scopes",
        )
        assert issue.required_by == "Google Gmail API"
        assert issue.remediation is not None


class TestScopeAuditResult:
    """Tests for ScopeAuditResult dataclass."""

    def test_audit_result_via_audit_scopes(self) -> None:
        """Test ScopeAuditResult created via audit_scopes has correct has_missing."""
        result = audit_scopes(
            connector_id="test-connector",
            declared_scopes=["gmail.readonly"],
            required_scopes=["gmail.readonly", "gmail.settings.basic", "calendar.read"],
        )
        assert result.connector_id == "test-connector"
        assert result.has_missing is True
        assert result.summary["missing_count"] == 2
        assert result.has_errors is True

    def test_audit_result_no_missing(self) -> None:
        """Test audit result when all scopes are declared."""
        result = audit_scopes(
            connector_id="test-connector",
            declared_scopes=["gmail.readonly", "gmail.settings.basic", "calendar.read"],
            required_scopes=["gmail.readonly", "gmail.settings.basic", "calendar.read"],
        )
        assert result.has_missing is False
        assert result.summary["missing_count"] == 0
        assert result.has_errors is False


class TestIsValidScopeName:
    """Tests for _is_valid_scope_name helper."""

    def test_valid_scope_simple(self) -> None:
        """Test valid simple scope name."""
        assert _is_valid_scope_name("gmail.readonly") is True

    def test_valid_scope_with_dots(self) -> None:
        """Test valid scope name with multiple dots."""
        assert _is_valid_scope_name("calendar.readonly") is True

    def test_valid_scope_single_word(self) -> None:
        """Test valid single-word scope name."""
        assert _is_valid_scope_name("openid") is True

    def test_invalid_empty_scope(self) -> None:
        """Test invalid empty scope name."""
        assert _is_valid_scope_name("") is False

    def test_invalid_uppercase(self) -> None:
        """Test invalid uppercase scope name."""
        assert _is_valid_scope_name("Gmail.Readonly") is False

    def test_invalid_special_chars(self) -> None:
        """Test invalid scope with special characters."""
        assert _is_valid_scope_name("gmail!readonly") is False


class TestAuditScopes:
    """Tests for audit_scopes function."""

    def test_audit_with_missing_scopes(self) -> None:
        """Test auditing scopes with missing required scopes."""
        result = audit_scopes(
            connector_id="gmail-connector",
            declared_scopes=["gmail.readonly"],
            required_scopes=["gmail.readonly", "gmail.settings.basic"],
        )
        assert result.connector_id == "gmail-connector"
        assert result.has_missing is True
        assert result.missing_scopes == {"gmail.settings.basic"}
        assert len(result.issues) == 1
        assert result.issues[0].severity == ScopeIssueSeverity.ERROR
        assert result.issues[0].category == ScopeIssueCategory.MISSING_SCOPE
        assert "gmail.settings.basic" in result.issues[0].message

    def test_audit_with_unused_scopes(self) -> None:
        """Test auditing scopes with declared but unused scopes."""
        result = audit_scopes(
            connector_id="calendar-connector",
            declared_scopes=["gmail.readonly", "calendar.read", "unused.scope"],
            required_scopes=["gmail.readonly", "calendar.read"],
        )
        assert result.unused_scopes == {"unused.scope"}
        assert len(result.issues) > 0

    def test_audit_all_scopes_declared(self) -> None:
        """Test auditing when all required scopes are declared."""
        result = audit_scopes(
            connector_id="full-connector",
            declared_scopes=["gmail.readonly", "gmail.settings.basic", "calendar.read"],
            required_scopes=["gmail.readonly", "gmail.settings.basic", "calendar.read"],
        )
        assert result.has_missing is False
        assert result.missing_scopes == set()
        assert result.has_errors is False
        assert len(result.issues) == 0

    def test_audit_connector_id_carrythrough(self) -> None:
        """Test that connector_id is carried through in results."""
        result = audit_scopes(
            connector_id="specific-connector-123",
            declared_scopes=["scope1"],
            required_scopes=["scope1", "scope2"],
        )
        assert result.connector_id == "specific-connector-123"
