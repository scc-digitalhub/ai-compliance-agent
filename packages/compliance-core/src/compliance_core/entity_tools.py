"""Framework-neutral entity lookup tool."""
from __future__ import annotations

from typing import Any, Callable

from .ports import EntityKind
from .state import ENTITIES_KEY
from .tools import ToolEnv, ToolSpec

ENTITY_KINDS = ("dataset", "model")


def _error(message: str, code: str) -> dict[str, str]:
    return {"error": message, "code": code}


def get_entity_details(
    env: ToolEnv, kind: EntityKind, entity: str, refresh: bool = False
) -> dict[str, Any]:
    """Retrieve dataset or model details from the configured entity catalog.

    Details are cached in the current workspace state unless `refresh` is true.

    Args:
        kind: 'dataset' or 'model'.
        entity: Name of the dataset or model.
        refresh: True only when the user asks to reload the details.
    """
    if kind not in ENTITY_KINDS:
        return _error(
            f"Unknown kind '{kind}'; use one of {list(ENTITY_KINDS)}", "invalid_kind"
        )
    if env.entities is None:
        return _error("The entity catalog integration is not configured", "integration_unavailable")

    state = env.state
    cached = state.get(ENTITIES_KEY, {}).get(kind, {}).get(entity)
    if cached is not None and not refresh:
        return {"kind": kind, "entity": entity, "source": "session", "details": cached}
    try:
        details = env.entities.get(kind, entity)
    except Exception as exc:
        return _error(
            f"Could not retrieve {kind} '{entity}' from the entity catalog: {exc}",
            "dh_error",
        )
    if not details:
        return _error(f"No {kind} named '{entity}' was found in the entity catalog", "not_found")
    entities = state.get(ENTITIES_KEY, {})
    state[ENTITIES_KEY] = {
        **entities,
        kind: {**entities.get(kind, {}), entity: details},
    }
    return {"kind": kind, "entity": entity, "source": "dh", "details": details}


TOOL_SPEC = ToolSpec(
    name="get_entity_details",
    fn=get_entity_details,
    group="dh",
    description=get_entity_details.__doc__ or "",
    read_only=True,
)

ENTITY_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {TOOL_SPEC.name: get_entity_details}

__all__ = ["ENTITY_KINDS", "ENTITY_TOOL_REGISTRY", "TOOL_SPEC", "get_entity_details"]
