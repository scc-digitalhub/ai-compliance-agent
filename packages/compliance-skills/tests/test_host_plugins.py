from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from compliance_skills import load_agent

ROOT = Path(__file__).resolve().parents[3]


def test_generated_host_integrations_are_fresh():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_host_plugins.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.fixture
def generator():
    spec = importlib.util.spec_from_file_location("sync_host_plugins", ROOT / "scripts/sync_host_plugins.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("host", ["copilot", "claude-code", "opencode"])
def test_native_agents_share_the_portable_instructions(generator, host):
    definition = load_agent()
    path = ROOT / "integrations" / host / generator.AGENT_FILES[host]
    _, header, body = path.read_text().split("---", 2)
    metadata = yaml.safe_load(header)
    assert metadata["description"] == definition.description
    assert body.strip().startswith(definition.instructions)
    assert "model" not in metadata

    if host == "claude-code":
        assert metadata["name"] == definition.name
        assert metadata["skills"] == [f"ai-compliance:{name}" for name in definition.skills]
        assert "tools" not in metadata  # Inherit the plugin's namespaced MCP tools.
        for name in definition.skills:
            assert (ROOT / "integrations" / host / "skills" / name / "SKILL.md").is_file()
    else:
        for name in definition.skills:
            assert (path.parent / ".." / "skills" / name / "SKILL.md").is_file()
        if host == "copilot":
            assert metadata["tools"] == ["read", "search", "ai-compliance/*"]
        else:
            assert metadata["mode"] == "primary"
            assert metadata["permission"] == {"edit": "deny", "bash": "deny"}


@pytest.mark.parametrize("host", ["copilot", "claude-code", "opencode"])
def test_freshness_detects_missing_changed_and_obsolete_agents(generator, monkeypatch, tmp_path, host):
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    assert generator.sync(check=False) == 0
    assert generator.sync(check=True) == 0
    path = tmp_path / "integrations" / host / generator.AGENT_FILES[host]
    original = path.read_bytes()
    path.unlink()
    assert generator.sync(check=True) == 1
    path.write_bytes(original + b"\nChanged")
    assert generator.sync(check=True) == 1
    path.write_bytes(original)
    obsolete = path.with_name("obsolete.md")
    obsolete.write_text("Old agent")
    assert generator.sync(check=True) == 1
    obsolete.unlink()
    assert generator.sync(check=True) == 0
