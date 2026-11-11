"""Tests for symlink detector service."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from app.services.symlink_detector import (
    SymlinkIssue,
    SymlinkScanResult,
    scan_for_symlinks,
    get_default_plugins_path,
    analyze_symlinks,
)


class TestSymlinkDetector:
    """Tests for symlink detector service."""

    def test_get_default_plugins_path(self) -> None:
        """Test that default plugins path is correctly constructed."""
        path = get_default_plugins_path()
        assert str(path).endswith(".cursor/plugins/local")

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning a non-existent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"
            result = scan_for_symlinks(nonexistent)

            assert result.scanned_path == str(nonexistent)
            assert result.total_plugins == 0
            assert len(result.issues) == 1
            assert result.issues[0].issue_type == "missing"
            assert "does not exist" in result.issues[0].message

    def test_scan_not_a_directory(self) -> None:
        """Test scanning a path that is not a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "not_a_dir.txt"
            file_path.write_text("content")
            result = scan_for_symlinks(file_path)

            assert result.total_plugins == 0
            assert len(result.issues) == 1
            assert result.issues[0].issue_type == "not-directory"
            assert "not a directory" in result.issues[0].message

    def test_scan_empty_directory(self) -> None:
        """Test scanning an empty plugins directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)
            result = scan_for_symlinks(plugins_dir)

            assert result.scanned_path == str(plugins_dir)
            assert result.total_plugins == 0
            assert result.symlinked_plugins == []
            assert result.broken_symlinks == []
            assert result.issues == []
            assert not result.has_issues
            assert not result.has_symlinks
            assert not result.has_broken

    def test_scan_with_regular_directories(self) -> None:
        """Test scanning directory with regular plugin directories (no symlinks)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)

            # Create regular plugin directories
            (plugins_dir / "plugin1").mkdir()
            (plugins_dir / "plugin2").mkdir()
            (plugins_dir / "plugin1" / "plugin.json").write_text('{"name": "plugin1"}')
            (plugins_dir / "plugin2" / "plugin.json").write_text('{"name": "plugin2"}')

            result = scan_for_symlinks(plugins_dir)

            assert result.total_plugins == 2
            assert result.symlinked_plugins == []
            assert result.broken_symlinks == []
            assert result.issues == []
            assert not result.has_issues

    def test_scan_with_valid_symlink(self) -> None:
        """Test scanning directory with a valid symlink to a plugin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)

            # Create actual plugin elsewhere
            real_plugin = Path(tmpdir) / "real_plugins" / "my-plugin"
            real_plugin.mkdir(parents=True)
            (real_plugin / "plugin.json").write_text('{"name": "my-plugin"}')

            # Create symlink in plugins directory
            symlink_path = plugins_dir / "my-plugin"
            symlink_path.symlink_to(real_plugin)

            result = scan_for_symlinks(plugins_dir)

            assert result.total_plugins == 1
            assert result.symlinked_plugins == ["my-plugin"]
            assert result.broken_symlinks == []
            assert len(result.issues) == 1
            assert result.issues[0].issue_type == "symlinked"
            assert "my-plugin" in result.issues[0].plugin_name
            assert "symlink" in result.issues[0].message.lower()
            assert result.issues[0].target_path == str(real_plugin)
            assert "copy" in result.issues[0].suggestion.lower()
            assert result.has_symlinks
            assert not result.has_broken

    def test_scan_with_broken_symlink(self) -> None:
        """Test scanning directory with a broken symlink."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)

            # Create broken symlink (target doesn't exist)
            symlink_path = plugins_dir / "broken-plugin"
            symlink_path.symlink_to("/nonexistent/path")

            result = scan_for_symlinks(plugins_dir)

            assert result.total_plugins == 1
            assert result.symlinked_plugins == ["broken-plugin"]
            assert result.broken_symlinks == ["broken-plugin"]
            assert len(result.issues) == 1
            assert result.issues[0].issue_type == "broken"
            assert "broken-plugin" in result.issues[0].plugin_name
            assert "non-existent" in result.issues[0].message
            assert result.issues[0].target_path == "/nonexistent/path"
            assert result.has_symlinks
            assert result.has_broken

    def test_scan_mixed_plugins(self) -> None:
        """Test scanning with mix of regular dirs, valid symlinks, and broken symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)

            # Regular plugin
            (plugins_dir / "regular-plugin").mkdir()
            (plugins_dir / "regular-plugin" / "plugin.json").write_text('{"name": "regular"}')

            # Valid symlink
            real_plugin = Path(tmpdir) / "real" / "linked-plugin"
            real_plugin.mkdir(parents=True)
            (real_plugin / "plugin.json").write_text('{"name": "linked"}')
            (plugins_dir / "linked-plugin").symlink_to(real_plugin)

            # Broken symlink
            (plugins_dir / "broken-plugin").symlink_to("/nonexistent")

            result = scan_for_symlinks(plugins_dir)

            assert result.total_plugins == 3
            assert set(result.symlinked_plugins) == {"linked-plugin", "broken-plugin"}
            assert result.broken_symlinks == ["broken-plugin"]
            assert len(result.issues) == 2
            issue_types = {i.issue_type for i in result.issues}
            assert issue_types == {"symlinked", "broken"}
            assert result.has_symlinks
            assert result.has_broken

    def test_analyze_symlinks_alias(self) -> None:
        """Test that analyze_symlinks is an alias for scan_for_symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)
            (plugins_dir / "plugin1").mkdir()

            result1 = scan_for_symlinks(plugins_dir)
            result2 = analyze_symlinks(plugins_dir)

            assert result1.total_plugins == result2.total_plugins
            assert result1.symlinked_plugins == result2.symlinked_plugins


class TestSymlinkDetectorAPI:
    """Tests for symlink detector API endpoints."""

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.get("/symlinks/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "symlink-detector"}

    def test_scan_endpoint_default_path(self) -> None:
        """Test scan endpoint with default path (may not exist)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/symlinks/scan", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "scanned_path" in data
        assert "total_plugins" in data
        assert "symlinked_plugins" in data
        assert "broken_symlinks" in data
        assert "issues" in data
        assert "has_issues" in data
        assert "has_symlinks" in data
        assert "has_broken" in data

    def test_scan_endpoint_custom_path(self) -> None:
        """Test scan endpoint with custom path."""
        from fastapi.testclient import TestClient
        from app.main import app
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)
            (plugins_dir / "plugin1").mkdir()

            client = TestClient(app)
            resp = client.post("/symlinks/scan", json={"plugins_path": str(plugins_dir)})
            assert resp.status_code == 200
            data = resp.json()
            assert data["scanned_path"] == str(plugins_dir)
            assert data["total_plugins"] == 1
            assert data["symlinked_plugins"] == []
            assert data["has_issues"] is False

    def test_scan_endpoint_with_symlink(self) -> None:
        """Test scan endpoint detects symlinks."""
        from fastapi.testclient import TestClient
        from app.main import app
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins" / "local"
            plugins_dir.mkdir(parents=True)

            real_plugin = Path(tmpdir) / "real" / "my-plugin"
            real_plugin.mkdir(parents=True)
            (plugins_dir / "my-plugin").symlink_to(real_plugin)

            client = TestClient(app)
            resp = client.post("/symlinks/scan", json={"plugins_path": str(plugins_dir)})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_plugins"] == 1
            assert data["symlinked_plugins"] == ["my-plugin"]
            assert data["has_symlinks"] is True
            assert len(data["issues"]) == 1
            assert data["issues"][0]["issue_type"] == "symlinked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
