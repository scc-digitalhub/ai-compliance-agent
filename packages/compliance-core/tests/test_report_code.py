from __future__ import annotations

import ast
import asyncio
import copy
import importlib.util
import json
import sys
import types
from types import SimpleNamespace

import pytest

from compliance_core.contracts.evaluation_code import EntityInputContract, MetricEvaluationCodeArtifact
from compliance_core.contracts.report_code import ReportCodeArtifact, ReportCodeOutput, ReportCodeRequest
from compliance_core.report_code_tools import (
    generate_compliance_report_code,
    get_session_report_codes,
    render_combined_report_artifact,
    render_compliance_report_code,
)
from compliance_core.reporting import build_reports, validate_report
from compliance_core.report_code_tools import (
    TOOL_SPECS,
    get_report_code_schema,
    validate_compliance_report_code,
)
from compliance_core.state import CODES_KEY, InMemoryStateStore, scoped_get
from compliance_core.tools import ToolEnv


def _request(**overrides):
    values = {
        "project": "loans",
        "entity_kind": "dataset",
        "entity": "training-data",
        "language": "python",
        "mode": "standalone",
        "report_names": {"EVALUATION": "dataset-quality"},
        "variants": ["EVALUATION"],
        "input_contract": {"format": "canonical-json", "schema": "MeasurementEnvelope[]"},
        "objective_snapshots": [{"objective_ref": "urn:objective:complete"}],
    }
    values.update(overrides)
    return ReportCodeRequest.model_validate(values)


def _artifact(request, **overrides):
    values = {
        "status": "ready",
        "language": request.language,
        "mode": request.mode,
        "files": {
            "run.py": (
                "from compliance_core.report_cli import main\n"
                "if __name__ == '__main__':\n"
                "    raise SystemExit(main())\n"
            )
        },
        "entry_point": "run.py",
        "invocation": [
            "python run.py preview --results results.json",
            "python run.py publish --results results.json",
        ],
        "input_contract": request.input_contract,
        "objective_snapshots": request.objective_snapshots,
        "target": {
            "project": request.project,
            "entity_kind": request.entity_kind,
            "entity": request.entity,
        },
        "report_names": {"EVALUATION": "dataset-quality"},
        "declared_effects": [{
            "operation": "publish_report",
            "extension_kind": "compliance-report",
            "report_kind": "EVALUATION",
            "report_name": "dataset-quality",
            "project": request.project,
            "entity_kind": request.entity_kind,
            "entity": request.entity,
        }],
    }
    values.update(overrides)
    return ReportCodeArtifact.model_validate(values)


def test_standalone_python_artifact_checks_target_effect_and_invocations():
    request = _request()
    artifact = _artifact(request)

    result = validate_compliance_report_code(request, artifact)

    assert result["valid"]
    assert result["normalized"]["validation"]["executed"] is False
    assert "get_report_code_schema" in {spec.name for spec in TOOL_SPECS}
    assert get_report_code_schema()["properties"]["result"]["$ref"]


def test_report_code_rejects_unbound_write_and_syntax_error():
    request = _request()
    artifact = _artifact(
        request,
        declared_effects=[{
            "operation": "publish_report", "extension_kind": "compliance-report",
            "report_kind": "EVALUATION", "report_name": "someone-elses-report",
            "project": "other", "entity_kind": "dataset", "entity": "other-data",
        }],
        files={"run.py": "def main(:\n    pass"},
    )

    result = validate_compliance_report_code(request, artifact)

    assert not result["valid"]
    assert any("write effect" in issue["message"] or "outside" in issue["message"] for issue in result["errors"])
    assert any("syntactically valid" in issue["message"] for issue in result["errors"])


def test_shell_wrapper_is_syntax_checked_without_execution():
    request = _request(language="shell")
    artifact = _artifact(
        request,
        language="shell",
        files={"run.sh": (
            "#!/bin/sh\n"
            "set -eu\n"
            "compliance-report preview --results \"$1\"\n"
            "compliance-report publish --results \"$1\"\n"
        )},
        entry_point="run.sh",
    )

    result = validate_compliance_report_code(request, artifact)

    assert result["valid"]
    assert result["normalized"]["validation"]["shell_syntax_only"] is True


_OBJECTIVE_REF = "urn:objective:complete"
_METRIC = {"id": "completeness", "name": "Completeness", "kind": "PRIMITIVE", "scale": "RATIO"}
_OBJECTIVE = {"id": _OBJECTIVE_REF, "metric": _METRIC,
              "condition": {"threshold": {"operator": "GEQ", "value": 0.8}}}
_EVALUATOR_SOURCE = (
    "from __future__ import annotations\n"
    "import json\n\n"
    "OBJECTIVE = " + repr(_OBJECTIVE) + "\n\n"
    "def evaluate_completeness(entity, *, completeness=0.95):\n"
    "    \"\"\"Return a measurement envelope for the requested entity.\"\"\"\n"
    "    return {'project': entity['project'], 'entity': entity['name'],\n"
    "            'objective_ref': " + repr(_OBJECTIVE_REF) + ", 'objective': " + repr(_OBJECTIVE) + ",\n"
    "            'metric_result': {'metric': " + repr(_METRIC) + ", 'value': completeness,\n"
    "                              'computed_at': '2026-01-02T03:04:05+00:00'},\n"
    "            'provenance': {'run': json.dumps('combined')}}\n"
).replace("OBJECTIVE = " + repr(_OBJECTIVE) + "\n\n", "")


def _combined_request(source=_EVALUATOR_SOURCE, **overrides):
    evaluator = MetricEvaluationCodeArtifact(
        status="ready", source_code=source, entry_point="evaluate_completeness",
        entity_contract=EntityInputContract(
            kind="dataset", name="training-data", project="loans", interface="mapping",
        ),
        objective_ref=_OBJECTIVE_REF, objective=_OBJECTIVE, metric=_METRIC,
    )
    values = {
        "mode": "combined",
        "evaluator_artifacts": [evaluator],
        "objective_snapshots": [{"objective_ref": _OBJECTIVE_REF, "objective": _OBJECTIVE}],
        "variants": ["EVALUATION", "TEST"],
        "report_names": {"EVALUATION": "dataset-quality", "TEST": "dataset-tests"},
    }
    values.update(overrides)
    return _request(**values)


class _FakeEntity:
    def __init__(self, extensions=None):
        self.project, self.name, self.kind = "loans", "training-data", "table"
        self.extensions = list(extensions or [])

    def to_dict(self):
        return {"project": self.project, "name": self.name, "kind": self.kind,
                "extensions": copy.deepcopy(self.extensions)}


def _load_combined(tmp_path, monkeypatch, request, entity):
    artifact = render_combined_report_artifact(request)
    assert artifact.status == "ready", artifact.unsupported_reasons
    path = tmp_path / artifact.entry_point
    path.write_text(artifact.files[artifact.entry_point])
    updates = []
    sdk = types.ModuleType("digitalhub")

    def get_dataitem(identifier, project=None, entity_id=None):
        assert (identifier, project) == ("training-data", "loans")
        return copy.deepcopy(entity)

    def update_dataitem(found):
        updates.append(copy.deepcopy(found.extensions))
        entity.extensions = copy.deepcopy(found.extensions)
        return found

    sdk.get_dataitem, sdk.update_dataitem = get_dataitem, update_dataitem
    sdk.get_model = sdk.update_model = None
    monkeypatch.setitem(sys.modules, "digitalhub", sdk)
    spec = importlib.util.spec_from_file_location("rendered_compliance_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return artifact, module, updates


def test_combined_artifact_is_rendered_self_contained_and_valid():
    request = _combined_request()

    artifact = render_combined_report_artifact(request)
    result = validate_compliance_report_code(request, artifact)

    assert result["valid"], result["errors"]
    assert not result["warnings"]
    assert list(artifact.files) == ["compliance_report.py"]
    source = artifact.files["compliance_report.py"]
    tree = ast.parse(source)
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    assert "digitalhub" in imported
    assert not any(name.startswith("compliance_") for name in imported)
    assert "report_cli" not in source and "${" not in source
    assert "digitalhub" in artifact.dependencies
    assert artifact.invocation[0].startswith("python compliance_report.py preview")


def test_combined_validator_rejects_report_cli_import():
    request = _combined_request()
    artifact = render_combined_report_artifact(request)
    source = artifact.files["compliance_report.py"].replace(
        "import digitalhub\n", "import digitalhub\nfrom compliance_core.report_cli import main\n", 1,
    )

    result = validate_compliance_report_code(request, artifact.model_copy(update={"files": {
        "compliance_report.py": source}}))

    assert not result["valid"]
    assert any("compliance_" in issue["message"] for issue in result["errors"])


def test_combined_rendering_reports_name_conflicts_as_unsupported():
    source = _EVALUATOR_SOURCE + "\ndef run_report_workflow(*args, **kwargs):\n    return None\n"
    request = _combined_request(source=source)

    artifact = render_combined_report_artifact(request)

    assert artifact.status == "unsupported"
    assert any("run_report_workflow" in reason for reason in artifact.unsupported_reasons)


def test_combined_generation_and_render_tool_do_not_need_engine(bundle):
    request = _combined_request()
    env = ToolEnv(InMemoryStateStore(), bundle)

    generated = asyncio.run(generate_compliance_report_code(env, request))
    rendered = render_compliance_report_code(env, request)

    assert generated["status"] == "ready" and generated["stored"], generated
    assert generated["provenance"]["template"] == "templates/combined_report.py.tmpl"
    assert generated["provenance"]["model"] is None
    assert rendered["artifact"]["files"] == generated["artifact"]["files"]
    assert render_compliance_report_code(env, _request())["code"] == "unsupported_mode"
    spec = next(spec for spec in TOOL_SPECS if spec.name == "render_compliance_report_code")
    assert not spec.needs_llm


def test_combined_build_reports_matches_core(tmp_path, monkeypatch):
    _, module, _ = _load_combined(tmp_path, monkeypatch, _combined_request(), _FakeEntity())

    def envelope(value=0.9, reference="o:1", **extra):
        objective = {"id": reference, "metric": _METRIC,
                     "condition": {"threshold": {"operator": "GEQ", "value": 0.8}}}
        raw = {"project": "loans", "entity": "training-data", "objective_ref": reference,
               "objective": objective, "specification_revision": "rev-1",
               "metric_result": {"metric": _METRIC, "value": value,
                                 "computed_at": "2026-01-02T03:04:05+00:00"},
               "provenance": {"run": "r"}}
        raw.update(extra)
        return raw

    scenarios = [
        [envelope()],
        [envelope(0.5), envelope(0.5, reference="o:2")],
        [envelope(), envelope(reference="o:2", status="ERROR", error="boom", metric_result=None)],
        [envelope(reference="o:3", status="INCOMPLETE", error="missing", metric_result=None)],
    ]
    for measurements in scenarios:
        expected = build_reports(copy.deepcopy(measurements), variants=["EVALUATION", "TEST"])
        actual = module.build_reports(copy.deepcopy(measurements), variants=["EVALUATION", "TEST"])
        for key in ("reports", "objective_references", "provenance", "target"):
            assert json.loads(json.dumps(actual[key])) == json.loads(json.dumps(expected[key])), key
        assert [i["message"] for i in actual["issues"]] == [i["message"] for i in expected["issues"]]
    for invalid in ([envelope(), envelope(project="other", reference="o:2")],
                    [envelope(0.5), envelope(reference="o:2")]):
        with pytest.raises(ValueError):
            build_reports(copy.deepcopy(invalid), variants=["TEST"])
        with pytest.raises(ValueError):
            module.build_reports(copy.deepcopy(invalid), variants=["TEST"])


def test_combined_script_previews_and_publishes_with_sdk(tmp_path, monkeypatch, capsys):
    other = {"kind": "data-compliance", "name": "spec", "spec": {"objectives": []}}
    entity = _FakeEntity([other])
    _, module, updates = _load_combined(tmp_path, monkeypatch, _combined_request(), entity)

    assert module.main(["preview"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["status"] == "preview" and not updates
    assert preview["publication"]["write_performed"] is False

    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"evaluate_completeness": {"completeness": 0.5}}))
    assert module.main(["publish", "--inputs", str(inputs)]) == 0
    published = json.loads(capsys.readouterr().out)
    assert published["status"] == "published" and len(updates) == 1
    saved = {ext["name"]: ext["spec"] for ext in entity.extensions if ext["kind"] == "compliance-report"}
    assert entity.extensions[0] == other
    for item in published["reports"]:
        assert saved[item["name"]] == validate_report(item["report"]).model_dump(
            mode="json", by_alias=True, exclude_none=True)
    assert saved["dataset-tests"]["content"]["test"]["verdict"] == "FAIL"

    assert module.main(["publish"]) == 2
    assert "--overwrite" in capsys.readouterr().err and len(updates) == 1
    assert module.main(["publish", "--overwrite"]) == 0
    capsys.readouterr()
    assert len(updates) == 2
    assert saved_names(entity) == ["dataset-quality", "dataset-tests"]


def saved_names(entity):
    return sorted(ext["name"] for ext in entity.extensions if ext["kind"] == "compliance-report")


def test_record_and_delegated_generation_are_scoped_and_do_not_execute(bundle):
    request = _request()
    artifact = _artifact(request)

    class Engine:
        calls = []

        async def run(self, operation, supplied):
            self.calls.append((operation, supplied))
            return SimpleNamespace(
                data=ReportCodeOutput(result=artifact, assumptions=["Used canonical result contract"]).model_dump(),
                meta=SimpleNamespace(model="fixture"),
            )

    engine = Engine()
    env = ToolEnv(InMemoryStateStore(), bundle, analysis_engine=engine)
    generated = asyncio.run(generate_compliance_report_code(env, request))

    assert generated["status"] == "ready"
    assert generated["stored"]
    assert engine.calls[0][0] == "compliance_report_code"
    assert generated["validation"]["normalized"]["validation"]["executed"] is False
    records = scoped_get(env.state, CODES_KEY, request.project)
    assert generated["artifact"]["artifact_id"] in records
    session_codes = get_session_report_codes(env, request.project)
    assert generated["artifact"]["artifact_id"] in session_codes["artifacts"]
    assert "get_session_report_codes" in {spec.name for spec in TOOL_SPECS}
    assert generated["assumptions"] == ["Used canonical result contract"]


def test_strict_atomic_generation_is_explicitly_unsupported_without_engine(bundle):
    request = _request(strict_atomic=True)
    env = ToolEnv(InMemoryStateStore(), bundle)

    result = asyncio.run(generate_compliance_report_code(env, request))

    assert result["status"] == "unsupported"
    assert "strict atomic" in result["artifact"]["unsupported_reasons"][0].lower()
