from __future__ import annotations

import ast
import asyncio
import copy
import importlib.util
from types import SimpleNamespace


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
    "def evaluate_completeness(entity, *, completeness=0.95):\n"
    "    \"\"\"Return a measurement envelope for the given entity.\"\"\"\n"
    "    return {'project': entity.project, 'entity': entity.name,\n"
    "            'objective_ref': " + repr(_OBJECTIVE_REF) + ", 'objective': " + repr(_OBJECTIVE) + ",\n"
    "            'metric_result': {'metric': " + repr(_METRIC) + ", 'value': completeness,\n"
    "                              'computed_at': '2026-01-02T03:04:05Z'},\n"
    "            'provenance': {'run': json.dumps('combined')}}\n"
)


def _combined_request(source=_EVALUATOR_SOURCE, **overrides):
    evaluator = MetricEvaluationCodeArtifact(
        status="ready", source_code=source, entry_point="evaluate_completeness",
        entity_contract=EntityInputContract(
            kind="dataset", name="training-data", project="loans", interface="digitalhub",
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
    """Stands in for a DigitalHub DataItem/Model: extensions plus save(update=True)."""

    def __init__(self, extensions=None):
        self.project, self.name = "loans", "training-data"
        self.extensions = list(extensions or [])
        self.saved = []

    def save(self, update=False):
        assert update is True
        self.saved.append(copy.deepcopy(self.extensions))
        return self


def _load_combined(tmp_path, request):
    artifact = render_combined_report_artifact(request)
    assert artifact.status == "ready", artifact.unsupported_reasons
    path = tmp_path / artifact.entry_point
    path.write_text(artifact.files[artifact.entry_point])
    spec = importlib.util.spec_from_file_location("rendered_compliance_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _imported_roots(source):
    tree = ast.parse(source)
    roots = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names}
    return roots | {node.module.split(".")[0] for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module}


def test_combined_artifact_is_rendered_self_contained_and_valid():
    request = _combined_request()

    artifact = render_combined_report_artifact(request)
    result = validate_compliance_report_code(request, artifact)

    assert result["valid"], result["errors"]
    assert not result["warnings"]
    assert list(artifact.files) == ["compliance_report.py"]
    source = artifact.files["compliance_report.py"]
    assert not any(name.startswith("compliance_") for name in _imported_roots(source))
    assert "report_cli" not in source and "${" not in source
    assert "loans" not in source and "training-data" not in source
    assert artifact.target == {}
    assert artifact.invocation == ["compliance_report.py:run(project, entity, **kwargs)"]


def test_combined_validator_rejects_compliance_imports_and_missing_handler():
    request = _combined_request()
    artifact = render_combined_report_artifact(request)
    source = artifact.files["compliance_report.py"].replace(
        "import inspect\n", "import inspect\nfrom compliance_core.report_cli import main\n", 1,
    ).replace("def run(project: str, entity: Any, **kwargs: Any)", "def run(entity: Any)")

    result = validate_compliance_report_code(request, artifact.model_copy(update={"files": {
        "compliance_report.py": source}, "source_hashes": {}}))

    messages = [issue["message"] for issue in result["errors"]]
    assert not result["valid"]
    assert any("compliance packages" in message for message in messages)
    assert any("run(project, entity, **kwargs)" in message for message in messages)


def test_combined_rendering_reports_name_conflicts_as_unsupported():
    source = _EVALUATOR_SOURCE + "\ndef publish(*args, **kwargs):\n    return None\n"
    request = _combined_request(source=source)

    artifact = render_combined_report_artifact(request)

    assert artifact.status == "unsupported"
    assert any("publish" in reason for reason in artifact.unsupported_reasons)


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


def test_combined_build_reports_matches_core_verdicts(tmp_path):
    module = _load_combined(tmp_path, _combined_request())
    module.OBJECTIVES = {
        ref: {"id": ref, "metric": _METRIC, "condition": {"threshold": {"operator": "GEQ", "value": 0.8}}}
        for ref in ("o:1", "o:2", "o:3")
    }

    def envelope(value=0.9, reference="o:1", **extra):
        raw = {"project": "loans", "entity": "training-data", "objective_ref": reference,
               "objective": module.OBJECTIVES[reference],
               "metric_result": {"metric": _METRIC, "value": value, "computed_at": "2026-01-02T03:04:05Z"}}
        raw.update(extra)
        return raw

    scenarios = [
        [envelope()],
        [envelope(0.5), envelope(0.5, reference="o:2")],
        [envelope(), envelope(reference="o:2", status="ERROR", error="boom", metric_result=None)],
        [envelope(reference="o:3", status="INCOMPLETE", error="missing", metric_result=None)],
    ]
    for measurements in scenarios:
        expected = build_reports(copy.deepcopy(measurements), variants=["EVALUATION", "TEST"])["reports"]
        actual = module.build_reports({item["objective_ref"]: item for item in copy.deepcopy(measurements)})
        assert set(actual) == set(expected)
        for kind, report in actual.items():
            validate_report(report)
            assert report["objectives"] == expected[kind]["objectives"]
        if "EVALUATION" in expected:
            assert actual["EVALUATION"]["content"] == expected["EVALUATION"]["content"]
        expected_test, actual_test = expected["TEST"]["content"]["test"], actual["TEST"]["content"]["test"]
        assert actual_test["verdict"] == expected_test["verdict"]
        assert actual_test["results"] == [
            {key: value for key, value in check.items() if key != "details"} for check in expected_test["results"]
        ]


def test_combined_run_evaluates_entity_and_overwrites_reports(tmp_path):
    other = {"kind": "data-compliance", "name": "spec", "spec": {"objectives": []}}
    stale = {"kind": "compliance-report", "name": "dataset-tests", "spec": {"stale": True}}
    entity = _FakeEntity([other, stale])
    module = _load_combined(tmp_path, _combined_request())

    reports = module.run("loans", entity, completeness=0.5, unrelated="ignored")

    assert len(entity.saved) == 1
    assert entity.extensions[0] == other
    saved = {ext["name"]: ext["spec"] for ext in entity.extensions if ext["kind"] == "compliance-report"}
    assert set(saved) == {"dataset-quality", "dataset-tests"}
    assert saved["dataset-tests"] == reports["TEST"]
    assert saved["dataset-tests"]["content"]["test"]["verdict"] == "FAIL"
    assert saved["dataset-quality"]["content"]["evaluation"]["metrics"][0]["value"] == 0.5
    for report in saved.values():
        validate_report(report)

    module.run("loans", entity)
    saved = {ext["name"]: ext["spec"] for ext in entity.extensions if ext["kind"] == "compliance-report"}
    assert len(saved) == 2 and saved["dataset-tests"]["content"]["test"]["verdict"] == "PASS"


def test_combined_run_reports_evaluator_failures_as_error(tmp_path):
    source = _EVALUATOR_SOURCE.replace("    return {'project'", "    raise RuntimeError('no data')\n    return {'project'")
    entity = _FakeEntity()
    module = _load_combined(tmp_path, _combined_request(source=source))

    reports = module.run("loans", entity)

    assert set(reports) == {"TEST"}
    assert reports["TEST"]["content"]["test"]["verdict"] == "ERROR"
    assert "no data" in reports["TEST"]["content"]["test"]["summary"]
    validate_report(reports["TEST"])


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
