"""
OKF bundle navigation tools for LangChain.

Tools are deliberately lazy: they read only what the agent asks for,
never scanning the whole bundle at once.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from config import settings

logger = logging.getLogger(__name__)

_OKF = settings.okf_bundle_path


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _resolve(rel: str) -> Path:
    """Resolve a bundle-relative path safely (no path traversal)."""
    p = (_OKF / rel).resolve()
    if not str(p).startswith(str(_OKF.resolve())):
        raise ValueError(f"Path traversal attempt blocked: {rel}")
    return p


def _read_file(path: Path) -> str:
    if not path.exists():
        return f"[NOT FOUND: {path.relative_to(_OKF)}]"
    return path.read_text(encoding="utf-8")


def _extract_frontmatter_field(text: str, field: str) -> str:
    """Quick regex extract of a frontmatter scalar value."""
    m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _concept_summary(path: Path) -> str:
    """One-line summary: relative_path — description."""
    text = _read_file(path)
    desc = _extract_frontmatter_field(text, "description")
    rel = path.relative_to(_OKF)
    return f"{rel}: {desc}" if desc else str(rel)


# ──────────────────────────────────────────────────────────────────────────────
# Public tools
# ──────────────────────────────────────────────────────────────────────────────

@tool
def list_okf_directory(path: str) -> str:
    """List the concepts available in an OKF bundle directory.

    Reads the directory's index.md to give an overview of available concepts
    without loading individual files. Use this first to discover what exists
    before reading specific concepts.

    Args:
        path: Bundle-relative path, e.g. 'catalog/regulatory-refs' or
              'catalog/metrics/fairness'.
    """
    logger.debug("list_okf_directory(path=%r)", path)
    index = _resolve(path) / "index.md"
    if index.exists():
        result = _read_file(index)
        logger.debug("list_okf_directory -> index.md (%d chars)", len(result))
        return result
    # Fallback: plain listing
    d = _resolve(path)
    if d.is_dir():
        names = sorted(f.name for f in d.iterdir() if f.suffix == ".md")
        logger.debug("list_okf_directory -> %d entries: %s", len(names), names)
        return f"Contents of {path}:\n" + "\n".join(names)
    logger.warning("list_okf_directory: directory not found: %r", path)
    return f"[Directory not found: {path}]"


@tool
def read_okf_concept(path: str) -> str:
    """Read a specific OKF concept file (frontmatter + body).

    Use this only after identifying the file you need via list_okf_directory
    or search_catalog. Reading unnecessary files wastes tokens.

    Args:
        path: Bundle-relative path, e.g.
              'catalog/regulatory-refs/eu-ai-act.md'
              'catalog/metrics/fairness/demographic-parity-difference.md'
    """
    logger.debug("read_okf_concept(path=%r)", path)
    result = _read_file(_resolve(path))
    logger.debug("read_okf_concept -> %d chars", len(result))
    return result


@tool
def search_catalog(query: str, category: str = "") -> str:
    """Keyword search across OKF catalog concept files.

    Scores each file by how many query words appear in its text, returning
    a ranked list of matching concepts with their descriptions.

    Args:
        query: Space-separated keywords, e.g. 'fairness demographic parity'.
        category: Optional sub-path to scope the search, e.g.
                  'catalog/metrics', 'catalog/requirements', 'catalog/groups'.
                  Defaults to the full catalog.
    """
    logger.debug("search_catalog(query=%r, category=%r)", query, category)
    root = _resolve(category) if category else _OKF / "catalog"
    if not root.is_dir():
        logger.warning("search_catalog: directory not found: %r", category)
        return f"[Directory not found: {category}]"

    words = [w.lower() for w in query.split() if w]
    scored: list[tuple[int, str]] = []

    for md in root.rglob("*.md"):
        if md.name in ("index.md", "log.md"):
            continue
        text = md.read_text(encoding="utf-8").lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            desc = _extract_frontmatter_field(md.read_text(encoding="utf-8"), "description")
            rel = str(md.relative_to(_OKF))
            scored.append((score, f"{rel}: {desc}" if desc else rel))

    if not scored:
        logger.debug("search_catalog: no matches for %r in %r", query, category or "catalog")
        return f"No concepts found for '{query}' in '{category or 'catalog'}'."

    scored.sort(key=lambda x: -x[0])
    lines = [entry for _, entry in scored[:25]]
    returned = min(len(scored), 25)
    logger.debug("search_catalog -> %d total matches, returning top %d", len(scored), returned)
    return f"Top matches for '{query}' ({len(scored)} total):\n" + "\n".join(lines)


@tool
def get_regulatory_refs(frameworks: str = "") -> str:
    """List available RegulatoryRef instances, optionally filtered by framework name.

    Args:
        frameworks: Comma-separated framework keywords to filter, e.g.
                    'eu-ai-act,gdpr'. Leave empty to list all.
    """
    logger.debug("get_regulatory_refs(frameworks=%r)", frameworks)
    ref_dir = _OKF / "catalog" / "regulatory-refs"
    keywords = [k.strip().lower() for k in frameworks.split(",") if k.strip()]
    results = []
    for md in sorted(ref_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if not keywords or any(k in text.lower() for k in keywords):
            results.append(_concept_summary(md))
    logger.debug("get_regulatory_refs -> %d results", len(results))
    return "\n".join(results) if results else "No matching regulatory references found."


@tool
def get_requirements(framework: str, article: str = "") -> str:
    """Get normative requirements for a regulatory framework.

    Args:
        framework: Framework key, e.g. 'eu-ai-act', 'gdpr', 'dsa',
                   'nis2', 'eu-charter', 'unesco', 'iso-42001-annex-a', 'eba-ml'.
        article: Optional article keyword to narrow results, e.g. 'art10', 'art14'.
    """
    logger.debug("get_requirements(framework=%r, article=%r)", framework, article)
    req_dir = _OKF / "catalog" / "requirements" / framework
    if not req_dir.is_dir():
        parent = _OKF / "catalog" / "requirements"
        avail = [d.name for d in parent.iterdir() if d.is_dir()]
        logger.warning("get_requirements: framework %r not found; available: %s", framework, avail)
        return f"Framework '{framework}' not found. Available: {avail}"
    results = []
    for md in sorted(req_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        if article and article.lower() not in md.name.lower():
            continue
        results.append(_concept_summary(md))
    logger.debug("get_requirements -> %d results", len(results))
    return "\n".join(results) if results else "No matching requirements found."


@tool
def get_groups(vulnerability_or_kind: str = "") -> str:
    """Get GroupSpec instances, optionally filtered by vulnerability type or kind.

    Args:
        vulnerability_or_kind: Optional keyword such as 'vulnerable', 'protected',
                                'age', 'disability', 'employment', 'health'.
                                Leave empty to list all groups.
    """
    logger.debug("get_groups(vulnerability_or_kind=%r)", vulnerability_or_kind)
    groups_dir = _OKF / "catalog" / "groups"
    kw = vulnerability_or_kind.lower()
    results = []
    for md in sorted(groups_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if not kw or kw in text.lower():
            results.append(_concept_summary(md))
    logger.debug("get_groups -> %d results", len(results))
    return "\n".join(results) if results else "No matching groups found."


@tool
def get_attributes(concern: str = "") -> str:
    """Get AttributeRef instances, optionally filtered by concern keyword.

    Args:
        concern: Optional keyword such as 'gdpr', 'protected', 'health',
                 'gender', 'race', 'age', 'ai-derived', 'credit'.
                 Leave empty to list all attributes.
    """
    logger.debug("get_attributes(concern=%r)", concern)
    attrs_dir = _OKF / "catalog" / "attributes"
    kw = concern.lower()
    results = []
    for md in sorted(attrs_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if not kw or kw in text.lower():
            results.append(_concept_summary(md))
    logger.debug("get_attributes -> %d results", len(results))
    return "\n".join(results) if results else "No matching attributes found."


@tool
def get_metrics(concern_area: str, applies_to: str = "") -> str:
    """Get Metric instances for a compliance concern area.

    Args:
        concern_area: One of 'fairness', 'data-quality', 'performance',
                      'robustness', 'explainability', 'calibration',
                      'privacy', 'environmental'.
        applies_to: Optional entity filter: 'Model', 'Dataset', 'ModelService'.
    """
    logger.debug("get_metrics(concern_area=%r, applies_to=%r)", concern_area, applies_to)
    metrics_dir = _OKF / "catalog" / "metrics" / concern_area
    if not metrics_dir.is_dir():
        avail = [d.name for d in (_OKF / "catalog" / "metrics").iterdir() if d.is_dir()]
        logger.warning("get_metrics: concern area %r not found; available: %s", concern_area, avail)
        return f"Concern area '{concern_area}' not found. Available: {avail}"
    kw = applies_to.lower()
    results = []
    for md in sorted(metrics_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if not kw or kw.lower() in text.lower():
            results.append(_concept_summary(md))
    logger.debug("get_metrics -> %d results", len(results))
    return "\n".join(results) if results else "No matching metrics found."


@tool
def get_misuse_scenarios(domain_or_kind: str = "") -> str:
    """Get MisuseScenario instances relevant to a domain or misuse kind.

    Args:
        domain_or_kind: Optional keyword such as 'adversarial', 'privacy',
                        'manipulation', 'healthcare', 'credit', 'llm'.
                        Leave empty to list all scenarios.
    """
    logger.debug("get_misuse_scenarios(domain_or_kind=%r)", domain_or_kind)
    ms_dir = _OKF / "catalog" / "misuse-scenarios"
    kw = domain_or_kind.lower()
    results = []
    for md in sorted(ms_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if not kw or kw in text.lower():
            results.append(_concept_summary(md))
    logger.debug("get_misuse_scenarios -> %d results", len(results))
    return "\n".join(results) if results else "No matching misuse scenarios found."


ALL_TOOLS = [
    list_okf_directory,
    read_okf_concept,
    search_catalog,
    get_regulatory_refs,
    get_requirements,
    get_groups,
    get_attributes,
    get_metrics,
    get_misuse_scenarios,
]
