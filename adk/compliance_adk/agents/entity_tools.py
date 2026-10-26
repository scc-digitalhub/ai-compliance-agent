"""Tools of the entity-details skill: retrieve dataset and model details from the DH platform.

Retrieved details are kept in session state, like the analyses, so the conversation reuses them
without calling the platform again; the user may ask to refresh them.
"""
from __future__ import annotations

from typing import Any, Callable, Literal

from google.adk.tools import ToolContext

from ..dh import tools as dh
from .session_state import ENTITIES_KEY

EntityKind = Literal["dataset", "model"]
ENTITY_KINDS = ("dataset", "model")


def _error(message: str, code: str) -> dict[str, str]:
    return {"error": message, "code": code}


def get_entity_details(
    kind: EntityKind, entity: str, tool_context: ToolContext, refresh: bool = False
) -> dict[str, Any]:
    """Retrieve the details of a dataset or model registered on the DH platform.

    The details are kept in this conversation: later calls return them without contacting the platform
    (source 'session') unless `refresh` is True. Use them to build the input of analyze_dataset or
    analyze_model when the user names an entity.

    Args:
        kind: 'dataset' or 'model'.
        entity: Name of the dataset or model on the DH platform.
        refresh: True only when the user asks to reload the details from the DH platform.
    """
    if kind not in ENTITY_KINDS:
        return _error(f"Unknown kind '{kind}'; use one of {list(ENTITY_KINDS)}", "invalid_kind")
    state = tool_context.state
    cached = state.get(ENTITIES_KEY, {}).get(kind, {}).get(entity)
    if cached is not None and not refresh:
        return {"kind": kind, "entity": entity, "source": "session", "details": cached}
    try:
        details = dh.get_entity(entity, kind)
    except Exception as exc:  # the platform client may fail in many ways; report, don't raise
        return _error(f"Could not retrieve {kind} '{entity}' from the DH platform: {exc}", "dh_error")
    if not details:
        return _error(f"No {kind} named '{entity}' was found on the DH platform", "not_found")
    entities = state.get(ENTITIES_KEY, {})
    state[ENTITIES_KEY] = {**entities, kind: {**entities.get(kind, {}), entity: details}}
    return {"kind": kind, "entity": entity, "source": "dh", "details": details}


ENTITY_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {fn.__name__: fn for fn in (get_entity_details,)}
