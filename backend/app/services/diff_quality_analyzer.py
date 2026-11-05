"""Diff rendering quality analyzer service (issue #472)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class IssueSeverity(str, Enum):
    """Severity levels for diff quality issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DiffIssue:
    """A quality issue found in a diff."""

    file_path: str
    line_number: int | None
    severity: IssueSeverity
    category: str
    message: str
    context: str | None = None


@dataclass
class DiffAnalysisResult:
    """Result of diff quality analysis."""

    issues: list[DiffIssue] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == IssueSeverity.WARNING for i in self.issues)


class DiffParser:
    """Parse unified diff format and track line numbers."""

    HUNK_HEADER_PATTERN = re.compile(r"^@@\s+-(\d+),?(\d*)\s+\+(\d+),?(\d*)\s+@@")

    def __init__(self) -> None:
        self.current_old_line: int | None = None
        self.current_new_line: int | None = None
        self.current_file: str | None = None
        self.in_hunk: bool = False

    def parse(self, diff_text: str) -> DiffAnalysisResult:
        """Parse a unified diff and analyze quality issues."""
        result = DiffAnalysisResult()
        lines = diff_text.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("--- "):
                self.current_file = line[4:].strip()
                if self.current_file.startswith("a/"):
                    self.current_file = self.current_file[2:]
            elif line.startswith("+++ "):
                new_file = line[4:].strip()
                if new_file.startswith("b/"):
                    new_file = new_file[2:]
                if not self.current_file:
                    self.current_file = new_file
            elif line.startswith("@@"):
                match = self.HUNK_HEADER_PATTERN.match(line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1

                    self.current_old_line = old_start
                    self.current_new_line = new_start
                    self.in_hunk = True
                else:
                    self.in_hunk = False
            elif self.in_hunk and self.current_file:
                issues = self._analyze_line(line, lines, i)
                result.issues.extend(issues)

                if line.startswith(" "):
                    if self.current_old_line is not None:
                        self.current_old_line += 1
                    if self.current_new_line is not None:
                        self.current_new_line += 1
                elif line.startswith("-"):
                    if self.current_old_line is not None:
                        self.current_old_line += 1
                elif line.startswith("+"):
                    if self.current_new_line is not None:
                        self.current_new_line += 1

            i += 1

        result.stats = self._compute_stats(diff_text, result.issues)
        return result

    def _analyze_line(
        self, line: str, all_lines: list[str], index: int
    ) -> list[DiffIssue]:
        """Analyze a single diff line for quality issues."""
        issues: list[DiffIssue] = []

        if not self.current_file or self.current_new_line is None:
            return issues

        if line.startswith("+") and self._is_import_line(line[1:]):
            issues.append(
                DiffIssue(
                    file_path=self.current_file,
                    line_number=self.current_new_line,
                    severity=IssueSeverity.WARNING,
                    category="import-filtering",
                    message="Import line added - verify not filtered by diff renderer",
                    context=line,
                )
            )

        if line.startswith("-") and index + 1 < len(all_lines):
            next_line = all_lines[index + 1]
            if next_line.startswith("+") and self._is_whitespace_only_change(
                line[1:], next_line[1:]
            ):
                issues.append(
                    DiffIssue(
                        file_path=self.current_file,
                        line_number=self.current_new_line,
                        severity=IssueSeverity.WARNING,
                        category="whitespace-collapsing",
                        message="Whitespace-only change - may be collapsed by diff renderer",
                        context=f"{line}\n{next_line}",
                    )
                )

        if (line.startswith("+") or line.startswith("-")) and len(line) > 200:
            issues.append(
                DiffIssue(
                    file_path=self.current_file,
                    line_number=self.current_new_line,
                    severity=IssueSeverity.INFO,
                    category="long-line",
                    message=f"Very long line ({len(line)} chars) - may be truncated in UI",
                    context=line[:100] + "...",
                )
            )

        if "Binary files" in line and line.startswith("Binary"):
            issues.append(
                DiffIssue(
                    file_path=self.current_file or "unknown",
                    line_number=None,
                    severity=IssueSeverity.INFO,
                    category="binary-file",
                    message="Binary file diff - cannot analyze line-level changes",
                    context=line,
                )
            )

        return issues

    def _is_import_line(self, line: str) -> bool:
        """Check if a line is an import statement."""
        stripped = line.strip()
        return (
            stripped.startswith("import ")
            or stripped.startswith("from ")
            or stripped.startswith("# import")
            or (stripped.startswith("const ") and "require(" in stripped)
            or (stripped.startswith("import ") and " from " in stripped)
        )

    def _is_whitespace_only_change(self, old_line: str, new_line: str) -> bool:
        """Check if the change is whitespace-only."""
        return old_line.strip() == new_line.strip() and old_line != new_line

    def _compute_stats(self, diff_text: str, issues: list[DiffIssue]) -> dict[str, Any]:
        """Compute statistics about the diff."""
        lines = diff_text.splitlines()
        files = set()
        additions = 0
        deletions = 0
        hunks = 0

        for line in lines:
            if line.startswith("--- "):
                f = line[4:].strip()
                if f.startswith("a/"):
                    f = f[2:]
                files.add(f)
            elif line.startswith("+++ "):
                f = line[4:].strip()
                if f.startswith("b/"):
                    f = f[2:]
                files.add(f)
            elif line.startswith("@@"):
                hunks += 1
            elif line.startswith("+"):
                additions += 1
            elif line.startswith("-"):
                deletions += 1

        return {
            "files_changed": len(files),
            "total_additions": additions,
            "total_deletions": deletions,
            "total_hunks": hunks,
            "issues_by_severity": {
                "error": sum(1 for i in issues if i.severity == IssueSeverity.ERROR),
                "warning": sum(1 for i in issues if i.severity == IssueSeverity.WARNING),
                "info": sum(1 for i in issues if i.severity == IssueSeverity.INFO),
            },
            "issues_by_category": {
                cat: sum(1 for i in issues if i.category == cat)
                for cat in set(i.category for i in issues)
            },
        }


def analyze_diff(diff_text: str) -> DiffAnalysisResult:
    """Analyze a unified diff for quality issues."""
    parser = DiffParser()
    return parser.parse(diff_text)


def analyze_diff_file(diff_path: Path) -> DiffAnalysisResult:
    """Analyze a diff file for quality issues."""
    text = diff_path.read_text(encoding="utf-8")
    return analyze_diff(text)
