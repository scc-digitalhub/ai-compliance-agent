from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "packages" / "compliance-skills" / "src" / "compliance_skills" / "skills"

COPILOT_CONFIG = {
    "$schema": "https://json.schemastore.org/mcp.json",
    "servers": {
        "ai-compliance": {
            "type": "stdio",
            "command": "compliance-mcp",
            "args": [],
        }
    },
}

CLAUDE_MANIFEST = {
    "name": "ai-compliance",
    "version": "0.1.0",
    "description": "Portable AI compliance skills and MCP tools.",
    "mcpServers": {
        "ai-compliance": {
            "command": "compliance-mcp",
            "args": [],
        }
    },
}

OPENCODE_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
        "ai-compliance": {
            "type": "local",
            "command": ["compliance-mcp"],
            "enabled": True,
        }
    },
}

HOSTS = {
    "copilot": {
        "skills": Path(".github/skills"),
        "config": Path(".vscode/mcp.json"),
        "manifest": COPILOT_CONFIG,
    },
    "claude-code": {
        "skills": Path("skills"),
        "config": Path(".claude-plugin/plugin.json"),
        "manifest": CLAUDE_MANIFEST,
    },
    "opencode": {
        "skills": Path(".opencode/skills"),
        "config": Path("opencode.json"),
        "manifest": OPENCODE_CONFIG,
    },
}


def expected_files() -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    for host, settings in HOSTS.items():
        base = ROOT / "integrations" / host
        skills_path = settings["skills"]
        for skill_dir in sorted(SKILLS.iterdir()):
            if not skill_dir.is_dir():
                continue
            for source in sorted(path for path in skill_dir.rglob("*") if path.is_file()):
                relative = source.relative_to(SKILLS)
                files[base / skills_path / relative] = source.read_bytes()

        config_path = base / settings["config"]
        files[config_path] = (
            json.dumps(settings["manifest"], indent=2, ensure_ascii=False) + "\n"
        ).encode()
    return files


def sync(*, check: bool) -> int:
    stale: list[Path] = []
    files = expected_files()
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
            skill_root = ROOT / "integrations" / host / settings["skills"]
            if not skill_root.exists():
                continue
            for path in skill_root.rglob("*"):
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
        help="fail if generated bundle files differ from the canonical skills",
    )
    args = parser.parse_args()
    return sync(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
