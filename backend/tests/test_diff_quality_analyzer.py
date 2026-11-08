"""Tests for diff quality analyzer service."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.services.diff_quality_analyzer import (
    DiffAnalysisResult,
    DiffIssue,
    IssueSeverity,
    analyze_diff,
    analyze_diff_file,
)


class TestDiffParser:
    """Tests for DiffParser line number tracking."""

    def test_parse_simple_diff(self) -> None:
        """Test parsing a simple unified diff."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    import os
     print(\"hello\")
     return 42
"""
        result = analyze_diff(diff)
        assert isinstance(result, DiffAnalysisResult)
        assert len(result.issues) >= 1
        # Should detect import line
        import_issues = [i for i in result.issues if i.category == "import-filtering"]
        assert len(import_issues) >= 1
        assert import_issues[0].line_number == 2

    def test_parse_multi_hunk_diff(self) -> None:
        """Test parsing a diff with multiple hunks."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    import os
     print(\"hello\")
     return 42
@@ -10,3 +11,4 @@
 def world():
+    from sys import path
     print(\"world\")
     return 24
"""
        result = analyze_diff(diff)
        import_issues = [i for i in result.issues if i.category == "import-filtering"]
        assert len(import_issues) == 2
        # First hunk import at line 2
        assert import_issues[0].line_number == 2
        # Second hunk import at line 12
        assert import_issues[1].line_number == 12

    def test_whitespace_only_change_detection(self) -> None:
        """Test detection of whitespace-only changes."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 def hello():
-    print(\"hello\")
+    print(\"hello\")  
     return 42
"""
        result = analyze_diff(diff)
        ws_issues = [i for i in result.issues if i.category == "whitespace-collapsing"]
        assert len(ws_issues) >= 1
        assert ws_issues[0].severity == IssueSeverity.WARNING

    def test_long_line_detection(self) -> None:
        """Test detection of very long lines."""
        long_line = "+" + "x" * 250
        diff = f"""--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
 def hello():
{long_line}
"""
        result = analyze_diff(diff)
        long_issues = [i for i in result.issues if i.category == "long-line"]
        assert len(long_issues) >= 1
        assert long_issues[0].severity == IssueSeverity.INFO

    def test_binary_file_detection(self) -> None:
        """Test detection of binary file diffs."""
        diff = """--- a/image.png
+++ b/image.png
@@ -1 +1 @@
Binary files a/image.png and b/image.png differ
"""
        result = analyze_diff(diff)
        binary_issues = [i for i in result.issues if i.category == "binary-file"]
        assert len(binary_issues) >= 1
        assert binary_issues[0].severity == IssueSeverity.INFO
        assert binary_issues[0].line_number is None

    def test_stats_computation(self) -> None:
        """Test that stats are computed correctly."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    import os
     print(\"hello\")
     return 42
@@ -10,3 +11,4 @@
 def world():
+    from sys import path
     print(\"world\")
     return 24
"""
        result = analyze_diff(diff)
        stats = result.stats
        assert "files_changed" in stats
        assert "total_additions" in stats
        assert "total_deletions" in stats
        assert "total_hunks" in stats
        assert "issues_by_severity" in stats
        assert "issues_by_category" in stats
        assert stats["issues_by_severity"]["warning"] >= 1
        assert stats["total_hunks"] == 2


class TestAnalyzeDiffFile:
    """Tests for analyze_diff_file function."""

    def test_analyze_file(self) -> None:
        """Test analyzing a diff file from disk."""
        diff_content = """--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def foo():
+    import json
     pass
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            temp_path = Path(f.name)

        try:
            result = analyze_diff_file(temp_path)
            assert isinstance(result, DiffAnalysisResult)
            import_issues = [i for i in result.issues if i.category == "import-filtering"]
            assert len(import_issues) >= 1
        finally:
            temp_path.unlink()


class TestDiffAnalysisResult:
    """Tests for DiffAnalysisResult properties."""

    def test_has_errors_property(self) -> None:
        """Test has_errors property."""
        result = DiffAnalysisResult()
        assert not result.has_errors

        result.issues.append(
            DiffIssue(
                file_path="test.py",
                line_number=1,
                severity=IssueSeverity.ERROR,
                category="test",
                message="test",
            )
        )
        assert result.has_errors

    def test_has_warnings_property(self) -> None:
        """Test has_warnings property."""
        result = DiffAnalysisResult()
        assert not result.has_warnings

        result.issues.append(
            DiffIssue(
                file_path="test.py",
                line_number=1,
                severity=IssueSeverity.WARNING,
                category="test",
                message="test",
            )
        )
        assert result.has_warnings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestDiffQualityAPI:
    """Tests for diff quality analyzer API endpoints."""

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.get("/diff-quality/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "diff-quality-analyzer"}

    def test_analyze_endpoint(self) -> None:
        """Test analyze diff endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        diff_text = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    import os
     print("hello")
     return 42
"""
        resp = client.post("/diff-quality/analyze", json={"diff_text": diff_text})
        assert resp.status_code == 200
        data = resp.json()
        assert "issues" in data
        assert "stats" in data
        assert "has_errors" in data
        assert "has_warnings" in data
        assert len(data["issues"]) >= 1
        # Check import filtering issue
        import_issues = [i for i in data["issues"] if i["category"] == "import-filtering"]
        assert len(import_issues) >= 1
        assert import_issues[0]["line_number"] == 2

    def test_analyze_endpoint_invalid_diff(self) -> None:
        """Test analyze endpoint with invalid diff (returns empty result)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/diff-quality/analyze", json={"diff_text": "not a valid diff"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["issues"] == []
        assert data["stats"]["files_changed"] == 0
