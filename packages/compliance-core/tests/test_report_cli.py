# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json

from compliance_core.knowledge import get_bundle
from compliance_core.report_cli import main, run_report_workflow
from compliance_core.specification_tools import specification_revision


def _result(spec_revision=None, entity_version=None):
    metric = next(
        concept.instance for concept in get_bundle().concepts.values()
        if concept.id == "metric-data-completeness"
    )
    objective = {
        "name": "Completeness",
        "metric": metric,
        "condition": {"threshold": {"operator": "GEQ", "value": 0.9}},
    }
    return {
        "project": "loans",
        "entity": "training-data",
        "entity_version": entity_version,
        "objective_ref": "urn:objective:complete",
        "objective": objective,
        "metric_result": {
            "metric": metric,
            "value": 0.95,
            "computed_at": "2026-11-11T08:30:00Z",
        },
        "status": "SUCCESS",
        "specification_revision": spec_revision,
        "provenance": {"source": "fixture"},
    }


class ReportRepo:
    supports_atomic_batch = False

    def __init__(self):
        self.items = {}
        self.batch_calls = []
        self.single_calls = []

    def get(self, kind, entity, name, project=None):
        return self.items.get((kind, entity, name, project), {})

    def save_batch(self, kind, entity, reports, project=None, *, strict_atomic=False):
        self.batch_calls.append((kind, entity, reports, project, strict_atomic))
        for name, report in reports.items():
            self.items[(kind, entity, name, project)] = report

    def save(self, kind, entity, name, report, project=None):
        self.single_calls.append(name)
        self.items[(kind, entity, name, project)] = report


def test_preview_builds_complete_reports_without_touching_repository():
    repo = ReportRepo()
    result = run_report_workflow(
        [_result()], mode="preview", project="loans", entity_kind="dataset",
        entity="training-data", variants=("EVALUATION", "TEST"), repository=repo,
    )

    assert result["status"] == "preview"
    assert [item["kind"] for item in result["reports"]] == ["EVALUATION", "TEST"]
    assert result["publication"]["write_performed"] is False
    assert repo.batch_calls == []
    assert repo.single_calls == []


def test_publish_validates_everything_then_uses_one_report_batch():
    repo = ReportRepo()
    result = run_report_workflow(
        [_result()], mode="publish", project="loans", entity_kind="dataset",
        entity="training-data", variants=("EVALUATION", "TEST"), repository=repo,
    )

    assert result["status"] == "published"
    assert len(repo.batch_calls) == 1
    assert repo.single_calls == []
    assert len(result["receipts"]) == 2
    assert result["publication"]["write_performed"] is True
    assert "not guaranteed" in result["publication"]["atomicity"]
    assert result["revision_check"]["status"] == "not_available"


def test_strict_atomicity_rejects_before_any_write():
    repo = ReportRepo()

    try:
        run_report_workflow(
            [_result()], mode="publish", project="loans", entity_kind="dataset",
            entity="training-data", variants=("EVALUATION", "TEST"), repository=repo,
            strict_atomic=True,
        )
    except ValueError as exc:
        assert "Strict atomic publication is not supported" in str(exc)
    else:
        raise AssertionError("strict atomicity should be rejected")
    assert repo.batch_calls == []


def test_explicit_entity_version_mismatch_is_rejected_before_publication():
    repo = ReportRepo()
    try:
        run_report_workflow(
            [_result(entity_version="v1")], mode="publish", project="loans",
            entity_kind="dataset", entity="training-data", entity_version="v2",
            variants=("EVALUATION",), repository=repo,
        )
    except ValueError as exc:
        assert "does not match the explicitly requested target version" in str(exc)
    else:
        raise AssertionError("an entity version mismatch must be rejected")
    assert repo.batch_calls == []


def test_named_report_conflict_requires_explicit_overwrite():
    repo = ReportRepo()
    repo.items[("dataset", "training-data", "compliance-evaluation", "loans")] = {"old": "report"}

    try:
        run_report_workflow(
            [_result()], mode="publish", project="loans", entity_kind="dataset",
            entity="training-data", variants=("EVALUATION",), repository=repo,
        )
    except ValueError as exc:
        assert "pass --overwrite" in str(exc)
    else:
        raise AssertionError("existing report must not be overwritten implicitly")
    assert repo.batch_calls == []


def test_cli_supports_preview_and_publish_and_emits_machine_json(capsys):
    repo = ReportRepo()
    fixture = json.dumps({"results": [_result()]})
    args = [
        "preview", "--results", "-", "--project", "loans",
        "--entity-kind", "dataset", "--entity", "training-data",
        "--variants", "EVALUATION,TEST",
    ]

    assert main(args, stdin=io.StringIO(fixture), repository=repo) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "preview"
    assert repo.batch_calls == []

    args[0] = "publish"
    assert main(args, stdin=io.StringIO(fixture), repository=repo) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "published"
    assert len(repo.batch_calls) == 1


def test_cli_rejects_invalid_json_and_target_before_writes(capsys):
    repo = ReportRepo()
    args = [
        "publish", "--results", "-", "--project", "wrong",
        "--entity-kind", "dataset", "--entity", "training-data",
    ]

    assert main(args, stdin=io.StringIO("[]"), repository=repo) == 2
    assert json.loads(capsys.readouterr().err)["status"] == "error"
    assert repo.batch_calls == []

    assert main(args, stdin=io.StringIO("{"), repository=repo) == 2
    assert "canonical UTF-8 JSON" in json.loads(capsys.readouterr().err)["error"]
    assert repo.batch_calls == []


def test_publish_compares_specification_revision_before_any_write():
    current_spec = {"objectives": [{"name": "current"}]}
    current_revision = specification_revision(current_spec)

    class RevisionReportRepo(ReportRepo):
        def get_specification_revision(self, kind, entity, project=None):
            return current_revision

    repo = RevisionReportRepo()
    result = run_report_workflow(
        [_result(current_revision)], mode="publish", project="loans",
        entity_kind="dataset", entity="training-data", variants=("EVALUATION",),
        repository=repo,
    )
    assert result["revision_check"]["status"] == "matched"
    assert result["revision_check"]["current_revision"] == current_revision

    class StaleReportRepo(ReportRepo):
        def get_specification_revision(self, kind, entity, project=None):
            return current_revision

    repo = StaleReportRepo()
    try:
        run_report_workflow(
            [_result("stale-revision")], mode="publish", project="loans",
            entity_kind="dataset", entity="training-data", variants=("EVALUATION",),
            repository=repo,
        )
    except ValueError as exc:
        assert "changed after evaluation" in str(exc)
    else:
        raise AssertionError("a stale specification revision must be rejected")
    assert repo.batch_calls == []


def test_revision_receipt_does_not_claim_a_check_without_live_reader():
    repo = ReportRepo()
    result = run_report_workflow(
        [_result("recorded-revision")], mode="publish", project="loans",
        entity_kind="dataset", entity="training-data", variants=("EVALUATION",),
        repository=repo,
    )
    assert result["revision_check"]["status"] == "not_available"
    assert "not checked against the live target" in result["revision_check"]["reason"]

    class MissingSpecRepo(ReportRepo):
        def get_specification_revision(self, kind, entity, project=None):
            return None

    repo = MissingSpecRepo()
    try:
        run_report_workflow(
            [_result("recorded-revision")], mode="publish", project="loans",
            entity_kind="dataset", entity="training-data", variants=("EVALUATION",),
            repository=repo,
        )
    except ValueError as exc:
        assert "no current target specification" in str(exc)
    else:
        raise AssertionError("an unavailable current revision must prevent a stale publish")
    assert repo.batch_calls == []
