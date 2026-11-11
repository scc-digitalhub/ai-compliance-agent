"""Stable snapshot references for inline objectives without authoritative identifiers."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts.reports import finite_json


def snapshot_hash(value: Any) -> str:
    finite_json(value)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def objective_reference(
    objective: dict[str, Any], *, project: str, entity: str, specification_revision: str | None,
    position: int = 0, reference: str | None = None,
) -> dict[str, Any]:
    digest = snapshot_hash(objective)
    authoritative = reference or objective.get("id")
    if not authoritative and not specification_revision:
        raise ValueError("a specification revision is required for generated objective references")
    identity = {"project": project, "entity": entity, "specification_revision": specification_revision,
                "position": position, "snapshot_hash": digest}
    return {**identity, "reference": authoritative or f"urn:compliance:objective-snapshot:{snapshot_hash(identity)}",
            "generated": not bool(authoritative)}
