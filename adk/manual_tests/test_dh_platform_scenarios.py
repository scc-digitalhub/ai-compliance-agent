"""Opt-in scenarios against a real DH Core (and, for the coordinator one, the real LLM). Run from adk/ with:

    python -m pytest manual_tests/test_dh_platform_scenarios.py -q -s

DH Core connection: the digitalhub SDK reads DHCORE_* variables (adk/.env is loaded into the
environment first, e.g. DHCORE_ENDPOINT, DHCORE_USER, DHCORE_PASSWORD) or ~/.dhcore.ini.
Each test works on a throwaway project, deleted afterwards unless KEEP_DH_PROJECT=1.
The specifications must conform to the extension schemas registered in DH Core (checked first).
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid

import jsonschema
import pytest
import requests
from dotenv import load_dotenv

from compliance_adk.config import ADK_DIR, Settings

load_dotenv(ADK_DIR / ".env")

import digitalhub as sdk  # noqa: E402  (reads the DHCORE_* variables loaded above)
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from compliance_adk.agents.coordinator import build_coordinator_agent  # noqa: E402
from compliance_adk.agents.session_state import CONTEXT_KEY, PROJECT_KEY  # noqa: E402
from compliance_adk.contracts import (  # noqa: E402
    ComplianceContextOut,
    DataComplianceOut,
    ModelComplianceOut,
    ProjectComplianceSpec,
    ProjectInput,
)
from compliance_adk.dh import tools as dh  # noqa: E402
from compliance_adk.runtime import RunnerRegistry, set_registry  # noqa: E402

EXTENSION_KIND = "ai-compliance"  # project compliance extension kind registered in DH Core


def _compliance_extensions(project: str) -> list[dict]:
    """The project compliance extensions as stored on DH Core, read with a fresh SDK call."""
    return [e for e in sdk.get_project(project).extensions or [] if e.get("kind") == EXTENSION_KIND]


def _example_result(skill: str = "project-context") -> dict:
    path = Settings().skills_path / skill / "references" / "example.json"
    return json.loads(path.read_text())["result"]


def _example_project_spec() -> dict:
    project = ProjectInput(name="credit", domain="finance", ai_task="CLASSIFICATION", goal="Assess creditworthiness")
    spec = ProjectComplianceSpec.of(project, ComplianceContextOut.model_validate(_example_result()))
    return spec.model_dump(mode="json", exclude_none=True)


def _core_extension_schema(kind: str) -> dict:
    """The JSON schema DH Core validates the `kind` extension spec against."""
    from digitalhub.stores.client.factory import get_client

    config = get_client().get_credentials_and_config()
    token = config.get("DHCORE_ACCESS_TOKEN")
    response = requests.get(
        f"{config['DHCORE_ENDPOINT']}/api/v1/schemas/extension/{kind}",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        auth=None if token else (config.get("DHCORE_USER"), config.get("DHCORE_PASSWORD")),
        timeout=30,
    )
    if response.status_code == 404:
        pytest.fail(f"extension kind '{kind}' is not registered in DH Core")
    response.raise_for_status()
    return response.json()["schema"]


def _pruned_fields(spec, schema: dict, defs: dict, path: str = "") -> list[str]:
    """Spec fields DH Core drops because its schema does not declare them. Like Core, only inline
    `properties` are pruned; `$ref` subtrees are stored as sent."""
    if "$ref" in schema:
        return []
    if isinstance(spec, list):
        return [p for item in spec for p in _pruned_fields(item, schema.get("items", {}), defs, f"{path}[]")]
    if not isinstance(spec, dict) or "properties" not in schema:
        return []
    found = []
    for key, value in spec.items():
        if key not in schema["properties"]:
            found.append(f"{path}.{key}")
        else:
            found += _pruned_fields(value, schema["properties"][key], defs, f"{path}.{key}")
    return found


@pytest.mark.parametrize(
    "kind, spec",
    [
        ("ai-compliance", _example_project_spec),
        ("data-compliance", lambda: DataComplianceOut.model_validate(_example_result("dataset-analysis")).model_dump(mode="json", exclude_none=True)),
        ("model-compliance", lambda: ModelComplianceOut.model_validate(_example_result("model-analysis")).model_dump(mode="json", exclude_none=True)),
    ],
)
def test_specifications_conform_to_the_core_extension_schemas(kind, spec):
    try:
        schema = _core_extension_schema(kind)
    except requests.RequestException as exc:
        pytest.skip(f"DH Core not available: {exc}")
    data = spec()

    errors = [f"{list(e.absolute_path)}: {e.message[:200]}" for e in jsonschema.Draft202012Validator(schema).iter_errors(data)]
    pruned = _pruned_fields(data, schema, schema.get("$defs", {}))
    print(f"\n{kind}: {len(errors)} validation errors, fields dropped by DH Core: {sorted(set(pruned)) or 'none'}")

    assert errors == []


@pytest.fixture
def dh_project():
    name = f"compliance-manual-{uuid.uuid4().hex[:8]}"
    try:
        sdk.new_project(name, description="ai-compliance manual test (safe to delete)")
    except Exception as exc:  # no reachable / authorised DH Core
        pytest.skip(f"DH Core not available: {type(exc).__name__}: {exc}")
    print(f"\nDH project: {name}")
    yield name
    if os.getenv("KEEP_DH_PROJECT") != "1":
        sdk.delete_project(name, clean_context=True)


def test_sdk_round_trip_keeps_a_single_project_compliance_extension(dh_project):
    """Store, read back and replace the project specification through dh.tools and the SDK (no LLM)."""
    spec = _example_project_spec()

    dh.save_project_extension(dh_project, EXTENSION_KIND, spec)
    first = _compliance_extensions(dh_project)
    print("Stored extension:", {k: v for k, v in first[0].items() if k != "spec"} if first else None)

    assert len(first) == 1
    stored = ProjectComplianceSpec.model_validate(first[0]["spec"], extra="ignore")
    assert stored.goal == spec["goal"] and stored.domain.domain == "finance"
    assert stored.context.risk_classification.risk_level == spec["context"]["risk_classification"]["risk_level"]
    assert dh.get_project_extension(dh_project, EXTENSION_KIND) == first[0]["spec"]

    context = spec["context"]
    changed = {**spec, "context": {**context, "risk_classification": {**context["risk_classification"], "rationale": "Replaced."}}}
    dh.save_project_extension(dh_project, EXTENSION_KIND, changed)
    second = _compliance_extensions(dh_project)

    assert len(second) == 1  # replaced, not duplicated
    assert second[0]["spec"]["context"]["risk_classification"]["rationale"] == "Replaced."
    if first[0].get("id"):
        assert second[0].get("id") == first[0]["id"]


def _final_text(events) -> str:
    return "\n".join(p.text or "" for e in events if e.is_final_response() and e.content for p in e.content.parts)


def _calls(events) -> list[str]:
    return [p.function_call.name for e in events if e.content for p in e.content.parts if p.function_call]


def test_coordinator_generates_the_project_specification_and_stores_it_on_dh(dh_project):
    """Real LLM + real DH: the analysis finds nothing stored, generates the spec, then saves it via the SDK."""
    settings = Settings()
    for role in ("project_context", "coordinator"):
        settings.model_name_for(role)

    async def scenario():
        set_registry(RunnerRegistry(settings))
        sessions = InMemorySessionService()
        runner = Runner(agent=build_coordinator_agent(settings), app_name="dh_manual", session_service=sessions)
        session = await sessions.create_session(app_name="dh_manual", user_id="manual-check")

        async def turn(prompt: str):
            message = types.Content(role="user", parts=[types.Part(text=prompt)])
            events = [e async for e in runner.run_async(user_id="manual-check", session_id=session.id, new_message=message)]
            return _calls(events), _final_text(events)

        try:
            analyse_calls, analyse_reply = await turn(
                f"Analyse my project '{dh_project}' (use exactly this name): a finance credit scoring "
                "classification system in a pilot environment for EU loan officers and applicants. Goal: estimate "
                "creditworthiness for loan applications while supporting human review. Purpose: help officers "
                "prioritise applications; no automatic final decisions."
            )
            print("Analyse tools:", analyse_calls, "\nAnalyse reply:", analyse_reply[:800])
            state = (await sessions.get_session(app_name="dh_manual", user_id="manual-check", session_id=session.id)).state
            assert "analyze_project_context" in analyse_calls
            assert CONTEXT_KEY in state and PROJECT_KEY in state, "the project specification was not generated"
            generated = ProjectComplianceSpec.of(
                ProjectInput.model_validate(state[PROJECT_KEY]), ComplianceContextOut.model_validate(state[CONTEXT_KEY])
            )
            print("Generated project:", generated.model_dump(mode="json", exclude={"context"}, exclude_none=True))
            print("Generated risk level:", generated.context.risk_classification.risk_level)

            save_calls, save_reply = await turn(
                f"Save this project compliance specification on the DH platform for project '{dh_project}'."
            )
            print("Save tools:", save_calls, "\nSave reply:", save_reply[:800])
            assert "save_compliance_specification" in save_calls
            return generated
        finally:
            set_registry(None)

    generated = asyncio.run(scenario())

    stored = _compliance_extensions(dh_project)
    assert len(stored) == 1, f"expected one {EXTENSION_KIND} extension on DH, found {len(stored)}"
    print("Stored extension:", {k: v for k, v in stored[0].items() if k != "spec"})
    on_dh = ProjectComplianceSpec.model_validate(stored[0]["spec"], extra="ignore")
    assert on_dh.model_dump(exclude={"context"}) == generated.model_dump(exclude={"context"})
    assert on_dh.context.risk_classification == generated.context.risk_classification
    assert {r.id for r in on_dh.context.requirements} == {r.id for r in generated.context.requirements}
