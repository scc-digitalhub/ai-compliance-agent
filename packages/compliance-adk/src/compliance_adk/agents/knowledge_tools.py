"""ADK-compatible wrappers around the framework-neutral knowledge tools."""
from __future__ import annotations

from typing import Any, Callable

from compliance_core.knowledge_tools import TOOL_SPECS
from compliance_core.state import InMemoryStateStore
from compliance_core.tools import ToolEnv

from compliance_core.knowledge import get_bundle

_CORE_TOOLS = {spec.name: spec.fn for spec in TOOL_SPECS}


def _invoke(name: str, *args: Any, **kwargs: Any) -> Any:
    env = ToolEnv(state=InMemoryStateStore(), bundle=get_bundle())
    return _CORE_TOOLS[name](env, *args, **kwargs)


def list_all_concepts() -> str:
    return _invoke("list_all_concepts")


def list_okf_directory(path: str) -> str:
    return _invoke("list_okf_directory", path)


def read_okf_concept(path: str) -> str:
    return _invoke("read_okf_concept", path)


def search_catalog(query: str, category: str = "") -> dict[str, Any]:
    return _invoke("search_catalog", query, category)


def get_regulatory_refs(frameworks: str = "") -> dict[str, Any]:
    return _invoke("get_regulatory_refs", frameworks)


def get_requirements(framework: str, article: str = "") -> dict[str, Any]:
    return _invoke("get_requirements", framework, article)


def get_groups(vulnerability_or_kind: str = "") -> dict[str, Any]:
    return _invoke("get_groups", vulnerability_or_kind)


def get_attributes(concern: str = "") -> dict[str, Any]:
    return _invoke("get_attributes", concern)


def get_metrics(concern_area: str, applies_to: str = "") -> dict[str, Any]:
    return _invoke("get_metrics", concern_area, applies_to)


def get_misuse_scenarios(domain_or_kind: str = "") -> dict[str, Any]:
    return _invoke("get_misuse_scenarios", domain_or_kind)


for _adapter in (
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
):
    _adapter.__doc__ = _CORE_TOOLS[_adapter.__name__].__doc__

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
