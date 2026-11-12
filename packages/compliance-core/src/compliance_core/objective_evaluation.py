# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Deterministic objective comparisons; no statistical tests are executed."""
from __future__ import annotations

import operator
from typing import Any

from .contracts.reports import finite_json, numeric

OPERATORS = {"GEQ": operator.ge, "LEQ": operator.le, "GT": operator.gt,
             "LT": operator.lt, "EQ": operator.eq, "NEQ": operator.ne}


def validate_condition(condition: dict[str, Any], _depth: int = 0) -> dict[str, Any]:
    finite_json(condition)
    if _depth > 32 or not isinstance(condition, dict) or len(condition) != 1:
        raise ValueError("exactly one condition variant is required (maximum depth 32)")
    kind, body = next(iter(condition.items()))
    if not isinstance(body, dict):
        raise ValueError("condition body must be an object")
    if kind == "threshold":
        valid = set(body) == {"operator", "value"} and body["operator"] in OPERATORS and numeric(body["value"])
    elif kind == "range":
        valid = (set(body) == {"lower", "upper", "inclusive"} and numeric(body["lower"])
                 and numeric(body["upper"]) and body["lower"] <= body["upper"]
                 and isinstance(body["inclusive"], bool))
    elif kind == "categorical":
        allowed = body.get("allowed")
        valid = (set(body) == {"allowed"} and isinstance(allowed, list) and bool(allowed)
                 and all(isinstance(item, str) for item in allowed) and len(allowed) == len(set(allowed)))
    elif kind == "statistical":
        valid = (set(body) == {"test", "significance", "hypothesis"} and isinstance(body["test"], str)
                 and bool(body["test"]) and isinstance(body["hypothesis"], str)
                 and numeric(body["significance"]) and 0 < body["significance"] < 1)
    elif kind == "composite":
        valid = (set(body) == {"operator", "conditions"} and body["operator"] in ("AND", "OR")
                 and isinstance(body["conditions"], list) and bool(body["conditions"]))
        if valid:
            for child in body["conditions"]:
                validate_condition(child, _depth + 1)
    else:
        valid = False
    if not valid:
        raise ValueError(f"invalid {kind} condition")
    return condition


def _out(verdict: str, reason: str | None = None) -> dict[str, Any]:
    return {"verdict": verdict, "passed": verdict == "PASS" if verdict in ("PASS", "FAIL") else None,
            "issues": [{"code": "inconclusive", "message": reason}] if reason else []}


def aggregate_verdict(verdicts: list[str]) -> str:
    if not verdicts:
        raise ValueError("at least one objective check is required")
    return next(value for value in ("ERROR", "FAIL", "INCONCLUSIVE", "PASS") if value in verdicts)


def evaluate_condition(value: Any, condition: dict[str, Any], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_condition(condition)
    finite_json(value)
    kind, body = next(iter(condition.items()))
    if kind == "composite":
        children = [evaluate_condition(value, child, evidence) for child in body["conditions"]]
        verdicts = [child["verdict"] for child in children]
        if body["operator"] == "AND":
            verdict = "FAIL" if "FAIL" in verdicts else "PASS" if all(v == "PASS" for v in verdicts) else "INCONCLUSIVE"
        else:
            verdict = "PASS" if "PASS" in verdicts else "FAIL" if all(v == "FAIL" for v in verdicts) else "INCONCLUSIVE"
        result = _out(verdict)
        result["issues"] = [issue for child in children for issue in child["issues"]]
        return result
    if kind == "statistical":
        return _out("INCONCLUSIVE", f"Named statistical test '{body['test']}' is not supported; supplied scalar/evidence is not a test execution")
    if kind in ("threshold", "range"):
        if not numeric(value):
            return _out("INCONCLUSIVE", "Numeric objective requires a finite scalar; provide an explicit selector for structured values")
        if kind == "threshold":
            passed = OPERATORS[body["operator"]](value, body["value"])
        elif body["inclusive"]:
            passed = body["lower"] <= value <= body["upper"]
        else:
            passed = body["lower"] < value < body["upper"]
    else:
        if not isinstance(value, str):
            return _out("INCONCLUSIVE", "Categorical objective requires a string")
        passed = value in body["allowed"]
    return _out("PASS" if passed else "FAIL")
