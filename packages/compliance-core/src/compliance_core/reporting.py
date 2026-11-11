"""Non-agent report construction shared by tools and external executables.

Reports retain supplied measurement times. External evidence is validated, not
independently verified. Aggregate precedence is ERROR > FAIL > INCONCLUSIVE > PASS.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from .contracts.metric_evaluation import MeasurementEnvelope
from .contracts.reports import ReportSpec
from .metric_evaluation import evaluate_measurement
from .objective_evaluation import aggregate_verdict
from .objective_refs import snapshot_hash


def validate_report(value: Any) -> ReportSpec:
    if isinstance(value, ReportSpec):
        value = value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, str):
        return ReportSpec.model_validate_json(value)
    return ReportSpec.model_validate(value)


def build_reports(
    results: Sequence[Any], *, variants: Sequence[str] = ("EVALUATION", "TEST"),
    lineage: Any = None,
) -> dict[str, Any]:
    if not isinstance(results, (list, tuple)) or not results:
        raise ValueError("at least one supplied measurement or explicit execution failure is required")
    if isinstance(variants, str) or not variants or len(set(variants)) != len(variants):
        raise ValueError("variants must be a nonempty unique list")
    if any(variant not in ("EVALUATION", "TEST") for variant in variants):
        raise ValueError("only EVALUATION and TEST reports can be built")
    envelopes = [MeasurementEnvelope.model_validate(
        result.model_dump(mode="json") if isinstance(result, MeasurementEnvelope) else result,
    ) for result in results]
    target = {(result.project, result.entity, result.entity_version, result.specification_revision) for result in envelopes}
    if len(target) != 1:
        raise ValueError("one report set must address one entity/project and versioned specification")
    references: dict[str, str] = {}
    seen: set[str] = set()
    metrics: dict[str, dict[str, Any]] = {}
    metric_identities: dict[str, str] = {}
    assessments = []
    issues = []
    mappings = []
    for result in envelopes:
        digest = snapshot_hash(result.objective)
        if result.objective_ref in references:
            raise ValueError("duplicate or conflicting results for an objective reference")
        references[result.objective_ref] = digest
        mappings.append({"reference": result.objective_ref, "snapshot_hash": digest,
                         "generated": result.objective_ref.startswith("urn:compliance:objective-snapshot:"),
                         "project": result.project, "entity": result.entity,
                         "entity_version": result.entity_version,
                         "specification_revision": result.specification_revision,
                         "objective": result.objective})
        if result.metric_result:
            metric = result.metric_result.model_dump(mode="json", exclude_none=True)
            identity = result.metric_result.metric.id
            metric_snapshot = snapshot_hash(metric["metric"])
            if identity in metric_identities and metric_identities[identity] != metric_snapshot:
                raise ValueError("conflicting metric snapshots")
            metric_identities[identity] = metric_snapshot
            # One measurement can intentionally support several objectives, but
            # conflicting values/times for the same metric need separate reports.
            if identity in metrics and metrics[identity] != metric:
                raise ValueError("conflicting measurements for one metric")
            metrics[identity] = metric
        assessment = evaluate_measurement(result)
        assessments.append(assessment)
        issues.extend({**issue, "objective_ref": result.objective_ref} for issue in assessment["issues"])
        seen.add(result.objective_ref)
    common = {"objectives": list(references)}
    if lineage is not None:
        common["lineage"] = lineage
    reports = {}
    if "EVALUATION" in variants:
        if not metrics:
            issues.append({"code": "no_measurements", "message": "No successful measurement available for an EVALUATION report"})
        else:
            reports["EVALUATION"] = validate_report({
                **common, "kind": "EVALUATION",
                "content": {"evaluation": {"metrics": list(metrics.values())}},
            }).model_dump(mode="json", exclude_none=True, by_alias=True)
    if "TEST" in variants:
        checks = []
        for result, assessment in zip(envelopes, assessments):
            if assessment["passed"] is not None:
                checks.append({
                    "measured": json.dumps(assessment["measured"], ensure_ascii=False, sort_keys=True, allow_nan=False),
                    "expected": assessment["expected"], "passed": assessment["passed"],
                    "details": json.dumps({"objective_ref": result.objective_ref,
                                           "metric_id": result.objective["metric"]["id"]}, sort_keys=True),
                })
        explanations = [f"{issue.get('objective_ref', 'report')}: {issue['message']}" for issue in issues]
        reports["TEST"] = validate_report({
            **common, "kind": "TEST",
            "content": {"test": {"results": checks,
                                 "verdict": aggregate_verdict([a["verdict"] for a in assessments]),
                                 "summary": "; ".join(explanations) or "All requested objective checks are determinate."}},
        }).model_dump(mode="json", exclude_none=True, by_alias=True)
    return {"reports": reports, "issues": issues, "objective_references": mappings,
            "assessments": assessments, "provenance": [result.provenance for result in envelopes],
            "target": {"project": envelopes[0].project, "entity": envelopes[0].entity,
                       "entity_version": envelopes[0].entity_version,
                       "specification_revision": envelopes[0].specification_revision}}
