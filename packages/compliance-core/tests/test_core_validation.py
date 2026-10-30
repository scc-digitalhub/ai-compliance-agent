from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from compliance_core.validation import Issue, VALIDATORS, validate_context, validate_dataset

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "packages"


def test_core_validation_imports_without_adk_or_legacy_package() -> None:
    script = f"""
import sys
from importlib.abc import MetaPathFinder

class BlockLegacyPackages(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "compliance_adk" or fullname.startswith("compliance_adk."):
            raise AssertionError("core validation imported compliance_adk")
        if fullname == "google.adk" or fullname.startswith("google.adk."):
            raise AssertionError("core validation imported google.adk")
        return None

sys.meta_path.insert(0, BlockLegacyPackages())
sys.path.insert(0, {str(PACKAGE_DIR / "compliance-core" / "src")!r})
sys.path.insert(0, {str(PACKAGE_DIR / "compliance-dh" / "src")!r})
import compliance_core.contracts
import compliance_core.errors
import compliance_core.knowledge
import compliance_core.knowledge_tools
import compliance_dh.repositories
import compliance_core.ports
import compliance_core.state
import compliance_core.tool_catalog
import compliance_core.tools
import compliance_core.validation
import compliance_core.validation_tools
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_core_knowledge_bundle_can_be_injected_and_uses_repository_default() -> None:
    from importlib.resources import files

    from compliance_core.knowledge import get_bundle

    injected = get_bundle(Path(str(files("compliance_core").joinpath("data", "okf"))))
    default = get_bundle()

    assert injected.version == default.version
    assert injected.read("index.md").startswith("---")


def test_okf_and_okb_assets_are_package_data(monkeypatch) -> None:
    from importlib.resources import files

    from compliance_core.knowledge import get_bundle

    monkeypatch.delenv("OKF_PATH", raising=False)
    package = files("compliance_core")
    okf = package.joinpath("data", "okf")
    okb = package.joinpath("data", "okb")

    assert okf.joinpath("index.md").is_file()
    assert okb.joinpath("manifest.json").is_file()
    assert okb.joinpath("schemas", "ComplianceContext.json").is_file()
    assert get_bundle().root == Path(str(okf)).resolve()


def test_core_settings_resolve_workspace_and_okf_from_environment(monkeypatch, tmp_path: Path) -> None:
    from compliance_core.settings import get_core_settings

    custom_okf = tmp_path / "custom-okf"
    custom_okf.mkdir()
    custom_workspace = tmp_path / "workspace"
    monkeypatch.setenv("OKF_PATH", str(custom_okf))
    monkeypatch.setenv("COMPLIANCE_WORKSPACE", str(custom_workspace))
    get_core_settings.cache_clear()
    try:
        settings = get_core_settings()
        assert settings.okf_path == custom_okf
        assert settings.workspace_path == custom_workspace
    finally:
        get_core_settings.cache_clear()


def test_context_validation_keeps_semantic_checks() -> None:
    result = SimpleNamespace(
        regulations=[],
        requirements=[SimpleNamespace(
            id="unknown", source=SimpleNamespace(framework="EU_AI_ACT"), applicability_status="APPLICABLE",
        )],
        geography=[],
        risk_classification=SimpleNamespace(risk_level="UNKNOWN"),
    )
    bundle = SimpleNamespace(ids_of_type=lambda kind: {"known"}, concepts={})

    issues = validate_context(result, SimpleNamespace(), bundle)

    assert any(issue.message == "regulations must not be empty" for issue in issues)
    assert any(issue.message == "geography must not be empty" for issue in issues)
    assert any(issue.message == "requirement 'unknown' is not in the OKF bundle" for issue in issues)
    assert any(issue.message == "risk level could not be determined" for issue in issues)
    assert all(isinstance(issue, Issue) for issue in issues)


def test_dataset_validation_checks_scope_objectives_and_protected_attributes() -> None:
    result = SimpleNamespace(scope="TESTING", objectives=[], attributes=[])
    request = SimpleNamespace(
        dataset=SimpleNamespace(scope="TRAINING", known_protected_attributes=["age"])
    )
    bundle = SimpleNamespace(ids_of_type=lambda kind: set(), concepts={})

    issues = validate_dataset(result, request, bundle)

    assert [issue.severity for issue in issues] == ["error", "error", "warning"]
    assert "objectives must not be empty" in [issue.message for issue in issues]
    assert "scope must be 'TRAINING' as in the input, got 'TESTING'" in [issue.message for issue in issues]
    assert "known protected attribute 'age' is missing from attributes" in [issue.message for issue in issues]
    assert VALIDATORS["dataset"] is validate_dataset


def test_host_validation_helpers_expose_schemas_and_reject_invalid_outputs() -> None:
    from compliance_core.contracts import DatasetAgentOutput
    from compliance_core.validation_tools import get_output_schema, validate_dataset_compliance

    request = {
        "dataset": {"name": "sample", "scope": "TRAINING"},
    }
    bundle = SimpleNamespace(ids_of_type=lambda kind: set(), concepts={})

    result = validate_dataset_compliance(request, {"result": {}}, bundle)

    assert get_output_schema("dataset") == DatasetAgentOutput.model_json_schema()
    assert result["valid"] is False
    assert result["errors"]


def test_state_stores_share_mapping_behavior_and_workspace_persistence(tmp_path: Path) -> None:
    from compliance_core.state import (
        PROJECT_KEY,
        ENTITIES_KEY,
        FileStateStore,
        InMemoryStateStore,
        MappingStateStore,
        ComplianceWorkspace,
    )

    memory = InMemoryStateStore({"project": {"name": "credit"}})
    memory["models"] = {"risk": {"objectives": []}}
    assert memory.get("project") == {"name": "credit"}
    assert memory["models"]["risk"]["objectives"] == []

    host_state: dict[str, object] = {}
    adapter = MappingStateStore(host_state)
    adapter["context"] = {"risk": "HIGH"}
    assert host_state["context"] == {"risk": "HIGH"}

    directory = tmp_path / ".compliance"
    first = FileStateStore(directory)
    first[PROJECT_KEY] = {"name": "credit"}
    second = FileStateStore(directory)
    assert second[PROJECT_KEY] == {"name": "credit"}
    workspace = ComplianceWorkspace.from_store(second)
    assert workspace.project == {"name": "credit"}
    workspace.entities["dataset"] = {"sample": {"scope": "TRAINING"}}
    workspace.write_to(second)
    assert second[ENTITIES_KEY] == {"dataset": {"sample": {"scope": "TRAINING"}}}
    del second[PROJECT_KEY]
    assert PROJECT_KEY not in second


def test_core_tool_catalog_is_host_neutral_and_contains_reusable_capabilities() -> None:
    from compliance_core.tool_catalog import TOOL_CATALOG

    assert {
        "read_okf_concept",
        "get_entity_details",
        "get_compliance_specification",
        "save_compliance_specification",
        "validate_project_context",
        "validate_dataset_compliance",
        "validate_model_compliance",
        "get_output_schema",
        "record_compliance_analysis",
    }.issubset(TOOL_CATALOG)
    assert all(spec.name == name for name, spec in TOOL_CATALOG.items())


def test_host_record_tool_validates_before_persisting_workspace_state() -> None:
    import json
    from importlib.resources import files

    from compliance_core.host_tools import record_compliance_analysis
    from compliance_core.knowledge import get_bundle
    from compliance_core.state import (
        CONTEXT_KEY,
        DATASETS_KEY,
        MODELS_KEY,
        PROJECT_KEY,
        InMemoryStateStore,
    )
    from compliance_core.tools import ToolEnv

    skills = Path(str(files("compliance_skills").joinpath("skills")))
    state = InMemoryStateStore()
    env = ToolEnv(state=state, bundle=get_bundle())
    analyses = (
        (
            "project-context",
            "project",
            {
                "name": "Credit scoring",
                "domain": "finance",
                "ai_task": "CLASSIFICATION",
                "goal": "Assess creditworthiness of loan applicants",
            },
            PROJECT_KEY,
            CONTEXT_KEY,
        ),
        (
            "dataset-analysis",
            "dataset",
            {"dataset": {"name": "Applications 2024", "scope": "TRAINING"}},
            DATASETS_KEY,
            "Applications 2024",
        ),
        (
            "model-analysis",
            "model",
            {"model": {"name": "Credit model", "ai_task": "CLASSIFICATION"}},
            MODELS_KEY,
            "Credit model",
        ),
    )

    for skill, kind, request, state_key, entity_name in analyses:
        output = json.loads(
            (skills / skill / "references" / "example.json").read_text(encoding="utf-8")
        )
        result = record_compliance_analysis(env, kind, request, output, grounding=["catalog/requirements/eu-ai-act/art14-human-oversight.md"])
        assert result["valid"] is True
        assert result["stored"] is True
        if kind == "project":
            assert state[state_key]["name"] == request["name"]
            assert state[CONTEXT_KEY] == result["normalized"]["result"]
        else:
            assert state[state_key][entity_name] == result["normalized"]["result"]

    invalid = record_compliance_analysis(env, "dataset", {}, {"result": {}})
    assert invalid["valid"] is False
    assert invalid["stored"] is False
    assert set(state[DATASETS_KEY]) == {"Applications 2024"}
