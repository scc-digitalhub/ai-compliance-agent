# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "packages" / "compliance-skills" / "src" / "compliance_skills" / "skills"
sys.path.insert(0, str(SKILLS.parent.parent))

from compliance_skills import PortableAgent, load_agent

DISTRIBUTION = "ai-compliance-platform"
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
DESCRIPTION = "Portable AI compliance agent, skills and MCP tools."


def mcp_command(launcher: str) -> list[str]:
    """Command that starts the MCP server: an installed executable, or a version-pinned uvx run."""
    if launcher == "path":
        return ["compliance-mcp"]
    if launcher == "uvx":
        return ["uvx", "--from", f"{DISTRIBUTION}[mcp]=={VERSION}", "compliance-mcp"]
    raise ValueError(f"Unknown launcher: {launcher}")


def host_configs(launcher: str) -> dict[str, dict]:
    command, *args = mcp_command(launcher)
    return {
        "copilot": {
            "$schema": "https://json.schemastore.org/mcp.json",
            "servers": {"ai-compliance": {"type": "stdio", "command": command, "args": args}},
        },
        "claude-code": {
            "name": "ai-compliance",
            "version": VERSION,
            "description": DESCRIPTION,
            "mcpServers": {"ai-compliance": {"command": command, "args": args}},
        },
        "opencode": {
            "$schema": "https://opencode.ai/config.json",
            "mcp": {"ai-compliance": {"type": "local", "command": [command, *args], "enabled": True}},
        },
    }


MARKETPLACE_CONFIG = {
    "name": "ai-compliance",
    "description": "AI compliance assistant for Claude Code",
    "owner": {"name": "scc-digitalhub"},
    "plugins": [{
        "name": "ai-compliance",
        "source": "./integrations/claude-code",
        "description": DESCRIPTION,
        "version": VERSION,
    }],
}

HOSTS = {
    "copilot": {"skills": Path(".github/skills"), "config": Path(".vscode/mcp.json")},
    "claude-code": {"skills": Path("skills"), "config": Path(".claude-plugin/plugin.json")},
    "opencode": {"skills": Path(".opencode/skills"), "config": Path("opencode.json")},
}

AGENT_FILES = {
    "copilot": Path(".github/agents/compliance-assistant.agent.md"),
    "claude-code": Path("agents/compliance-assistant.md"),
    "opencode": Path(".opencode/agents/compliance-assistant.md"),
}


def render_agent(host: str, agent: PortableAgent) -> bytes:
    metadata: dict[str, object] = {
        "name": agent.name,
        "description": agent.description,
    }
    if host == "copilot":
        metadata["tools"] = ["read", "search", "ai-compliance/*"]
    elif host == "claude-code":
        # Inherit plugin MCP tools: Claude namespaces their server name at installation.
        metadata["disallowedTools"] = ["Bash", "Edit", "Write", "NotebookEdit"]
        metadata["skills"] = [f"ai-compliance:{name}" for name in agent.skills]
    elif host == "opencode":
        metadata.pop("name")
        metadata["mode"] = "primary"
        metadata["permission"] = {"edit": "deny", "bash": "deny"}
    else:
        raise ValueError(f"Unknown host: {host}")

    body = agent.instructions
    if host != "claude-code":
        body += "\n\nBundled skills\n"
        for name in agent.skills:
            body += f"- [{name}](../skills/{name}/SKILL.md)\n"
    return (
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=False)
        + "---\n"
        + body.rstrip()
        + "\n"
    ).encode("utf-8")


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def expected_files(output: Path | None = None, launcher: str = "path") -> dict[Path, bytes]:
    """Generated files; by default the checked-in bundles under integrations/."""
    files: dict[Path, bytes] = {}
    agent = load_agent()
    configs = host_configs(launcher)
    root = output or ROOT / "integrations"
    for host, settings in HOSTS.items():
        base = root / host
        files[base / AGENT_FILES[host]] = render_agent(host, agent)
        skills_path = settings["skills"]
        for skill_dir in sorted(SKILLS.iterdir()):
            if not skill_dir.is_dir():
                continue
            for source in sorted(path for path in skill_dir.rglob("*") if path.is_file()):
                relative = source.relative_to(SKILLS)
                files[base / skills_path / relative] = source.read_bytes()
        files[base / settings["config"]] = _json(configs[host])
    if output is None:
        files[ROOT / ".claude-plugin" / "marketplace.json"] = _json(MARKETPLACE_CONFIG)
    return files


def sync(*, check: bool, output: Path | None = None, launcher: str = "path") -> int:
    stale: list[Path] = []
    files = expected_files(output, launcher)
    expected_paths = set(files)
    for path, content in files.items():
        if check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(path.relative_to(ROOT))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    if check:
        for host, settings in HOSTS.items():
            base = ROOT / "integrations" / host
            for generated_root in (base / settings["skills"], base / AGENT_FILES[host].parent):
                if not generated_root.exists():
                    continue
                for path in generated_root.rglob("*"):
                    if path.is_file() and path not in expected_paths:
                        stale.append(path.relative_to(ROOT))

    if stale:
        print("Generated host integration files are stale:", file=sys.stderr)
        for path in stale:
            print(f"  {path}", file=sys.stderr)
        print("Run: python scripts/sync_host_plugins.py", file=sys.stderr)
        return 1
    if check:
        print("Host integration files are up to date.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate host-specific compliance bundles.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated bundle files differ from the canonical agent and skills",
    )
    parser.add_argument(
        "--output", type=Path,
        help="write the bundles to this directory instead of integrations/ (for release artifacts)",
    )
    parser.add_argument(
        "--launcher", choices=("path", "uvx"), default="path",
        help="path: run compliance-mcp from PATH; uvx: run the released version with uvx",
    )
    args = parser.parse_args()
    if args.check and (args.output or args.launcher != "path"):
        parser.error("--check verifies the checked-in path-launcher bundles only")
    return sync(check=args.check, output=args.output, launcher=args.launcher)


if __name__ == "__main__":
    raise SystemExit(main())
