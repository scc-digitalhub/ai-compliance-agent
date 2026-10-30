from __future__ import annotations

import asyncio
import time
import json

import pytest
from google.adk.events import Event, EventActions

from compliance_protocols.config import ProtocolSettings
from compliance_protocols.runtime import PENDING
from compliance_skills import SKILLS_PATH
from compliance_core.contracts import ModelComplianceOut

from protocol_test_support import GET_ENTITY, LOAD_ENTITY, LOAD_SPECS, SAVE, noop


def test_durable_history_and_explicit_project_policy(runtime_factory, monkeypatch):
    monkeypatch.setenv("DH_PROJECT", "credit")

    async def scenario():
        missing = {**GET_ENTITY, "args": {"kind": "model", "entity": "scorer"}}
        runtime = runtime_factory([LOAD_ENTITY, missing, "Which project?", GET_ENTITY, "Found it."])
        session_id = await runtime.create()
        try:
            first = await runtime.prompt(session_id, "Get scorer", noop)
            assert first.status == "input_required"
            assert runtime.entities.calls == []
            second = await runtime.prompt(session_id, "In credit", noop)
            assert second.status == "completed"
            assert runtime.entities.calls == [("model", "scorer", "credit")]
        finally:
            await runtime.close()
        restored = runtime_factory(["Continued."])
        try:
            history = await restored.history(session_id)
            assert any(item["text"] == "In credit" for item in history)
            assert (await restored.get(session_id)).state["protocol_project"] == "credit"
            assert (await restored.prompt(session_id, "Continue", noop)).text == "Continued."
        finally:
            await restored.close()
    asyncio.run(scenario())


def test_sessions_isolate_state_and_project_switch_is_rejected(runtime_factory):
    async def scenario():
        switch = {**GET_ENTITY, "args": {**GET_ENTITY["args"], "project": "other"}}
        runtime = runtime_factory([LOAD_ENTITY, GET_ENTITY, "Found.", switch, "Start a new session."])
        try:
            first, second = await runtime.create(), await runtime.create()
            await runtime.prompt(first, "Get scorer in credit", noop)
            assert "dh_entities" not in (await runtime.get(second)).state
            result = await runtime.prompt(first, "Get scorer in other", noop)
            assert result.status == "input_required"
            assert runtime.entities.calls == [("model", "scorer", "credit")]
        finally:
            await runtime.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("project", ["credit", "research", "previously-unlisted"])
def test_explicit_project_access_is_delegated_to_repository(runtime_factory, project):
    async def scenario():
        lookup = {**GET_ENTITY, "args": {**GET_ENTITY["args"], "project": project}}
        runtime = runtime_factory([LOAD_ENTITY, lookup, "Found it."])
        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, f"Get scorer in {project}", noop)
            assert result.status == "completed"
            assert runtime.entities.calls == [("model", "scorer", project)]
            assert (await runtime.get(session_id)).state["protocol_project"] == project
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_digitalhub_access_denial_is_reported(runtime_factory, monkeypatch):
    async def scenario():
        runtime = runtime_factory([LOAD_ENTITY, GET_ENTITY, "Access denied."])

        def denied(kind, entity, project=None):
            raise PermissionError("DigitalHub denied access to this project")

        monkeypatch.setattr(runtime.entities, "get", denied)
        try:
            session_id = await runtime.create()
            updates = []

            async def notify(event):
                updates.append(event)

            result = await runtime.prompt(session_id, "Get scorer in credit", notify)
            assert result.status == "failed"
            assert any(
                event.get("result", {}).get("code") == "dh_error"
                and "DigitalHub denied access" in event["result"]["error"]
                for event in updates if event["type"] == "tool_end"
            )
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_removed_project_allowlist_environment_is_ignored(monkeypatch):
    monkeypatch.setenv("COMPLIANCE_PROTOCOL_ALLOWED_PROJECTS", "obsolete-not-json")
    assert "allowed_projects" not in ProtocolSettings.model_fields
    assert "allowed_projects" not in ProtocolSettings().model_dump()


def test_approved_write_to_previously_unlisted_project(runtime_factory):
    async def scenario():
        save = {**SAVE, "args": {**SAVE["args"], "project": "research"}}
        runtime = runtime_factory([LOAD_SPECS, save, "Approve?"], allow_writes=True)
        try:
            session_id = await runtime.create()
            pending = await runtime.prompt(session_id, "Save scorer in research", noop)
            assert pending.status == "input_required"
            assert pending.approval["operation"]["project"] == "research"
            assert runtime.specifications.data == {}
            result = await runtime.prompt(
                session_id, "", noop, approval_id=pending.approval["id"], approve=True,
            )
            assert result.status == "completed"
            assert runtime.specifications.data == {("model", "scorer", "research"): {"objectives": []}}
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_writes_are_disabled_by_default(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD_SPECS, SAVE, "Writes disabled."])
        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, "Save this", noop)
            assert result.status == "failed"
            assert runtime.specifications.data == {}
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_write_approval_is_bound_to_session_payload_and_consumed_once(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD_SPECS, SAVE, "Please approve the write."], allow_writes=True)
        try:
            session_id = await runtime.create()
            other = await runtime.create()
            result = await runtime.prompt(session_id, "Save model scorer in credit", noop)
            assert result.status == "input_required"
            assert runtime.specifications.data == {}
            approval = result.approval
            assert approval["operation"]["project"] == "credit"
            bad = await runtime.prompt(other, "", noop, approval_id=approval["id"], approve=True)
            assert bad.status == "failed"
            invalid = await runtime.prompt(session_id, "", noop, approval_id=approval["id"], approve="true")
            assert invalid.status == "failed"
            saved = await runtime.prompt(session_id, "", noop, approval_id=approval["id"], approve=True)
            assert saved.status == "completed"
            assert runtime.specifications.data == {("model", "scorer", "credit"): {"objectives": []}}
            repeated = await runtime.prompt(session_id, "", noop, approval_id=approval["id"], approve=True)
            assert repeated.status == "failed"
            assert sum(call[0] == "save" for call in runtime.specifications.calls) == 1
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_rejected_and_expired_approvals_do_not_write(runtime_factory):
    async def scenario():
        runtime = runtime_factory(
            [LOAD_SPECS, SAVE, "Approve?", SAVE, "Approve again?"], allow_writes=True,
        )
        try:
            session_id = await runtime.create()
            first = await runtime.prompt(session_id, "Save", noop)
            rejected = await runtime.prompt(session_id, "", noop, approval_id=first.approval["id"], approve=False)
            assert rejected.status == "completed"
            second = await runtime.prompt(session_id, "Save again", noop)
            session = await runtime.get(session_id)
            pending = dict(second.approval, expires_at=time.time() - 1)
            await runtime.sessions.append_event(session, Event(
                author=runtime.agent.name, actions=EventActions(state_delta={PENDING: pending}),
            ))
            result = await runtime.prompt(session_id, "", noop, approval_id=pending["id"], approve=True)
            assert result.status == "failed"
            assert runtime.specifications.data == {}
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_transport_permission_is_once_per_write(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD_SPECS, SAVE, "Saved."], allow_writes=True)
        approvals = []

        async def permit(operation):
            approvals.append(operation)
            return True

        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, "Save scorer in credit", noop, permission=permit)
            assert result.status == "completed"
            assert len(approvals) == 1
            assert runtime.specifications.data
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_clarification_tool_sets_input_required(runtime_factory):
    async def scenario():
        runtime = runtime_factory([
            {"call": "request_user_input", "args": {"question": "What is the dataset scope?"}},
            "What is the dataset scope?",
        ])
        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, "Analyze a dataset", noop)
            assert result.status == "input_required"
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_cancellation_and_timeout(runtime_factory):
    async def scenario():
        runtime = runtime_factory(["Slow result"], timeout_s=0.1)
        runtime.agent.model.delay = 1
        try:
            session_id = await runtime.create()
            task = asyncio.create_task(runtime.prompt(session_id, "Wait", noop))
            await asyncio.sleep(0.03)
            await runtime.cancel(session_id)
            assert (await task).status == "cancelled"
            assert (await runtime.prompt(session_id, "Wait again", noop)).status == "failed"
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_recorded_results_are_validated_structured_artifacts(runtime_factory):
    async def scenario():
        example = json.loads((SKILLS_PATH / "model-analysis/references/example.json").read_text())
        runtime = runtime_factory([
            {"call": "load_skill", "args": {"skill_name": "model-analysis"}},
            {"call": "record_compliance_analysis", "args": {
                "kind": "model", "request": {"model": {"name": "scorer", "ai_task": "CLASSIFICATION"}},
                "output": example,
            }},
            "The validated assessment is ready.",
        ])
        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, "Assess scorer", noop)
            assert result.status == "completed"
            assert len(result.artifacts) == 1
            assert result.artifacts[0]["stored"] and result.artifacts[0]["valid"]
            assert result.artifacts[0]["normalized"]["result"] == ModelComplianceOut.model_validate(
                example["result"]
            ).model_dump(mode="json")
            assert result.artifacts[0]["meta"]["okf_version"]
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_framework_knowledge_tools_return_text_and_grounding(runtime_factory):
    async def scenario():
        runtime = runtime_factory([
            {"call": "load_skill", "args": {"skill_name": "compliance-framework"}},
            {"call": "list_all_concepts", "args": {}},
            {"call": "read_okf_concept", "args": {"path": "data/DataGovernance.md"}},
            "Grounded explanation.",
        ])
        try:
            session_id = await runtime.create()
            result = await runtime.prompt(session_id, "Explain data governance", noop)
            assert result.status == "completed"
            assert result.text == "Grounded explanation."
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_concurrent_turns_in_same_session_are_rejected(runtime_factory):
    async def scenario():
        runtime = runtime_factory(["Done."])
        runtime.agent.model.delay = 0.1
        try:
            session_id = await runtime.create()
            task = asyncio.create_task(runtime.prompt(session_id, "First", noop))
            await asyncio.sleep(0.02)
            try:
                await runtime.prompt(session_id, "Second", noop)
            except ValueError as exc:
                assert "already running" in str(exc)
            else:
                raise AssertionError("Concurrent turn was accepted")
            assert (await task).status == "completed"
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_pending_write_approval_survives_restart(runtime_factory):
    async def scenario():
        first = runtime_factory([LOAD_SPECS, SAVE, "Approve?"], allow_writes=True)
        session_id = await first.create()
        try:
            result = await first.prompt(session_id, "Save scorer in credit", noop)
            approval_id = result.approval["id"]
        finally:
            await first.close()
        restored = runtime_factory([], allow_writes=True)
        try:
            result = await restored.prompt(session_id, "", noop, approval_id=approval_id, approve=True)
            assert result.status == "completed"
            assert restored.specifications.data == {("model", "scorer", "credit"): {"objectives": []}}
        finally:
            await restored.close()
    asyncio.run(scenario())
