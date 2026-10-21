"""Shared fixtures: a scripted LLM so agents, runners and the API run without a provider."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.models._capabilities import LlmCapabilities
from google.genai import types

ADK_DIR = Path(__file__).resolve().parents[1]
if str(ADK_DIR) not in sys.path:
    sys.path.insert(0, str(ADK_DIR))

from compliance_adk.config import Settings  # noqa: E402
from compliance_adk.knowledge import get_bundle  # noqa: E402
from compliance_adk.runtime import RunnerRegistry, set_registry  # noqa: E402

SKILLS = ADK_DIR / "compliance_adk" / "skills"


def example(skill: str) -> dict[str, Any]:
    return json.loads((SKILLS / skill / "references" / "example.json").read_text())


class ScriptedLlm(BaseLlm):
    """Plays back a script. Items: a JSON-able object/str (final answer), or {"call": name, "args": {...}}."""

    model: str = "scripted"
    script: list[Any] = []
    seen_messages: list[str] = []
    fail_with: Any = None

    @property
    def capabilities(self) -> LlmCapabilities:
        return LlmCapabilities(output_schema_and_tools=True)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        if self.fail_with is not None:
            raise self.fail_with
        last_user = next(
            (c for c in reversed(llm_request.contents) if c.role == "user" and c.parts and c.parts[0].text),
            None,
        )
        if last_user:
            self.seen_messages.append(last_user.parts[0].text)
        item = self.script.pop(0)
        if isinstance(item, dict) and "call" in item:
            part = types.Part(function_call=types.FunctionCall(name=item["call"], args=item.get("args", {})))
        else:
            part = types.Part(text=item if isinstance(item, str) else json.dumps(item))
        yield LlmResponse(
            content=types.Content(role="model", parts=[part]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=10, candidates_token_count=5),
        )


@pytest.fixture
def settings() -> Settings:
    return Settings(structured_model="scripted", coordinator_model="scripted", max_validation_retries=1)


@pytest.fixture
def bundle():
    return get_bundle()


@pytest.fixture
def make_registry(settings):
    """Build a registry whose agents share one scripted LLM; registers it process-wide."""

    def _make(*script: Any) -> tuple[RunnerRegistry, ScriptedLlm]:
        llm = ScriptedLlm(script=list(script), seen_messages=[])
        registry = RunnerRegistry(settings, model=llm)
        set_registry(registry)
        return registry, llm

    yield _make
    set_registry(None)


PROJECT = {
    "name": "Credit scoring",
    "domain": "finance",
    "ai_task": "CLASSIFICATION",
    "goal": "Assess creditworthiness of loan applicants",
}
DATASET = {"name": "Applications 2024", "scope": "TRAINING", "sensitivity": "PII", "known_protected_attributes": ["age"]}
MODEL = {"name": "Credit model", "ai_task": "CLASSIFICATION", "output_type": "BINARY_CLASSIFICATION"}
