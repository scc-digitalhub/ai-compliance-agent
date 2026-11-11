"""Safe, catalog-grounded extraction of metric computation guidance."""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .knowledge import OkfBundle

_HEADING = re.compile(r"^(#{1,6})\s+Computation\s*$", re.IGNORECASE)
_NEXT_HEADING = re.compile(r"^(#{1,6})\s+")
_FENCE = re.compile(r"^```([^\n`]*)\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


def _section(text: str) -> str | None:
    lines = text.splitlines()
    start = None
    level = 0
    in_fence = False
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        match = _HEADING.match(line)
        if match and not in_fence:
            start, level = index, len(match.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    in_fence = False
    for index in range(start + 1, len(lines)):
        if lines[index].lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        match = _NEXT_HEADING.match(lines[index])
        if match and not in_fence and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def _code_blocks(section: str) -> list[dict[str, str]]:
    blocks = []
    for match in _FENCE.finditer(section):
        language = match.group(1).strip().lower().split(maxsplit=1)[0] if match.group(1).strip() else ""
        blocks.append({"language": language or "unspecified", "source": match.group(2).strip()})
    return blocks


def resolve_metric_computation(
    bundle: OkfBundle, metric_id: str, *, entity_kind: str | None = None,
) -> dict[str, Any]:
    """Return exact catalog identity, full computation section and all Python examples.

    The resolver only returns content found in the selected bundle. It never interprets or executes
    the examples. Ambiguous and missing identities are explicit unsupported results.
    """
    metric_id = metric_id.strip() if isinstance(metric_id, str) else ""
    if not metric_id:
        return {
            "supported": False, "status": "unsupported",
            "reason": "A catalog metric id is required.", "metric_id": metric_id,
            "bundle_version": bundle.version,
        }

    candidates = [
        concept for concept in bundle.concepts.values()
        if concept.path.startswith("catalog/metrics/")
        and (concept.id == metric_id or concept.title.casefold() == metric_id.casefold())
    ]
    if len(candidates) != 1:
        reason = "No catalog metric matched that identity." if not candidates else "The metric identity is ambiguous."
        return {
            "supported": False, "status": "unsupported", "reason": reason,
            "metric_id": metric_id, "matches": [c.record() for c in candidates],
            "bundle_version": bundle.version,
        }

    concept = candidates[0]
    text = bundle.read(concept.path)
    section = _section(text)
    if section is None:
        return {
            "supported": False, "status": "unsupported",
            "reason": "The catalog entry has no Computation section.",
            "metric": concept.record(), "source_path": concept.path,
            "applicability": concept.applies_to or None,
            "bundle_version": bundle.version,
        }

    blocks = _code_blocks(section)
    if not section.partition("\n")[2].strip():
        return {
            "supported": False, "status": "unsupported",
            "reason": "The catalog Computation section is empty.",
            "metric": concept.record(), "source_path": concept.path,
            "applicability": concept.applies_to or None,
            "bundle_version": bundle.version,
        }
    if entity_kind and concept.applies_to:
        applies = concept.applies_to.casefold()
        normalized_kind = "dataitem" if entity_kind == "dataset" else entity_kind.casefold()
        applicable = normalized_kind in applies or entity_kind.casefold() in applies or "both" in applies
        if not applicable:
            return {
                "supported": False, "status": "unsupported",
                "reason": f"Metric applicability '{concept.applies_to}' does not include {entity_kind}.",
                "metric": concept.record(), "source_path": concept.path,
                "applicability": concept.applies_to,
                "bundle_version": bundle.version,
            }

    return {
        "supported": True,
        "status": "available" if any(item["language"] in {"python", "py", "unspecified"} for item in blocks)
        else "prose_only",
        "metric": concept.record(),
        "source_path": concept.path,
        "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "applicability": concept.applies_to or None,
        "computation_section": section,
        "prose": _FENCE.sub("", section).strip(),
        "code_blocks": blocks,
        "python_code_blocks": [
            item for item in blocks if item["language"] in {"python", "py", "unspecified"}
        ],
        "bundle_version": bundle.version,
    }


__all__ = ["resolve_metric_computation"]
