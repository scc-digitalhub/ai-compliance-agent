# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
from types import SimpleNamespace

from compliance_core.contracts.evaluation_code import (
    EntityInputContract,
    MetricEvaluationCodeArtifact,
    MetricEvaluationCodeOutput,
    MetricEvaluationCodeRequest,
)
from compliance_core.metric_computation import resolve_metric_computation
from compliance_core.metric_evaluation_tools import (
    TOOL_SPECS,
    generate_metric_evaluation_code,
    get_evaluation_schema,
    get_metric_computation,
    get_session_evaluation_codes,
    record_metric_evaluation_code,
    validate_metric_evaluation_code,
)
from compliance_core.state import CODES_KEY, InMemoryStateStore, scoped_get
from compliance_core.tools import ToolEnv


def _objective(bundle):
    return next(
        concept.instance for concept in bundle.concepts.values()
        if concept.id == "metric-data-completeness"
    )


def _request(bundle, **overrides):
    values = {
        "project": "loans",
        "entity_kind": "dataset",
        "entity": "training-data",
        "objective_ref": "urn:objective:completeness",
        "objective": {
            "name": "Completeness",
            "metric": _objective(bundle),
            "condition": {"threshold": {"operator": "GEQ", "value": 0.9}},
        },
        "bindings": {"frame": "entity['frame']", "required_columns": ["income"]},
        "computation_guidance": resolve_metric_computation(
            bundle, "metric-data-completeness", entity_kind="dataset",
        ),
    }
    values.update(overrides)
    return MetricEvaluationCodeRequest.model_validate(values)


def _artifact(request, source=None, **overrides):
    source = source or (
        "def evaluate_completeness(entity, *, evaluation_data=None):\n"
        "    frame = entity['frame']\n"
        "    value = float(frame.notna().mean().mean())\n"
        "    return {'metric': {'id': 'metric-data-completeness'}, 'value': value}\n"
    )
    fields = {
        "status": "ready",
        "source_code": source,
        "entry_point": "evaluate_completeness",
        "entity_contract": EntityInputContract(
            kind="dataset", project=request.project, name=request.entity, interface="mapping",
            entity_version=request.entity_version,
            fields={"frame": "read-only table"},
        ),
        "result_contract": {"type": "MeasurementEnvelope"},
        "objective_ref": request.objective_ref,
        "objective": request.objective,
        "metric": request.objective["metric"],
        "source_paths": ["catalog/metrics/data-quality/completeness.md"],
        "source_hashes": {
            "catalog/metrics/data-quality/completeness.md":
                request.computation_guidance["source_hash"],
        },
        "bundle_version": request.computation_guidance["bundle_version"],
        "parameters": {"frame": request.bindings["frame"]},
    }
    fields.update(overrides)
    return MetricEvaluationCodeArtifact.model_validate(fields)


def test_get_computation_is_tool_and_records_grounding(bundle):
    class Grounding:
        paths = []

        def record(self, path):
            self.paths.append(path)

    env = ToolEnv(InMemoryStateStore(), bundle, grounding=Grounding())
    result = get_metric_computation(env, "metric-data-completeness", "dataset")
    assert result["supported"]
    assert env.grounding.paths == [result["source_path"]]
    assert "get_metric_computation" in {spec.name for spec in TOOL_SPECS}


def test_static_validation_checks_syntax_binding_and_entity_contract(bundle):
    request = _request(bundle)
    artifact = _artifact(request)

    result = validate_metric_evaluation_code(request, artifact)

    assert result["valid"]
    assert result["ready"]
    assert result["normalized"]["validation"]["executed"] is False
    assert result["normalized"]["source_hash"] == hashlib.sha256(artifact.source_code.encode()).hexdigest()


def test_static_validation_rejects_side_effects_and_mismatched_target(bundle):
    request = _request(bundle)
    artifact = _artifact(
        request,
        source=(
            "def evaluate_completeness(entity):\n"
            "    print('result')\n"
            "    open('/home/user/result.json', 'w').write('x')\n"
            "    return 0\n"
        ),
    )
    result = validate_metric_evaluation_code(request, artifact)
    assert not result["valid"]
    assert any("prohibited side-effect" in issue["message"] for issue in result["errors"])
    assert any("prohibited side-effect function" in issue["message"] for issue in result["errors"])

    mismatch = artifact.model_copy(update={
        "entity_contract": EntityInputContract(
            kind="dataset", project="other", name=request.entity, interface="mapping",
        )
    })
    mismatch_result = validate_metric_evaluation_code(request, mismatch)
    assert not mismatch_result["valid"]
    assert any("project" in issue["message"] for issue in mismatch_result["errors"])


def test_nonready_artifacts_contain_no_success_shaped_code(bundle):
    request = _request(bundle)
    needs_input = MetricEvaluationCodeArtifact(
        status="needs_input", missing_inputs=["labels and predictions"],
    )
    result = validate_metric_evaluation_code(request, needs_input)
    assert result["valid"]
    assert result["ready"] is False
    assert "source_code" not in result["normalized"]


def test_recording_is_project_scoped_and_schema_is_public(bundle):
    env = ToolEnv(InMemoryStateStore(), bundle)
    request = _request(bundle)
    artifact = _artifact(request)

    stored = record_metric_evaluation_code(env, request, artifact)

    assert stored["valid"] and stored["stored"]
    records = scoped_get(env.state, CODES_KEY, "loans")
    assert stored["normalized"]["artifact_id"] in records
    result = get_session_evaluation_codes(env, "loans")
    assert result["project"] == "loans"
    assert stored["normalized"]["artifact_id"] in result["artifacts"]
    assert get_session_evaluation_codes(env, "other")["artifacts"] == {}
    assert "get_session_evaluation_codes" in {spec.name for spec in TOOL_SPECS}
    assert get_evaluation_schema()["properties"]["result"]["$ref"]


def test_delegated_generation_uses_engine_and_records_but_never_executes(bundle):
    request = _request(bundle)
    artifact = _artifact(request)

    class Engine:
        calls = []

        async def run(self, operation, supplied):
            self.calls.append((operation, supplied))
            return SimpleNamespace(
                data=MetricEvaluationCodeOutput(result=artifact, assumptions=["Used catalog example"]).model_dump(),
                meta=SimpleNamespace(model="fixture"),
            )

    engine = Engine()
    env = ToolEnv(InMemoryStateStore(), bundle, analysis_engine=engine)
    result = __import__("asyncio").run(generate_metric_evaluation_code(env, request))

    assert result["status"] == "ready"
    assert result["stored"] is True
    assert engine.calls[0][0] == "metric_evaluation_code"
    assert engine.calls[0][1].computation_guidance["source_path"] == "catalog/metrics/data-quality/completeness.md"
    assert result["assumptions"] == ["Used catalog example"]
