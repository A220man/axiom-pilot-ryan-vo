"""Tests for plugin validator service."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.services.plugin_validator import (
    PluginManifest,
    SkillManifest,
    ValidationResult,
    detect_unlisted_plugins,
    load_plugin_manifest,
    parse_skill_markdown,
    validate_component_paths,
    validate_mcp_placeholders,
    validate_manifest_schema,
    validate_plugin_directory,
    validate_skill_frontmatter,
)


class TestPluginManifest:
    """Tests for PluginManifest loading and validation."""

    def test_load_valid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()
            manifest_data = {
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "skills": ["skills/test-skill"],
                "agents": ["agents/test-agent.md"],
                "hooks": ["hooks/test-hook.py"],
                "mcpServers": ["mcp/test-server"],
                "variables": {"API_KEY": "test-key"},
            }
            (plugin_dir / "plugin.json").write_text(json.dumps(manifest_data))

            manifest = load_plugin_manifest(plugin_dir)

            assert manifest is not None
            assert manifest.name == "test-plugin"
            assert manifest.version == "1.0.0"
            assert manifest.description == "A test plugin"
            assert manifest.author == "Test Author"
            assert manifest.skills == ["skills/test-skill"]
            assert manifest.agents == ["agents/test-agent.md"]
            assert manifest.hooks == ["hooks/test-hook.py"]
            assert manifest.mcp_servers == ["mcp/test-server"]
            assert manifest.variables == {"API_KEY": "test-key"}

    def test_load_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "empty-plugin"
            plugin_dir.mkdir()

            manifest = load_plugin_manifest(plugin_dir)

            assert manifest is None

    def test_load_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "bad-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text("{ invalid json")

            manifest = load_plugin_manifest(plugin_dir)

            assert manifest is None

    def test_validate_manifest_schema_valid(self) -> None:
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            description="Test",
            author="Author",
        )
        result = validate_manifest_schema(manifest)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_validate_manifest_schema_missing_fields(self) -> None:
        manifest = PluginManifest(
            name="",
            version="",
            description="",
            author="",
        )
        result = validate_manifest_schema(manifest)
        assert result.passed is False
        assert len(result.errors) >= 4


class TestSkillMarkdown:
    """Tests for SKILL.md frontmatter parsing."""

    def test_parse_valid_skill_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_content = """---
name: test-skill
description: A test skill
version: 1.0.0
author: Skill Author
tags: [tag1, tag2]
requires: [dep1, dep2]
---
# Test Skill

This is the skill content.
"""
            (skill_dir / "SKILL.md").write_text(skill_content)

            skill = parse_skill_markdown(skill_dir)

            assert skill is not None
            assert skill.name == "test-skill"
            assert skill.description == "A test skill"
            assert skill.version == "1.0.0"
            assert skill.author == "Skill Author"
            assert skill.tags == ["tag1", "tag2"]
            assert skill.requires == ["dep1", "dep2"]

    def test_parse_skill_markdown_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "minimal-skill"
            skill_dir.mkdir()
            skill_content = """---
name: minimal-skill
description: Minimal skill
---
"""
            (skill_dir / "SKILL.md").write_text(skill_content)

            skill = parse_skill_markdown(skill_dir)

            assert skill is not None
            assert skill.name == "minimal-skill"
            assert skill.description == "Minimal skill"
            assert skill.version == "0.0.0"
            assert skill.author == ""
            assert skill.tags == []
            assert skill.requires == []

    def test_parse_missing_skill_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "no-skill"
            skill_dir.mkdir()

            skill = parse_skill_markdown(skill_dir)

            assert skill is None

    def test_parse_invalid_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "bad-skill"
            skill_dir.mkdir()
            skill_content = """---
name: bad-skill
description: Bad skill
invalid yaml: [unclosed
---
"""
            (skill_dir / "SKILL.md").write_text(skill_content)

            skill = parse_skill_markdown(skill_dir)

            assert skill is None

    def test_parse_no_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "no-frontmatter"
            skill_dir.mkdir()
            skill_content = """# No Frontmatter

Just content.
"""
            (skill_dir / "SKILL.md").write_text(skill_content)

            skill = parse_skill_markdown(skill_dir)

            assert skill is None

    def test_validate_skill_frontmatter_valid(self) -> None:
        skill = SkillManifest(
            name="valid-skill",
            description="A valid skill",
            version="1.0.0",
            author="Author",
        )
        result = validate_skill_frontmatter(skill)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_validate_skill_frontmatter_missing_name(self) -> None:
        skill = SkillManifest(
            name="",
            description="A skill",
        )
        result = validate_skill_frontmatter(skill)
        assert result.passed is False
        assert any("name cannot be empty" in e for e in result.errors)

    def test_validate_skill_frontmatter_empty_description(self) -> None:
        skill = SkillManifest(
            name="test-skill",
            description="",
        )
        result = validate_skill_frontmatter(skill)
        assert result.passed is True
        assert any("description is empty" in w for w in result.warnings)


class TestComponentPaths:
    """Tests for component path validation."""

    def test_validate_component_paths_all_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            # Create skill with SKILL.md
            skill_dir = plugin_dir / "skills" / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
---
""")

            # Create agent
            agents_dir = plugin_dir / "agents"
            agents_dir.mkdir()
            (agents_dir / "test-agent.md").write_text("# Test Agent")

            # Create hook
            hooks_dir = plugin_dir / "hooks"
            hooks_dir.mkdir()
            (hooks_dir / "test-hook.py").write_text("# test hook")

            # Create MCP server
            mcp_dir = plugin_dir / "mcp" / "test-server"
            mcp_dir.mkdir(parents=True)
            (mcp_dir / "mcp.json").write_text("{}")

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                skills=["skills/test-skill"],
                agents=["agents/test-agent.md"],
                hooks=["hooks/test-hook.py"],
                mcp_servers=["mcp/test-server"],
            )

            result = validate_component_paths(plugin_dir, manifest)

            assert result.passed is True
            assert len(result.errors) == 0

    def test_validate_component_paths_missing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                skills=["skills/missing-skill"],
            )

            result = validate_component_paths(plugin_dir, manifest)

            assert result.passed is False
            assert any("does not exist" in e for e in result.errors)

    def test_validate_component_paths_skill_missing_skillmd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            skill_dir = plugin_dir / "skills" / "test-skill"
            skill_dir.mkdir(parents=True)
            # No SKILL.md

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                skills=["skills/test-skill"],
            )

            result = validate_component_paths(plugin_dir, manifest)

            assert result.passed is True  # warning, not error
            assert any("missing SKILL.md" in w for w in result.warnings)

    def test_validate_component_paths_invalid_skill_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            skill_dir = plugin_dir / "skills" / "bad-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("""---
# invalid yaml: [
---
""")

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                skills=["skills/bad-skill"],
            )

            result = validate_component_paths(plugin_dir, manifest)

            assert result.passed is True  # warning, not error
            assert any("Failed to parse SKILL.md" in w for w in result.warnings)

    def test_validate_component_paths_skill_empty_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            skill_dir = plugin_dir / "skills" / "bad-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("""---
name: ""
description: Bad skill
---
""")

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                skills=["skills/bad-skill"],
            )

            result = validate_component_paths(plugin_dir, manifest)

            assert result.passed is False
            assert any("name cannot be empty" in e for e in result.errors)


class TestMCPPlaceholders:
    """Tests for MCP placeholder validation."""

    def test_validate_mcp_placeholders_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            mcp_dir = plugin_dir / "mcp" / "test-server"
            mcp_dir.mkdir(parents=True)
            mcp_data = {
                "command": "python",
                "args": ["-m", "server"],
                "env": {"API_KEY": "${API_KEY}"},
            }
            (mcp_dir / "mcp.json").write_text(json.dumps(mcp_data))

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                mcp_servers=["mcp/test-server"],
                variables={"API_KEY": "secret"},
            )

            result = validate_mcp_placeholders(plugin_dir, manifest)

            assert result.passed is True
            assert len(result.errors) == 0

    def test_validate_mcp_placeholders_missing_variable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()

            mcp_dir = plugin_dir / "mcp" / "test-server"
            mcp_dir.mkdir(parents=True)
            mcp_data = {
                "env": {"API_KEY": "${MISSING_KEY}"},
            }
            (mcp_dir / "mcp.json").write_text(json.dumps(mcp_data))

            manifest = PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Author",
                mcp_servers=["mcp/test-server"],
                variables={"OTHER_KEY": "value"},
            )

            result = validate_mcp_placeholders(plugin_dir, manifest)

            assert result.passed is False
            assert any("not declared" in e for e in result.errors)


class TestUnlistedPlugins:
    """Tests for unlisted plugin detection."""

    def test_detect_unlisted_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_root = Path(tmpdir) / "plugins"
            plugins_root.mkdir()

            # Listed plugin
            listed = plugins_root / "listed-plugin"
            listed.mkdir()
            (listed / "plugin.json").write_text(json.dumps({"name": "listed-plugin"}))

            # Unlisted plugin
            unlisted = plugins_root / "unlisted-plugin"
            unlisted.mkdir()
            (unlisted / "plugin.json").write_text(json.dumps({"name": "unlisted-plugin"}))

            # Not a plugin (no plugin.json)
            not_plugin = plugins_root / "not-a-plugin"
            not_plugin.mkdir()

            marketplace = {"listed-plugin"}
            result = detect_unlisted_plugins(plugins_root, marketplace)

            assert result == ["unlisted-plugin"]

    def test_detect_unlisted_plugins_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_root = Path(tmpdir) / "plugins"
            plugins_root.mkdir()

            marketplace = {"plugin1", "plugin2"}
            result = detect_unlisted_plugins(plugins_root, marketplace)

            assert result == []


class TestValidatePluginDirectory:
    """Tests for full plugin directory validation."""

    def test_validate_plugin_directory_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "plugins" / "valid-plugin"
            plugin_dir.mkdir(parents=True)

            # Create plugin.json
            manifest_data = {
                "name": "valid-plugin",
                "version": "1.0.0",
                "description": "A valid plugin",
                "author": "Author",
                "skills": ["skills/test-skill"],
            }
            (plugin_dir / "plugin.json").write_text(json.dumps(manifest_data))

            # Create skill
            skill_dir = plugin_dir / "skills" / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
---
""")

            result = validate_plugin_directory(plugin_dir)

            assert result.passed is True
            assert len(result.errors) == 0

    def test_validate_plugin_directory_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "plugins" / "invalid-plugin"
            plugin_dir.mkdir(parents=True)

            # Missing required fields
            (plugin_dir / "plugin.json").write_text(json.dumps({"name": "invalid"}))

            result = validate_plugin_directory(plugin_dir)

            assert result.passed is False
            assert len(result.errors) > 0

    def test_validate_plugin_directory_unlisted_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_root = Path(tmpdir) / "plugins"
            plugins_root.mkdir()

            # Valid plugin
            plugin_dir = plugins_root / "valid-plugin"
            plugin_dir.mkdir()
            manifest_data = {
                "name": "valid-plugin",
                "version": "1.0.0",
                "description": "Valid",
                "author": "Author",
            }
            (plugin_dir / "plugin.json").write_text(json.dumps(manifest_data))

            # Unlisted plugin
            unlisted_dir = plugins_root / "unlisted-plugin"
            unlisted_dir.mkdir()
            (unlisted_dir / "plugin.json").write_text(json.dumps({"name": "unlisted-plugin"}))

            result = validate_plugin_directory(plugin_dir, marketplace_plugins={"valid-plugin"})

            assert result.passed is True
            assert any("Unlisted plugin directory" in w for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
