from __future__ import annotations

import copy

import pytest

from compliance_core.contracts.metric_evaluation import MeasurementEnvelope
from compliance_core.contracts.reports import MetricResult
from compliance_core.metric_evaluation import evaluate_measurement, select_value
from compliance_core.objective_evaluation import evaluate_condition, validate_condition
from compliance_core.objective_refs import objective_reference


def envelope(value=0.9):
    metric = {"id": "accuracy", "name": "Accuracy", "kind": "PRIMITIVE", "scale": "RATIO",
              "range": {"lower": 0, "upper": 1}}
    return {"project": "p", "entity": "model", "objective_ref": "objective:accuracy",
            "objective": {"id": "objective:accuracy", "metric": metric,
                          "condition": {"threshold": {"operator": "GEQ", "value": 0.9}}},
            "metric_result": {"metric": metric, "value": value, "computed_at": "2026-01-02T03:04:05Z"}}


@pytest.mark.parametrize("op,expected", [
    ("GEQ", [False, True, True]), ("LEQ", [True, True, False]),
    ("GT", [False, False, True]), ("LT", [True, False, False]),
    ("EQ", [False, True, False]), ("NEQ", [True, False, True]),
])
def test_threshold_boundaries(op, expected):
    assert [evaluate_condition(v, {"threshold": {"operator": op, "value": 1}})["passed"]
            for v in (0, 1, 2)] == expected


@pytest.mark.parametrize("inclusive,expected", [(True, [True, True, True]), (False, [False, True, False])])
def test_ranges(inclusive, expected):
    condition = {"range": {"lower": 0, "upper": 2, "inclusive": inclusive}}
    assert [evaluate_condition(v, condition)["passed"] for v in (0, 1, 2)] == expected


@pytest.mark.parametrize("value", [True, "1", {"a": 1}, [1], None])
def test_type_mismatches_are_not_failed_checks(value):
    result = evaluate_condition(value, {"threshold": {"operator": "EQ", "value": 1}})
    assert result["verdict"] == "INCONCLUSIVE" and result["passed"] is None


def test_categories_and_composites():
    categorical = {"categorical": {"allowed": ["ok"]}}
    assert evaluate_condition("ok", categorical)["passed"]
    assert not evaluate_condition("bad", categorical)["passed"]
    assert evaluate_condition(1, categorical)["verdict"] == "INCONCLUSIVE"
    geq = {"threshold": {"operator": "GEQ", "value": 1}}
    lt = {"threshold": {"operator": "LT", "value": 3}}
    nested = {"composite": {"operator": "AND", "conditions": [
        geq, {"composite": {"operator": "OR", "conditions": [lt, categorical]}}]}}
    assert evaluate_condition(2, nested)["passed"]
    assert evaluate_condition(0, nested)["verdict"] == "FAIL"


def test_statistical_scalar_or_unmatched_evidence_never_passes():
    condition = {"statistical": {"test": "unknown", "significance": .05, "hypothesis": "null"}}
    assert evaluate_condition(.001, condition)["verdict"] == "INCONCLUSIVE"
    assert evaluate_condition(.001, condition, {"passed": True, "p_value": .001})["passed"] is None


@pytest.mark.parametrize("condition", [
    {}, {"threshold": {"operator": "=", "value": 1}},
    {"threshold": {"operator": "EQ", "value": True}},
    {"range": {"lower": 2, "upper": 1, "inclusive": True}},
    {"categorical": {"allowed": ["a", "a"]}},
    {"composite": {"operator": "AND", "conditions": []}},
    {"statistical": {"test": "test", "significance": 1.1, "hypothesis": "null"}},
])
def test_malformed_conditions_raise(condition):
    with pytest.raises(ValueError):
        validate_condition(condition)


def test_selectors_are_explicit_and_unambiguous():
    value = {"a/b": {"~": [1, 2]}}
    assert select_value(value, "/a~1b/~0/1") == 2
    for selector in ("a", "/missing", "/a~1b/~0/8", "/a~1b/~0/01", "/bad~2"):
        with pytest.raises(ValueError):
            select_value(value, selector)
    result = envelope({"precision": .8, "recall": .9})
    assert evaluate_measurement(result)["verdict"] == "INCONCLUSIVE"
    result["selector"] = "/recall"
    assert evaluate_measurement(result)["verdict"] == "PASS"


@pytest.mark.parametrize("timestamp", [None, "", "2026-01-01", "2026-01-01T00:00:00", 123])
def test_measurement_time_is_required_and_timezone_aware(timestamp):
    raw = envelope()["metric_result"]
    raw["computed_at"] = timestamp
    with pytest.raises(ValueError):
        MetricResult.model_validate(raw)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -.1, 1.1, {"a": float("-inf")}])
def test_nonfinite_or_out_of_range_measurements_rejected(value):
    with pytest.raises(ValueError):
        MeasurementEnvelope.model_validate(envelope(value))


def test_confidence_bounds_and_linkage_are_checked():
    raw = envelope()
    raw["metric_result"]["confidence"] = {"lower": .95, "upper": 1, "level": .95}
    with pytest.raises(ValueError):
        MeasurementEnvelope.model_validate(raw)
    raw = envelope()
    raw["metric_result"]["metric"] = {**raw["metric_result"]["metric"], "id": "other"}
    with pytest.raises(ValueError):
        MeasurementEnvelope.model_validate(raw)
    raw = envelope()
    raw["objective_ref"] = "other"
    with pytest.raises(ValueError):
        MeasurementEnvelope.model_validate(raw)


def test_execution_failure_is_distinct_from_invalid_measurement():
    raw = envelope()
    raw.update(status="ERROR", error="external computation failed", metric_result=None)
    assert evaluate_measurement(raw)["verdict"] == "ERROR"
    raw.update(status="INCOMPLETE", error="missing labels")
    assert evaluate_measurement(raw)["verdict"] == "INCONCLUSIVE"
    raw.update(status="SUCCESS")
    with pytest.raises(ValueError):
        evaluate_measurement(raw)


def test_objective_references_are_stable_scoped_and_change_with_snapshot():
    objective = envelope()["objective"]
    assert objective_reference(objective, project="p", entity="m", specification_revision="v")["reference"] == objective["id"]
    objective = copy.deepcopy(objective)
    objective.pop("id")
    kwargs = {"project": "p", "entity": "m", "specification_revision": "v", "position": 2}
    first = objective_reference(objective, **kwargs)
    assert first["generated"] and objective_reference(objective, **kwargs) == first
    assert objective_reference(objective, **{**kwargs, "project": "q"})["reference"] != first["reference"]
    objective["condition"]["threshold"]["value"] = .8
    assert objective_reference(objective, **kwargs)["reference"] != first["reference"]
    with pytest.raises(ValueError):
        objective_reference(objective, **{**kwargs, "specification_revision": None})
