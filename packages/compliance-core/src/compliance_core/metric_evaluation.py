# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Validation and assessment of supplied measurements, never source execution."""
from __future__ import annotations

from typing import Any

from .contracts.metric_evaluation import MeasurementEnvelope
from .objective_evaluation import evaluate_condition


def select_value(value: Any, selector: str | None) -> Any:
    """Resolve an explicit RFC 6901 JSON pointer; no inferred keys or reductions."""
    if selector is None or selector == "":
        return value
    if not selector.startswith("/"):
        raise ValueError("selector must be an RFC 6901 JSON pointer")
    current = value
    for token in selector[1:].split("/"):
        if "~" in token.replace("~0", "").replace("~1", ""):
            raise ValueError("invalid JSON pointer escape")
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit() and (key == "0" or not key.startswith("0")):
            try:
                current = current[int(key)]
            except IndexError as exc:
                raise ValueError(f"selector component '{key}' was not found") from exc
        else:
            raise ValueError(f"selector component '{key}' was not found")
    return current


def evaluate_measurement(result: Any) -> dict[str, Any]:
    envelope = result if isinstance(result, MeasurementEnvelope) else MeasurementEnvelope.model_validate(result)
    if envelope.status != "SUCCESS":
        verdict = "ERROR" if envelope.status == "ERROR" else "INCONCLUSIVE"
        return {"objective_ref": envelope.objective_ref, "verdict": verdict, "passed": None,
                "issues": [{"code": envelope.status.lower(), "message": envelope.error}],
                "expected": envelope.objective["condition"]}
    selected = select_value(envelope.metric_result.value, envelope.selector)
    assessment = evaluate_condition(selected, envelope.objective["condition"], envelope.evidence)
    return {**assessment, "objective_ref": envelope.objective_ref, "measured": selected,
            "expected": envelope.objective["condition"], "metric_id": envelope.metric_result.metric.id}
