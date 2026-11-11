from __future__ import annotations

import asyncio
import json
from importlib.resources import files

import pytest

from compliance_core.analysis_engine import (
    ANALYSES,
    CODE_GENERATIONS,
    DATASET,
    PROJECT_CONTEXT,
    STRUCTURED_OPERATIONS,
    STRUCTURED_OPERATIONS_BY_KEY,
    AnalysisTrace,
    OutputRejected,
    build_response,
    check_output,
    run_validated,
)
from compliance_core.contracts.evaluation_code import (
    MetricEvaluationCodeArtifact,
    MetricEvaluationCodeOutput,
    MetricEvaluationCodeRequest,
)
from compliance_core.contracts.report_code import ReportCodeArtifact, ReportCodeOutput, ReportCodeRequest
from compliance_core.errors import OutputValidationError
from compliance_core.knowledge import get_bundle


def example(skill: str) -> dict:
    return json.loads(files("compliance_skills").joinpath("skills", skill, "references", "example.json").read_text())


class Scripted:
    def __init__(self, *answers):
        self.answers, self.messages = list(answers), []

    async def send(self, message: str) -> str:
        self.messages.append(message)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


REQUEST = PROJECT_CONTEXT.request_model.model_validate(
    {"name": "credit", "domain": "finance", "ai_task": "CLASSIFICATION", "goal": "Score loans"}
)


def run(conversation, retries=2):
    trace = AnalysisTrace()
    output, warnings = asyncio.run(run_validated(
        PROJECT_CONTEXT, REQUEST, conversation, bundle=get_bundle(), max_retries=retries, trace=trace,
    ))
    return output, warnings, trace


def test_invalid_answers_are_fed_back_until_valid():
    conversation = Scripted("not json", OutputRejected(["result: missing"]),
                            "```json\n" + json.dumps(example("project-context")) + "\n```")
    output, _, trace = run(conversation)
    assert output.result.risk_classification.risk_level == "HIGH"
    assert trace.attempts == 3
    assert json.loads(conversation.messages[0]) == REQUEST.model_dump(mode="json", exclude_none=True)
    assert "rejected" in conversation.messages[1] and "result: missing" in conversation.messages[2]


def test_semantic_errors_exhaust_retries():
    broken = example("project-context")
    broken["result"]["requirements"] = []
    with pytest.raises(OutputValidationError) as raised:
        run(Scripted(json.dumps(broken), json.dumps(broken)), retries=1)
    assert any("requirements must not be empty" in problem for problem in raised.value.issues)


def test_response_carries_trace_and_grounding():
    trace = AnalysisTrace()
    trace.observe_call("read_okf_concept", {"path": "catalog/requirements/x.md"})
    trace.collect({"items": [{"path": "catalog/metrics/y.md"}, {"path": "not-markdown"}]})
    trace.add_usage(3, None)
    output = PROJECT_CONTEXT.output_model.model_validate(example("project-context"))
    response = build_response(PROJECT_CONTEXT, output, ["w"], trace, request_id="r", model="m",
                              bundle=get_bundle(), latency_ms=1)
    assert response.meta.grounding == ["catalog/requirements/x.md", "catalog/metrics/y.md"]
    assert response.meta.usage.input_tokens == 3 and response.meta.warnings == ["w"]


def test_core_defines_each_analysis_once():
    assert {definition.key for definition in ANALYSES} == {"project_context", "dataset", "model"}
    assert DATASET.request_model.__name__ == "DatasetAnalysisRequest"


def test_code_generation_operations_share_structured_result_assumptions_contract():
    assert {definition.key for definition in CODE_GENERATIONS} == {
        "metric_evaluation_code",
        "compliance_report_code",
    }
    assert len(STRUCTURED_OPERATIONS) == len(ANALYSES) + len(CODE_GENERATIONS)
    assert set(STRUCTURED_OPERATIONS_BY_KEY) == {
        "project_context",
        "dataset",
        "model",
        "metric_evaluation_code",
        "compliance_report_code",
    }

    metric = STRUCTURED_OPERATIONS_BY_KEY["metric_evaluation_code"]
    report = STRUCTURED_OPERATIONS_BY_KEY["compliance_report_code"]
    assert metric.output_model.model_fields.keys() == {"result", "assumptions"}
    assert report.output_model.model_fields.keys() == {"result", "assumptions"}


def test_code_generation_outputs_are_static_validated_without_execution():
    cases = (
        (
            STRUCTURED_OPERATIONS_BY_KEY["metric_evaluation_code"],
            MetricEvaluationCodeRequest(
                project="credit",
                entity_kind="model",
                entity="credit-model",
                objective_ref="accuracy-objective",
                objective={
                    "metric": {"id": "accuracy"},
                    "condition": {"threshold": {"operator": "GEQ", "value": 0.8}},
                },
            ),
            MetricEvaluationCodeOutput(
                result=MetricEvaluationCodeArtifact(
                    status="needs_input", missing_inputs=["explicit predictions"],
                ),
                assumptions=["The model needs bound evaluation inputs."],
            ),
        ),
        (
            STRUCTURED_OPERATIONS_BY_KEY["compliance_report_code"],
            ReportCodeRequest(
                project="credit",
                entity_kind="model",
                entity="credit-model",
                language="python",
            ),
            ReportCodeOutput(
                result=ReportCodeArtifact(
                    status="needs_input",
                    language="python",
                    mode="standalone",
                    missing_inputs=["measurement source"],
                ),
                assumptions=["The result source was not supplied."],
            ),
        ),
    )
    for definition, request, output in cases:
        checked, errors, _ = check_output(
            definition, output.model_dump_json(), request, get_bundle(),
        )
        assert checked is not None, errors
        assert checked.assumptions == output.assumptions
