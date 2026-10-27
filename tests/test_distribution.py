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
        "compliance_adk",
        "compliance_agent",
        "dataset_agent",
        "model_agent",
        "project_context_agent",
    }
    assert expected <= package_dirs.keys()
    assert all((ROOT / package_dirs[name]).is_dir() for name in expected)
