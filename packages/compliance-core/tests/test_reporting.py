# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json

import pytest

from compliance_core.contracts.reports import ReportSpec
from compliance_core.knowledge import get_bundle
from compliance_core.report_tools import (
    build_compliance_report, get_compliance_report, prepare_compliance_report,
    save_compliance_report, validate_compliance_report,
)
from compliance_core.reporting import build_reports
from compliance_core.state import InMemoryStateStore, activate_project
from compliance_core.tools import ToolEnv


def evidence(value=.9, reference="o:1"):
    metric = {"id": "accuracy", "name": "Accuracy", "kind": "PRIMITIVE", "scale": "RATIO"}
    return {"project": "p", "entity": "m", "objective_ref": reference,
            "objective": {"id": reference, "metric": metric,
                          "condition": {"threshold": {"operator": "GEQ", "value": .8}}},
            "metric_result": {"metric": metric, "value": value, "computed_at": "2026-01-02T03:04:05+01:00"},
            "provenance": {"run": "run-1"}}


def test_evaluation_and_test_are_separate_and_keep_measurement_time():
    result = build_reports([evidence()], lineage={"sources": ["external:run"], "operation": "run-1"})
    assert set(result["reports"]) == {"EVALUATION", "TEST"}
    evaluation, test = result["reports"].values()
    assert set(evaluation["content"]) == {"evaluation"}
    assert "verdict" not in evaluation["content"]["evaluation"]
    assert evaluation["content"]["evaluation"]["metrics"][0]["computed_at"] == "2026-01-02T03:04:05+01:00"
    assert evaluation["objectives"] == ["o:1"] and evaluation["lineage"]["operation"] == "run-1"
    assert test["content"]["test"]["verdict"] == "PASS"
    check = test["content"]["test"]["results"][0]
    assert json.loads(check["measured"]) == .9 and check["expected"] == evidence()["objective"]["condition"]
    assert json.loads(check["details"]) == {"objective_ref": "o:1", "metric_id": "accuracy"}
    assert "provenance" not in evaluation
    assert result["provenance"] == [{"run": "run-1"}]


def test_one_measurement_can_support_multiple_explicit_objectives():
    one, two = evidence(), evidence(reference="o:2")
    two["objective"]["condition"]["threshold"]["value"] = .95
    result = build_reports([one, two])
    assert len(result["reports"]["EVALUATION"]["content"]["evaluation"]["metrics"]) == 1
    assert result["reports"]["TEST"]["content"]["test"]["verdict"] == "FAIL"
    assert len(result["reports"]["TEST"]["content"]["test"]["results"]) == 2


@pytest.mark.parametrize("status,expected", [("ERROR", "ERROR"), ("INCOMPLETE", "INCONCLUSIVE")])
def test_execution_issues_are_not_fabricated_failed_tests(status, expected):
    raw = evidence()
    raw.update(status=status, error="external computation unavailable", metric_result=None)
    result = build_reports([raw])
    test = result["reports"]["TEST"]["content"]["test"]
    assert test["verdict"] == expected and test["results"] == []
    assert "o:1" in test["summary"] and "external computation" in test["summary"]
    assert "EVALUATION" not in result["reports"]
    assert result["issues"]


def test_aggregate_precedence_and_no_false_pass_on_partial_results():
    fail = evidence(.5)
    incomplete = evidence(reference="o:2")
    incomplete.update(status="INCOMPLETE", error="missing data", metric_result=None)
    error = evidence(reference="o:3")
    error.update(status="ERROR", error="compute error", metric_result=None)
    for records, expected in (([fail, incomplete, error], "ERROR"), ([fail, incomplete], "FAIL"),
                              ([evidence(), incomplete], "INCONCLUSIVE")):
        assert build_reports(records)["reports"]["TEST"]["content"]["test"]["verdict"] == expected


def test_unsupported_statistics_keep_measurement_but_no_determinate_check():
    raw = evidence()
    raw["objective"]["condition"] = {"statistical": {"test": "unknown", "significance": .05, "hypothesis": "null"}}
    result = build_reports([raw])
    assert "EVALUATION" in result["reports"]
    assert result["reports"]["TEST"]["content"]["test"]["verdict"] == "INCONCLUSIVE"
    assert result["reports"]["TEST"]["content"]["test"]["results"] == []


def test_duplicate_conflicting_identity_and_version_mismatches_rejected():
    for other in (evidence(), {**evidence(reference="o:2"), "project": "q"},
                  {**evidence(reference="o:2"), "specification_revision": "new"},
                  evidence(.5, reference="o:2")):
        with pytest.raises(ValueError):
            build_reports([evidence(), other])
    for records, variants in (([], ["TEST"]), ([evidence()], []), ([evidence()], ["LOG"]), ([evidence()], "TEST")):
        with pytest.raises(ValueError):
            build_reports(records, variants=variants)


@pytest.mark.parametrize("content", [
    {}, {"evaluation": {"metrics": []}, "test": {"verdict": "INCONCLUSIVE"}},
    {"test": {"verdict": "INCONCLUSIVE"}}, {"evaluation": {"metrics": [], "verdict": "PASS"}},
])
def test_exactly_one_content_variant_and_kind_agreement(content):
    with pytest.raises(ValueError):
        ReportSpec.model_validate({"kind": "EVALUATION", "content": content})


def test_existing_log_reports_remain_valid():
    raw = {"kind": "LOG", "content": {"log": {"kind": "AUDIT", "window": {
        "from": "2026-01-01T00:00:00Z", "to": "2026-01-02T00:00:00Z"}}}}
    assert ReportSpec.model_validate(raw).model_dump(mode="json", by_alias=True, exclude_none=True) == {**raw, "objectives": []}


class Reports:
    def __init__(self):
        self.data = {}
        self.writes = 0

    def get(self, kind, entity, name, project=None):
        return copy.deepcopy(self.data.get((project, kind, entity, name), {}))

    def save(self, kind, entity, name, report, project=None):
        self.writes += 1
        self.data[project, kind, entity, name] = copy.deepcopy(report)


def tools():
    return ToolEnv(state=InMemoryStateStore(), bundle=get_bundle(), reports=Reports())


def test_named_report_conflicts_and_unrelated_reports_are_preserved():
    env = tools()
    report = build_reports([evidence()])["reports"]["EVALUATION"]
    first = save_compliance_report(env, "model", "m", "run-1", report, "p")
    assert first["saved"] and first["revision"]
    assert save_compliance_report(env, "model", "m", "run-2", report, "p")["saved"]
    fresh = tools()
    fresh.reports = env.reports
    assert save_compliance_report(fresh, "model", "m", "run-1", report, "p")["code"] == "conflict"
    assert get_compliance_report(fresh, "model", "m", "run-1", "p")["report"] == report
    changed = {**report, "objectives": ["other"]}
    env.reports.save("model", "m", "run-1", changed, "p")
    assert save_compliance_report(fresh, "model", "m", "run-1", report, "p")["code"] == "conflict"
    assert save_compliance_report(fresh, "model", "m", "run-1", report, "p", overwrite=True)["saved"]
    assert len(env.reports.data) == 2
    assert prepare_compliance_report(fresh.state, "model", "m", "run-1", project="p")["report"] == report


def test_reports_do_not_leak_between_project_workspaces():
    env = tools()
    report = build_reports([evidence()])["reports"]["TEST"]
    save_compliance_report(env, "model", "m", "checks", report, "p")
    activate_project(env.state, "q")
    assert save_compliance_report(env, "model", "m", "checks")["code"] == "not_found"
    assert prepare_compliance_report(env.state, "model", "m", "checks", project="p")["report"] == report


def test_tools_validate_input_and_never_write_when_building():
    env = tools()
    result = build_compliance_report(env, [evidence()])
    assert result["reports"] and env.reports.writes == 0
    assert build_compliance_report(env, [])["code"] == "invalid_input"
    assert validate_compliance_report(env, {"kind": "TEST", "content": {}})["code"] == "invalid_report"
    assert save_compliance_report(env, "project", "p", "r", {}, "p")["code"] == "invalid_kind"
    assert save_compliance_report(env, "model", "store://p/model/m", "r", {}, "q")["code"] == "project_mismatch"
    assert env.reports.writes == 0
