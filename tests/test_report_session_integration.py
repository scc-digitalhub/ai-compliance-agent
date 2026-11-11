import json

from compliance_core.knowledge import get_bundle
from compliance_core.state import InMemoryStateStore, activate_project
from compliance_core.tools import ToolEnv


def report(summary):
    return {
        "kind": "TEST",
        "content": {"test": {"results": [], "verdict": "INCONCLUSIVE", "summary": summary}},
        "objectives": ["objective::one"],
    }


def test_recorded_report_can_be_prepared_for_save_without_rebuilding():
    from compliance_core.report_tools import prepare_compliance_report, record_compliance_report

    env = ToolEnv(state=InMemoryStateStore(), bundle=get_bundle())
    recorded = record_compliance_report(
        env, "model", "scorer", "run-one", report("Recorded evidence"), project="credit",
    )
    assert recorded["stored"] is True, recorded
    prepared = prepare_compliance_report(env.state, "model", "scorer", "run-one", project="credit")
    assert prepared["report"]["content"]["test"]["summary"] == "Recorded evidence"


def test_report_session_retrieval_cannot_mix_projects():
    from compliance_core.report_tools import get_session_compliance_reports, record_compliance_report

    env = ToolEnv(state=InMemoryStateStore(), bundle=get_bundle())
    activate_project(env.state, "credit")
    record_compliance_report(env, "model", "scorer", "run-one", report("Credit evidence"), project="credit")
    activate_project(env.state, "research")
    record_compliance_report(env, "model", "scorer", "run-one", report("Research evidence"), project="research")
    credit = json.dumps(get_session_compliance_reports(env, project="credit"))
    research = json.dumps(get_session_compliance_reports(env, project="research"))
    assert "Credit evidence" in credit and "Research evidence" not in credit
    assert "Research evidence" in research and "Credit evidence" not in research
