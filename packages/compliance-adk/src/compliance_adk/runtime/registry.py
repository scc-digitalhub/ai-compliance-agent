"""Process-wide set of structured runners, shared by the API and the coordinator tools."""
from __future__ import annotations

from google.adk.models.base_llm import BaseLlm

from ..agents.specs import STRUCTURED_SPECS
from ..config import Settings, get_settings
from compliance_core.knowledge import OkfBundle, get_bundle
from .runner import StructuredRunner


class RunnerRegistry:
    def __init__(
        self,
        settings: Settings | None = None,
        model: BaseLlm | str | None = None,
        bundle: OkfBundle | None = None,
    ):
        settings = settings or get_settings()
        self.bundle = bundle or get_bundle()
        self._runners = {
            s.key: StructuredRunner(s, settings, model, self.bundle) for s in STRUCTURED_SPECS
        }

    def get(self, key: str) -> StructuredRunner:
        return self._runners[key]


_registry: RunnerRegistry | None = None


def get_registry() -> RunnerRegistry:
    global _registry
    if _registry is None:
        _registry = RunnerRegistry()
    return _registry


def set_registry(registry: RunnerRegistry | None) -> None:
    global _registry
    _registry = registry
