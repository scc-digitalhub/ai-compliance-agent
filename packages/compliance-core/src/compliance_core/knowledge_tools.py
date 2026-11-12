# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Framework-neutral OKF navigation tools.

Tools read lazily and return structured records (path, id, instance) so agents copy ids, uris and
enum values from the bundle instead of inventing them. Runtime adapters select tools from
`TOOL_SPECS` according to the host's available skills and tool profile.
"""
from __future__ import annotations

import logging
from typing import Any

from .knowledge import Concept
from .tools import ToolEnv, ToolSpec

logger = logging.getLogger(__name__)


def _items(concepts: list[Concept], with_instance: bool = True) -> dict[str, Any]:
    return {"count": len(concepts), "items": [c.record(with_instance) for c in concepts]}


def _bad_path(exc: Exception, path: str) -> str:
    logger.warning("Rejected OKF path %r: %s", path, exc)
    return f"[INVALID PATH: {path}]"


def _record_paths(env: ToolEnv, value: Any) -> None:
    if env.grounding is None:
        return
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str) and path.endswith(".md"):
            env.grounding.record(path)
        for item in value.values():
            _record_paths(env, item)
    elif isinstance(value, list):
        for item in value:
            _record_paths(env, item)


def list_all_concepts(env: ToolEnv) -> str:
    """List all concepts available in the OKF bundle (top-level index)."""
    return env.bundle.list_directory("")


def list_okf_directory(env: ToolEnv, path: str) -> str:
    """List the concepts in an OKF bundle directory by reading its index.md.

    Use this to discover what exists before reading specific concepts.

    Args:
        path: Bundle-relative path, e.g. 'catalog/regulatory-refs' or 'catalog/metrics/fairness'.
    """
    try:
        if env.grounding is not None and path:
            env.grounding.record(path)
        return env.bundle.list_directory(path)
    except ValueError as exc:
        return _bad_path(exc, path)


def read_okf_concept(env: ToolEnv, path: str) -> str:
    """Read one OKF concept file (front-matter and body).

    Use only after identifying the file via list_okf_directory or search_catalog.

    Args:
        path: Bundle-relative path, e.g. 'catalog/regulatory-refs/eu-ai-act.md'.
    """
    try:
        if env.grounding is not None and path:
            env.grounding.record(path)
        return env.bundle.read(path)
    except ValueError as exc:
        return _bad_path(exc, path)


def search_catalog(env: ToolEnv, query: str, category: str = "") -> dict[str, Any]:
    """Keyword search over OKF catalog concepts, ranked by number of matching words.

    Args:
        query: Space-separated keywords, e.g. 'fairness demographic parity'.
        category: Optional bundle-relative sub-path, e.g. 'catalog/metrics'. Defaults to the catalog.
    """
    try:
        total, found = env.bundle.search(query, category)
    except ValueError as exc:
        return {"error": _bad_path(exc, category)}
    result = {"total": total, **_items(found, with_instance=False)}
    _record_paths(env, result)
    return result


def get_regulatory_refs(env: ToolEnv, frameworks: str = "") -> dict[str, Any]:
    """List RegulatoryRef instances, optionally filtered by framework keywords.

    Args:
        frameworks: Comma-separated keywords, e.g. 'eu-ai-act,gdpr'. Empty lists all.
    """
    keywords = [k.strip().lower() for k in frameworks.split(",") if k.strip()]
    found = [
        c
        for c in env.bundle.under("catalog/regulatory-refs")
        if not keywords or any(k in c.text_lower for k in keywords)
    ]
    result = _items(found)
    _record_paths(env, result)
    return result


def get_requirements(env: ToolEnv, framework: str, article: str = "") -> dict[str, Any]:
    """Get normative Requirement instances for a regulatory framework.

    Args:
        framework: e.g. 'eu-ai-act', 'gdpr', 'dsa', 'nis2', 'eu-charter', 'unesco',
            'iso-42001-annex-a', 'eba-ml'.
        article: Optional article keyword matched against file names, e.g. 'art10', 'art14'.
    """
    bundle = env.bundle
    available = bundle.subdirectories("catalog/requirements")
    if framework not in available:
        return {"error": f"Framework '{framework}' not found", "available": available}
    found = [
        c
        for c in bundle.under(f"catalog/requirements/{framework}")
        if not article or article.lower() in c.path.rsplit("/", 1)[-1].lower()
    ]
    result = _items(found)
    _record_paths(env, result)
    return result


def get_groups(env: ToolEnv, vulnerability_or_kind: str = "") -> dict[str, Any]:
    """Get GroupSpec instances, optionally filtered by a keyword.

    Args:
        vulnerability_or_kind: e.g. 'vulnerable', 'protected', 'age', 'disability', 'employment', 'health'.
    """
    result = _items(env.bundle.under("catalog/groups", vulnerability_or_kind))
    _record_paths(env, result)
    return result


def get_attributes(env: ToolEnv, concern: str = "") -> dict[str, Any]:
    """Get AttributeRef instances, optionally filtered by a keyword.

    Args:
        concern: e.g. 'gdpr', 'protected', 'health', 'gender', 'race', 'age', 'credit'.
    """
    result = _items(env.bundle.under("catalog/attributes", concern))
    _record_paths(env, result)
    return result


def get_metrics(env: ToolEnv, concern_area: str, applies_to: str = "") -> dict[str, Any]:
    """Get Metric instances (ready to use as objective metrics) for a concern area.

    Args:
        concern_area: One of 'fairness', 'data-quality', 'performance', 'robustness',
            'explainability', 'calibration', 'privacy', 'environmental'.
        applies_to: Optional entity filter: 'Model', 'Dataset', 'ModelService'.
    """
    bundle = env.bundle
    available = bundle.subdirectories("catalog/metrics")
    if concern_area not in available:
        return {"error": f"Concern area '{concern_area}' not found", "available": available}
    kw = applies_to.lower()
    found = [
        c
        for c in bundle.under(f"catalog/metrics/{concern_area}")
        if not kw or not c.applies_to or kw in c.applies_to.lower()
    ]
    result = _items(found)
    _record_paths(env, result)
    return result


def get_misuse_scenarios(env: ToolEnv, domain_or_kind: str = "") -> dict[str, Any]:
    """Get MisuseScenario instances, optionally filtered by a keyword.

    Args:
        domain_or_kind: e.g. 'adversarial', 'privacy', 'manipulation', 'healthcare', 'credit', 'llm'.
    """
    result = _items(env.bundle.under("catalog/misuse-scenarios", domain_or_kind))
    _record_paths(env, result)
    return result


_TOOLS = (
    list_all_concepts,
    list_okf_directory,
    read_okf_concept,
    search_catalog,
    get_regulatory_refs,
    get_requirements,
    get_groups,
    get_attributes,
    get_metrics,
    get_misuse_scenarios,
)

TOOL_SPECS = tuple(
    ToolSpec(
        name=fn.__name__,
        fn=fn,
        group="knowledge",
        description=fn.__doc__ or "",
        read_only=True,
    )
    for fn in _TOOLS
)

TOOL_REGISTRY = {spec.name: spec for spec in TOOL_SPECS}
