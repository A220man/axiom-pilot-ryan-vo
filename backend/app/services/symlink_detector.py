"""Symlink detector for Cursor local plugins (issue #35)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SymlinkIssue:
    """A symlink-related issue found during scanning."""

    plugin_name: str
    plugin_path: str
    issue_type: str  # "symlinked" | "broken"
    message: str
    target_path: str | None = None
    suggestion: str | None = None


@dataclass
class SymlinkScanResult:
    """Result of symlink scanning."""

    scanned_path: str
    total_plugins: int = 0
    symlinked_plugins: list[str] = field(default_factory=list)
    broken_symlinks: list[str] = field(default_factory=list)
    issues: list[SymlinkIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return len(self.issues) > 0

    @property
    def has_symlinks(self) -> bool:
        """Check if any symlinked plugins were found."""
        return len(self.symlinked_plugins) > 0

    @property
    def has_broken(self) -> bool:
        """Check if any broken symlinks were found."""
        return len(self.broken_symlinks) > 0


def get_default_plugins_path() -> Path:
    """Get the default Cursor local plugins path."""
    home = Path.home()
    return home / ".cursor" / "plugins" / "local"


def scan_for_symlinks(plugins_path: Path | None = None) -> SymlinkScanResult:
    """
    Scan the local plugins directory for symlinks.

    Args:
        plugins_path: Custom path to scan. Defaults to ~/.cursor/plugins/local

    Returns:
        SymlinkScanResult with details about symlinked and broken plugins
    """
    if plugins_path is None:
        plugins_path = get_default_plugins_path()

    result = SymlinkScanResult(scanned_path=str(plugins_path))

    if not plugins_path.exists():
        result.issues.append(
            SymlinkIssue(
                plugin_name="",
                plugin_path=str(plugins_path),
                issue_type="missing",
                message=f"Plugins directory does not exist: {plugins_path}",
                suggestion="Create the directory or check Cursor configuration",
            )
        )
        return result

    if not plugins_path.is_dir():
        result.issues.append(
            SymlinkIssue(
                plugin_name="",
                plugin_path=str(plugins_path),
                issue_type="not-directory",
                message=f"Plugins path is not a directory: {plugins_path}",
            )
        )
        return result

    # Scan each entry in the plugins directory
    for entry in plugins_path.iterdir():
        if not entry.is_dir() and not entry.is_symlink():
            continue

        result.total_plugins += 1

        if entry.is_symlink():
            target = entry.resolve()
            result.symlinked_plugins.append(entry.name)

            if not target.exists():
                result.broken_symlinks.append(entry.name)
                result.issues.append(
                    SymlinkIssue(
                        plugin_name=entry.name,
                        plugin_path=str(entry),
                        issue_type="broken",
                        message=f"Symlinked plugin points to non-existent target: {target}",
                        target_path=str(target),
                        suggestion="Remove the broken symlink and copy the plugin files instead",
                    )
                )
            else:
                result.issues.append(
                    SymlinkIssue(
                        plugin_name=entry.name,
                        plugin_path=str(entry),
                        issue_type="symlinked",
                        message=f"Plugin is a symlink to {target} - Cursor may not load symlinked plugins",
                        target_path=str(target),
                        suggestion="Copy the plugin files to this location instead of using a symlink",
                    )
                )

    return result


def analyze_symlinks(plugins_path: Path | None = None) -> SymlinkScanResult:
    """Analyze symlinks in the local plugins directory (alias for scan_for_symlinks)."""
    return scan_for_symlinks(plugins_path)
