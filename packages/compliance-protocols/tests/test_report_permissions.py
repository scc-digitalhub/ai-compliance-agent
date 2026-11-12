# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from copy import deepcopy

import pytest

from compliance_protocols.runtime import CURRENT, ScopedReports, Turn, _digest
from protocol_test_support import noop


REPORT = {
    "kind": "TEST",
    "content": {"test": {"results": [], "verdict": "INCONCLUSIVE", "summary": "Insufficient evidence"}},
    "objectives": ["objective::one"],
}
SAVE = {
    "call": "save_compliance_report",
    "args": {
        "kind": "model", "entity": "scorer", "project": "credit",
        "name": "validation-one", "report": REPORT,
    },
}
LOAD = {"call": "load_skill", "args": {"skill_name": "compliance-report"}}


class Reports:
    supports_atomic_batch = False

    def __init__(self):
        self.data = {}

    def get(self, kind, entity, name, project=None):
        return deepcopy(self.data.get((kind, entity, name, project), {}))

    def save(self, kind, entity, name, report, project=None):
        self.data[(kind, entity, name, project)] = deepcopy(report)


def test_report_write_requires_exact_approval_and_consumes_it(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD, deepcopy(SAVE), "Approve report?"], allow_writes=True)
        runtime.reports = Reports()
        try:
            session = await runtime.create()
            pending = await runtime.prompt(session, "Attach report in credit", noop)
            assert pending.status == "input_required", pending.text
            assert runtime.reports.data == {}
            assert pending.approval["operation"]["name"] == "validation-one"
            approved = await runtime.prompt(
                session, "", noop, approval_id=pending.approval["id"], approve=True,
            )
            assert approved.status == "completed", approved.text
            saved = runtime.reports.data[("model", "scorer", "validation-one", "credit")]
            assert saved["kind"] == "TEST"
            replay = await runtime.prompt(session, "", noop, approval_id=pending.approval["id"], approve=True)
            assert replay.status == "failed"
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_report_write_disabled_and_denial_do_not_publish(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD, deepcopy(SAVE), "Disabled"])
        runtime.reports = Reports()
        try:
            session = await runtime.create()
            result = await runtime.prompt(session, "Save report", noop)
            assert result.status == "failed"
            assert runtime.reports.data == {}
        finally:
            await runtime.close()
        runtime = runtime_factory([LOAD, deepcopy(SAVE), "Approve?"], allow_writes=True)
        runtime.reports = Reports()
        try:
            session = await runtime.create()
            result = await runtime.prompt(session, "Save report", noop)
            denied = await runtime.prompt(session, "", noop, approval_id=result.approval["id"], approve=False)
            assert denied.status == "completed"
            assert runtime.reports.data == {}
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_repository_boundary_rejects_tampered_payload_and_name():
    class Policy:
        settings = type("Settings", (), {"allow_writes": True})()

        def resolve(self, kind, entity, project):
            return project

    repository = Reports()
    scoped = ScopedReports(Policy(), repository)
    operation = {**SAVE["args"], "overwrite": False}
    turn = Turn(notify=noop, authorized_write=_digest(operation))
    token = CURRENT.set(turn)
    try:
        with pytest.raises(PermissionError, match="exact report"):
            scoped.save("model", "scorer", "other-name", REPORT, "credit")
        changed = deepcopy(REPORT)
        changed["content"]["test"]["verdict"] = "PASS"
        with pytest.raises(PermissionError, match="exact report"):
            scoped.save("model", "scorer", "validation-one", changed, "credit")
        scoped.save("model", "scorer", "validation-one", REPORT, "credit")
        with pytest.raises(PermissionError):
            scoped.save("model", "scorer", "validation-one", REPORT, "credit")
        assert len(repository.data) == 1
    finally:
        CURRENT.reset(token)
