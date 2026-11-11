from __future__ import annotations

import asyncio
from types import SimpleNamespace

from compliance_core.contracts.evaluation_code import EntityInputContract, MetricEvaluationCodeArtifact
from compliance_core.contracts.report_code import ReportCodeArtifact, ReportCodeOutput, ReportCodeRequest
from compliance_core.report_code_tools import (
    generate_compliance_report_code,
    get_session_report_codes,
)
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


def test_combined_python_artifact_must_include_and_call_each_evaluator():
    evaluator_source = (
        "def evaluate_completeness(entity, *, evaluation_data=None):\n"
        "    return {'value': 0.95}\n"
    )
    evaluator = MetricEvaluationCodeArtifact(
        status="ready", source_code=evaluator_source, entry_point="evaluate_completeness",
        entity_contract=EntityInputContract(
            kind="dataset", name="training-data", project="loans", interface="mapping",
        ),
        objective_ref="urn:objective:complete",
        objective={"metric": {"id": "metric-data-completeness"}},
        metric={"id": "metric-data-completeness"},
    )
    request = _request(
        mode="combined",
        evaluator_artifacts=[evaluator],
        objective_snapshots=[{
            "objective_ref": "urn:objective:complete",
            "objective": evaluator.objective,
        }],
    )
    artifact = _artifact(
        request,
        mode="combined",
        files={"run.py": (
            evaluator_source
            + "from compliance_core.report_cli import run_report_workflow\n"
            + "def run(entity, mode):\n"
            + "    results = [evaluate_completeness(entity)]\n"
            + "    return run_report_workflow(results, mode=mode, project='loans', "
            + "entity_kind='dataset', entity='training-data', variants=['EVALUATION'], "
            + "names={'EVALUATION': 'dataset-quality'})\n"
        )},
    )

    result = validate_compliance_report_code(request, artifact)

    assert result["valid"]


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
