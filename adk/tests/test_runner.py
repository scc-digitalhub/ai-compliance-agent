from __future__ import annotations

import asyncio
import copy

import pytest

from compliance_adk.contracts import DatasetAnalysisRequest, ProjectInput
from compliance_adk.errors import OutputValidationError, UpstreamModelError, UpstreamRateLimited

from .conftest import DATASET, PROJECT, example


def run(coro):
    return asyncio.run(coro)


def test_project_context_with_grounding_and_usage(make_registry):
    registry, _ = make_registry(
        {"call": "get_requirements", "args": {"framework": "eu-ai-act"}},
        example("project-context"),
    )
    out = run(registry.get("project_context").run(ProjectInput(**PROJECT), request_id="rid-1"))

    assert out.data.risk_classification.risk_level == "HIGH"
    meta = out.meta
    assert meta.request_id == "rid-1" and meta.attempts == 1
    assert "catalog/requirements/eu-ai-act/art14-human-oversight.md" in meta.grounding
    assert meta.usage.input_tokens == 20 and meta.usage.output_tokens == 10
    assert meta.assumptions == example("project-context")["assumptions"]
    assert meta.okf_version == registry.bundle.version


def test_retries_with_feedback_then_succeeds(make_registry):
    bad = example("dataset-analysis")
    bad["result"]["objectives"][0]["requirements"] = ["req-does-not-exist"]
    registry, llm = make_registry(bad, example("dataset-analysis"))

    request = DatasetAnalysisRequest(dataset=DATASET)
    out = run(registry.get("dataset").run(request))

    assert out.meta.attempts == 2
    assert "req-does-not-exist" in llm.seen_messages[1] and "rejected" in llm.seen_messages[1]


def test_gives_up_after_retries(make_registry):
    bad = example("dataset-analysis")
    bad["result"]["scope"] = "VALIDATION"  # differs from the input scope
    registry, _ = make_registry(bad, copy.deepcopy(bad))

    with pytest.raises(OutputValidationError) as exc:
        run(registry.get("dataset").run(DatasetAnalysisRequest(dataset=DATASET)))
    assert any("scope" in i for i in exc.value.issues)


def test_schema_violation_is_reported_to_the_model(make_registry):
    bad = example("model-analysis")
    bad["result"]["objectives"][0]["condition"] = {}
    registry, llm = make_registry(bad, example("model-analysis"))
    from compliance_adk.contracts import ModelAnalysisRequest

    run(registry.get("model").run(ModelAnalysisRequest(model={"name": "m", "ai_task": "CLASSIFICATION"})))
    assert "exactly one condition" in llm.seen_messages[1]


def test_threshold_outside_metric_range_is_rejected(make_registry):
    bad = example("dataset-analysis")
    bad["result"]["objectives"][0]["condition"] = {"threshold": {"operator": "GEQ", "value": 95.0}}
    registry, llm = make_registry(bad, example("dataset-analysis"))
    run(registry.get("dataset").run(DatasetAnalysisRequest(dataset=DATASET)))
    assert "outside the metric range" in llm.seen_messages[1]


def test_warnings_do_not_fail_the_request(make_registry):
    data = example("dataset-analysis")
    data["result"]["attributes"] = []  # known protected attribute 'age' missing
    registry, _ = make_registry(data)
    out = run(registry.get("dataset").run(DatasetAnalysisRequest(dataset=DATASET)))
    assert any("age" in w for w in out.meta.warnings)


def test_provider_errors_are_mapped(make_registry):
    registry, llm = make_registry()
    llm.fail_with = RuntimeError("boom")
    with pytest.raises(UpstreamModelError):
        run(registry.get("project_context").run(ProjectInput(**PROJECT)))

    class RateLimitError(Exception):
        status_code = 429

    llm.fail_with = RateLimitError("slow down")
    with pytest.raises(UpstreamRateLimited):
        run(registry.get("project_context").run(ProjectInput(**PROJECT)))
