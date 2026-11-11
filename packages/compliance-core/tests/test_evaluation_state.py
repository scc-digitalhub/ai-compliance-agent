from compliance_core.state import (
    CODES_KEY, REPORTS_KEY, ComplianceWorkspace, InMemoryStateStore,
    activate_project, scoped_get, scoped_update,
)


def test_evaluation_artifacts_survive_switch_and_round_trip():
    state = InMemoryStateStore()
    activate_project(state, "credit")
    scoped_update(state, CODES_KEY, "code", {"source": "one"}, "credit")
    scoped_update(state, REPORTS_KEY, "report", {"kind": "TEST"}, "credit")
    activate_project(state, "other")
    assert scoped_get(state, CODES_KEY) == {}
    scoped_update(state, CODES_KEY, "code", {"source": "two"}, "other")
    activate_project(state, "credit")
    assert scoped_get(state, CODES_KEY)["code"]["source"] == "one"
    restored = InMemoryStateStore()
    ComplianceWorkspace.from_store(state).write_to(restored)
    assert scoped_get(restored, REPORTS_KEY)["report"]["kind"] == "TEST"
    assert scoped_get(restored, CODES_KEY, "other")["code"]["source"] == "two"


def test_old_workspaces_have_empty_evaluation_stores():
    state = InMemoryStateStore()
    ComplianceWorkspace.from_store({}).write_to(state)
    assert scoped_get(state, CODES_KEY) == scoped_get(state, REPORTS_KEY) == {}
