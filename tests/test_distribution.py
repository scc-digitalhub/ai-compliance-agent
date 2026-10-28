from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_one_python_distribution():
    manifests = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("pyproject.toml")
        if ".venv" not in path.parts and ".git" not in path.parts
    }

    assert manifests == {"pyproject.toml"}


def test_server_extra_does_not_install_google_adk():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    extras = config["project"]["optional-dependencies"]

    assert any(dep.startswith("google-adk") for dep in extras["adk"])
    assert not any(dep.startswith("google-adk") for dep in extras["server"])


def test_all_component_packages_are_included_in_the_unified_distribution():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    package_dirs = config["tool"]["setuptools"]["package-dir"]

    expected = {
        "compliance_core",
        "compliance_dh",
        "compliance_skills",
        "compliance_api",
        "compliance_mcp",
        "compliance_protocols",
        "compliance_adk",
        "compliance_agent",
        "dataset_agent",
        "model_agent",
        "project_context_agent",
    }
    assert expected <= package_dirs.keys()
    assert all((ROOT / package_dirs[name]).is_dir() for name in expected)


def test_portable_agent_is_packaged_alongside_skills():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    patterns = config["tool"]["setuptools"]["package-data"]["compliance_skills"]
    package = ROOT / config["tool"]["setuptools"]["package-dir"]["compliance_skills"]
    included = {path.relative_to(package).as_posix() for pattern in patterns for path in package.glob(pattern)}
    assert "agents/compliance-assistant.md" in included
    assert "skills/project-context/SKILL.md" in included


def test_shared_adk_package_uses_component_source_layout():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    package_dirs = config["tool"]["setuptools"]["package-dir"]
    source = "packages/compliance-adk/src/compliance_adk"
    for package, suffix in (
        ("compliance_adk", ""),
        ("compliance_adk.agents", "/agents"),
        ("compliance_adk.runtime", "/runtime"),
    ):
        assert package_dirs[package] == source + suffix
        assert (ROOT / package_dirs[package] / "__init__.py").is_file()
    assert not list((ROOT / "adk" / "compliance_adk").rglob("*.py"))


def test_protocol_adapters_have_optional_dependencies_and_entry_points():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    extras = config["project"]["optional-dependencies"]
    assert any(dep.startswith("agent-client-protocol") for dep in extras["acp"])
    assert any(dep.startswith("a2a-sdk") for dep in extras["a2a"])
    for extra in ("api", "mcp", "server"):
        assert not any(dep.startswith(("agent-client-protocol", "a2a-sdk", "google-adk")) for dep in extras[extra])
    assert config["project"]["scripts"]["compliance-acp"] == "compliance_protocols.acp:main"
    assert config["project"]["scripts"]["compliance-a2a"] == "compliance_protocols.a2a:main"
