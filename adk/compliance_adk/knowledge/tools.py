"""OKF navigation tools exposed to the agents.

Tools read lazily and return structured records (path, id, instance) so agents copy ids, uris and
enum values from the bundle instead of inventing them. Which tools an agent receives is declared by
the `adk_additional_tools` metadata of its skill.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from .okf import Concept, get_bundle

logger = logging.getLogger(__name__)


def _items(concepts: list[Concept], with_instance: bool = True) -> dict[str, Any]:
    return {"count": len(concepts), "items": [c.record(with_instance) for c in concepts]}


def _bad_path(exc: Exception, path: str) -> str:
    logger.warning("Rejected OKF path %r: %s", path, exc)
    return f"[INVALID PATH: {path}]"


def list_all_concepts() -> str:
    """List all concepts available in the OKF bundle (top-level index)."""
    return get_bundle().list_directory("")


def list_okf_directory(path: str) -> str:
    """List the concepts in an OKF bundle directory by reading its index.md.

    Use this to discover what exists before reading specific concepts.

    Args:
        path: Bundle-relative path, e.g. 'catalog/regulatory-refs' or 'catalog/metrics/fairness'.
    """
    try:
        return get_bundle().list_directory(path)
    except ValueError as exc:
        return _bad_path(exc, path)


def read_okf_concept(path: str) -> str:
    """Read one OKF concept file (front-matter and body).

    Use only after identifying the file via list_okf_directory or search_catalog.

    Args:
        path: Bundle-relative path, e.g. 'catalog/regulatory-refs/eu-ai-act.md'.
    """
    try:
        return get_bundle().read(path)
    except ValueError as exc:
        return _bad_path(exc, path)


def search_catalog(query: str, category: str = "") -> dict[str, Any]:
    """Keyword search over OKF catalog concepts, ranked by number of matching words.

    Args:
        query: Space-separated keywords, e.g. 'fairness demographic parity'.
        category: Optional bundle-relative sub-path, e.g. 'catalog/metrics'. Defaults to the catalog.
    """
    try:
        total, found = get_bundle().search(query, category)
    except ValueError as exc:
        return {"error": _bad_path(exc, category)}
    return {"total": total, **_items(found, with_instance=False)}


def get_regulatory_refs(frameworks: str = "") -> dict[str, Any]:
    """List RegulatoryRef instances, optionally filtered by framework keywords.

    Args:
        frameworks: Comma-separated keywords, e.g. 'eu-ai-act,gdpr'. Empty lists all.
    """
    keywords = [k.strip().lower() for k in frameworks.split(",") if k.strip()]
    found = [
        c
        for c in get_bundle().under("catalog/regulatory-refs")
        if not keywords or any(k in c.text_lower for k in keywords)
    ]
    return _items(found)


def get_requirements(framework: str, article: str = "") -> dict[str, Any]:
    """Get normative Requirement instances for a regulatory framework.

    Args:
        framework: e.g. 'eu-ai-act', 'gdpr', 'dsa', 'nis2', 'eu-charter', 'unesco',
            'iso-42001-annex-a', 'eba-ml'.
        article: Optional article keyword matched against file names, e.g. 'art10', 'art14'.
    """
    bundle = get_bundle()
    available = bundle.subdirectories("catalog/requirements")
    if framework not in available:
        return {"error": f"Framework '{framework}' not found", "available": available}
    found = [
        c
        for c in bundle.under(f"catalog/requirements/{framework}")
        if not article or article.lower() in c.path.rsplit("/", 1)[-1].lower()
    ]
    return _items(found)


def get_groups(vulnerability_or_kind: str = "") -> dict[str, Any]:
    """Get GroupSpec instances, optionally filtered by a keyword.

    Args:
        vulnerability_or_kind: e.g. 'vulnerable', 'protected', 'age', 'disability', 'employment', 'health'.
    """
    return _items(get_bundle().under("catalog/groups", vulnerability_or_kind))


def get_attributes(concern: str = "") -> dict[str, Any]:
    """Get AttributeRef instances, optionally filtered by a keyword.

    Args:
        concern: e.g. 'gdpr', 'protected', 'health', 'gender', 'race', 'age', 'credit'.
    """
    return _items(get_bundle().under("catalog/attributes", concern))


def get_metrics(concern_area: str, applies_to: str = "") -> dict[str, Any]:
    """Get Metric instances (ready to use as objective metrics) for a concern area.

    Args:
        concern_area: One of 'fairness', 'data-quality', 'performance', 'robustness',
            'explainability', 'calibration', 'privacy', 'environmental'.
        applies_to: Optional entity filter: 'Model', 'Dataset', 'ModelService'.
    """
    bundle = get_bundle()
    available = bundle.subdirectories("catalog/metrics")
    if concern_area not in available:
        return {"error": f"Concern area '{concern_area}' not found", "available": available}
    kw = applies_to.lower()
    found = [
        c
        for c in bundle.under(f"catalog/metrics/{concern_area}")
        if not kw or not c.applies_to or kw in c.applies_to.lower()
    ]
    return _items(found)


def get_misuse_scenarios(domain_or_kind: str = "") -> dict[str, Any]:
    """Get MisuseScenario instances, optionally filtered by a keyword.

    Args:
        domain_or_kind: e.g. 'adversarial', 'privacy', 'manipulation', 'healthcare', 'credit', 'llm'.
    """
    return _items(get_bundle().under("catalog/misuse-scenarios", domain_or_kind))


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    fn.__name__: fn
    for fn in (
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
}
