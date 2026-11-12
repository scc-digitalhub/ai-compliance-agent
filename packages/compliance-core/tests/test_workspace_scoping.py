# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import multiprocessing
from importlib.resources import files
from pathlib import Path

from compliance_core.analysis_tools import get_session_analyses
from compliance_core.host_tools import record_compliance_analysis as _record
from compliance_core.knowledge import get_bundle
from compliance_core.specification_tools import save_compliance_specification
from compliance_core.state import (
    ACTIVE_KEY,
    DATASETS_KEY,
    FileStateStore,
    InMemoryStateStore,
    WORKSPACES_KEY,
    activate_project,
    scoped_get,
)
from compliance_core.tools import ToolEnv


def example(skill: str) -> dict:
    return json.loads(files("compliance_skills").joinpath("skills", skill, "references", "example.json").read_text())


def project(name: str) -> dict:
    return {"name": name, "domain": "finance", "ai_task": "CLASSIFICATION", "goal": "Score loans"}


DATASET = {"dataset": {"name": "applications", "scope": "TRAINING"}}


class Specifications:
    def __init__(self):
        self.data: dict = {}

    def get(self, kind, entity, project=None):
        return self.data.get((kind, entity, project), {})

    def save(self, kind, entity, specification, project=None):
        self.data[(kind, entity, project)] = specification


GROUNDING = ["catalog/requirements/eu-ai-act/art14-human-oversight.md"]


def record_compliance_analysis(tools, kind, request, output):
    result = _record(tools, kind, request, output, grounding=GROUNDING)
    assert result["stored"], result
    return result


def env(state=None) -> ToolEnv:
    return ToolEnv(state=state if state is not None else InMemoryStateStore(), bundle=get_bundle(),
                   specifications=Specifications())


def test_analyses_of_one_project_do_not_leak_into_another():
    tools = env()
    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))
    record_compliance_analysis(tools, "dataset", DATASET, example("dataset-analysis"))
    record_compliance_analysis(tools, "project", project("research"), example("project-context"))

    research = get_session_analyses(tools)
    assert research["active_project"] == "research"
    assert research["datasets"] == {}
    assert set(research["projects"]) == {"credit", "research"}
    assert set(get_session_analyses(tools, "credit")["datasets"]) == {"applications"}

    out = save_compliance_specification(tools, "dataset", "applications", project="research")
    assert out["code"] == "not_found"
    assert tools.specifications.data == {}


def test_switching_back_restores_a_project_and_saves_from_its_scope():
    tools = env()
    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))
    record_compliance_analysis(tools, "dataset", DATASET, example("dataset-analysis"))
    record_compliance_analysis(tools, "project", project("research"), example("project-context"))

    saved = save_compliance_specification(tools, "dataset", "applications", project="credit")
    assert saved["saved"] is True and ("dataset", "applications", "credit") in tools.specifications.data

    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))
    assert set(get_session_analyses(tools)["datasets"]) == {"applications"}
    assert set(tools.state[WORKSPACES_KEY]) == {"research"}


def test_entity_analysis_for_an_inactive_project_is_stored_in_that_project():
    tools = env()
    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))
    record_compliance_analysis(
        tools, "dataset", {**DATASET, "project": project("research")}, example("dataset-analysis"),
    )

    assert get_session_analyses(tools)["datasets"] == {}
    assert set(scoped_get(tools.state, DATASETS_KEY, "research")) == {"applications"}
    assert tools.state[ACTIVE_KEY] == "credit"


def test_analyses_recorded_before_a_project_is_selected_are_adopted():
    tools = env()
    record_compliance_analysis(tools, "dataset", DATASET, example("dataset-analysis"))
    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))

    analyses = get_session_analyses(tools)
    assert analyses["active_project"] == "credit"
    assert set(analyses["datasets"]) == {"applications"}
    assert analyses["provenance"]["dataset:applications"]["mode"] == "host"


def test_legacy_flat_state_keeps_working_as_the_active_project():
    state = InMemoryStateStore({"analysis_project": project("credit"), DATASETS_KEY: {"old": {"scope": "TRAINING"}}})
    activate_project(state, "research")
    assert scoped_get(state, DATASETS_KEY) == {}
    assert scoped_get(state, DATASETS_KEY, "credit") == {"old": {"scope": "TRAINING"}}


def test_file_state_transaction_is_atomic_and_rolled_back_on_error(tmp_path: Path):
    store = FileStateStore(tmp_path)
    with store.transaction():
        store["a"] = 1
        store["b"] = 2
        assert not (tmp_path / "state.json").exists()  # written once, at the end
    assert FileStateStore(tmp_path).snapshot() == {"a": 1, "b": 2}

    try:
        with store.transaction():
            store["a"] = 99
            raise RuntimeError("tool failed")
    except RuntimeError:
        pass
    assert FileStateStore(tmp_path).snapshot() == {"a": 1, "b": 2}


def _increment(directory: str, times: int) -> None:
    store = FileStateStore(directory)
    for _ in range(times):
        with store.transaction():
            store["count"] = store.get("count", 0) + 1


def test_file_state_store_serializes_updates_from_several_processes(tmp_path: Path):
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=_increment, args=(str(tmp_path), 25)) for _ in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(60)
        assert worker.exitcode == 0
    assert FileStateStore(tmp_path)["count"] == 100


def test_delegated_entity_analysis_keeps_the_project_active_when_it_started():
    import asyncio

    from compliance_core.analysis_tools import analyze_dataset
    from compliance_core.analysis_engine import DATASET, AnalysisTrace, build_response

    class SwitchingEngine:
        """Another tool call selects a different project while the model is running."""

        def __init__(self, tools):
            self.tools = tools

        async def run(self, analysis, request, request_id=None):
            record_compliance_analysis(self.tools, "project", project("research"), example("project-context"))
            output = DATASET.output_model.model_validate(example("dataset-analysis"))
            return build_response(DATASET, output, [], AnalysisTrace(), request_id="r", model="m",
                                  bundle=get_bundle(), latency_ms=1)

    tools = env()
    tools.analysis_engine = SwitchingEngine(tools)
    record_compliance_analysis(tools, "project", project("credit"), example("project-context"))
    asyncio.run(analyze_dataset(tools, DATASET_INPUT, rerun=True))

    assert get_session_analyses(tools)["active_project"] == "research"
    assert get_session_analyses(tools)["datasets"] == {}
    assert set(get_session_analyses(tools, "credit")["datasets"]) == {"applications"}


DATASET_INPUT = {"name": "applications", "scope": "TRAINING"}
