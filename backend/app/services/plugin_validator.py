"""Plugin manifest validation service (stub for plugin-validator feature)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of a plugin validation check."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PluginManifest:
    """Parsed plugin.json manifest."""

    name: str
    version: str
    description: str
    author: str
    repository: str | None = None
    license: str | None = None
    skills: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def load_plugin_manifest(plugin_dir: Path) -> PluginManifest | None:
    """Load and parse plugin.json from a plugin directory."""
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None

    return PluginManifest(
        name=data.get("name", ""),
        version=data.get("version", "0.0.0"),
        description=data.get("description", ""),
        author=data.get("author", ""),
        repository=data.get("repository"),
        license=data.get("license"),
        skills=data.get("skills", []),
        agents=data.get("agents", []),
        hooks=data.get("hooks", []),
        mcp_servers=data.get("mcpServers", []),
        variables=data.get("variables", {}),
        raw=data,
    )


def validate_manifest_schema(manifest: PluginManifest) -> ValidationResult:
    """Validate plugin.json against required schema."""
    errors: list[str] = []
    warnings: list[str] = []

    required_fields = ["name", "version", "description", "author"]
    for field_name in required_fields:
        if not getattr(manifest, field_name, None):
            errors.append(f"Missing required field: {field_name}")

    if not manifest.name:
        errors.append("Plugin name cannot be empty")

    if not manifest.version:
        warnings.append("Version not specified, defaulting to 0.0.0")

    return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)


def validate_component_paths(plugin_dir: Path, manifest: PluginManifest) -> ValidationResult:
    """Verify that declared component paths exist."""
    errors: list[str] = []
    warnings: list[str] = []

    # Check skills
    for skill in manifest.skills:
        skill_path = plugin_dir / skill
        if not skill_path.exists():
            errors.append(f"Declared skill path does not exist: {skill}")
        elif not (skill_path / "SKILL.md").exists():
            warnings.append(f"Skill directory missing SKILL.md: {skill}")

    # Check agents
    for agent in manifest.agents:
        agent_path = plugin_dir / agent
        if not agent_path.exists():
            errors.append(f"Declared agent path does not exist: {agent}")
        elif not agent_path.suffix == ".md":
            warnings.append(f"Agent file should be .md: {agent}")

    # Check hooks
    for hook in manifest.hooks:
        hook_path = plugin_dir / hook
        if not hook_path.exists():
            errors.append(f"Declared hook path does not exist: {hook}")

    # Check MCP servers
    for mcp in manifest.mcp_servers:
        mcp_path = plugin_dir / mcp
        if not mcp_path.exists():
            errors.append(f"Declared MCP server path does not exist: {mcp}")
        elif not (mcp_path / "mcp.json").exists():
            warnings.append(f"MCP server directory missing mcp.json: {mcp}")

    return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)


def validate_mcp_placeholders(plugin_dir: Path, manifest: PluginManifest) -> ValidationResult:
    """Validate MCP server placeholders against declared variables."""
    errors: list[str] = []
    warnings: list[str] = []

    for mcp_server in manifest.mcp_servers:
        mcp_path = plugin_dir / mcp_server / "mcp.json"
        if not mcp_path.exists():
            continue

        try:
            with open(mcp_path, encoding="utf-8") as f:
                mcp_data = json.load(f)
        except json.JSONDecodeError:
            continue

        # Find all ${VAR} placeholders in mcp.json
        import re

        mcp_str = json.dumps(mcp_data)
        placeholders = set(re.findall(r"\$\{([^}]+)\}", mcp_str))

        for placeholder in placeholders:
            if placeholder not in manifest.variables:
                errors.append(
                    f"MCP placeholder '${{{placeholder}}}' not declared in plugin.json variables"
                )

    return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)


def detect_unlisted_plugins(plugins_root: Path, marketplace_plugins: set[str]) -> list[str]:
    """Detect plugin directories not listed in marketplace."""
    unlisted: list[str] = []

    if not plugins_root.exists():
        return unlisted

    for item in plugins_root.iterdir():
        if item.is_dir() and (item / "plugin.json").exists():
            if item.name not in marketplace_plugins:
                unlisted.append(item.name)

    return unlisted


def validate_plugin_directory(plugin_dir: Path, marketplace_plugins: set[str] | None = None) -> ValidationResult:
    """Run all validation checks on a plugin directory."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    manifest = load_plugin_manifest(plugin_dir)
    if manifest is None:
        return ValidationResult(
            passed=False,
            errors=["Failed to load plugin.json or file not found"],
            warnings=[],
        )

    # Schema validation
    schema_result = validate_manifest_schema(manifest)
    all_errors.extend(schema_result.errors)
    all_warnings.extend(schema_result.warnings)

    # Component paths
    paths_result = validate_component_paths(plugin_dir, manifest)
    all_errors.extend(paths_result.errors)
    all_warnings.extend(paths_result.warnings)

    # MCP placeholders
    mcp_result = validate_mcp_placeholders(plugin_dir, manifest)
    all_errors.extend(mcp_result.errors)
    all_warnings.extend(mcp_result.warnings)

    # Unlisted plugins (if marketplace provided)
    if marketplace_plugins is not None:
        unlisted = detect_unlisted_plugins(plugin_dir.parent, marketplace_plugins)
        for unlisted_name in unlisted:
            all_warnings.append(f"Unlisted plugin directory: {unlisted_name}")

    return ValidationResult(
        passed=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
    )