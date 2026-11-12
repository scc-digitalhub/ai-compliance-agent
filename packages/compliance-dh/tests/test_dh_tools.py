# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from types import SimpleNamespace

import pytest
from digitalhub.utils.exceptions import BackendError, EntityNotExistsError

from compliance_dh import tools
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository
from compliance_core.entity_tools import get_entity_details
from compliance_core.knowledge import get_bundle
from compliance_core.specification_tools import get_compliance_specification, save_compliance_specification
from compliance_core.state import InMemoryStateStore, PROJECT_KEY
from compliance_core.tools import ToolEnv


class FakeEntity:
    def __init__(self, name: str, kind: str, extensions: list[dict] | None = None, **extra):
        self.name, self.kind, self.extensions, self.extra = name, kind, extensions, extra

    def to_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "extensions": self.extensions, **self.extra}


@pytest.fixture
def sdk(monkeypatch):
    """Stand-in for the digitalhub SDK; stores entities by (type, project, name) and records calls."""
    store: dict[tuple[str, str | None, str], FakeEntity] = {}
    calls: list[tuple] = []

    def getter(entity_type):
        def get(identifier, project=None):
            calls.append((f"get_{entity_type}", identifier, project))
            if identifier.startswith("store://"):
                project, name = identifier.split("/")[2], identifier.rsplit("/", 1)[-1]
            else:
                name = identifier
            try:
                return store[(entity_type, project, name)]
            except KeyError:
                raise EntityNotExistsError(f"{entity_type} {identifier} not found") from None

        return get

    def updater(entity_type):
        def update(entity):
            calls.append((f"update_{entity_type}", entity.name, [dict(e) for e in entity.extensions]))
            return entity

        return update

    def get_project(name):
        calls.append(("get_project", name))
        try:
            return store[("project", None, name)]
        except KeyError:
            raise EntityNotExistsError(f"project {name} not found") from None

    fake = SimpleNamespace(
        get_dataitem=getter("dataitem"),
        update_dataitem=updater("dataitem"),
        get_model=getter("model"),
        update_model=updater("model"),
        get_project=get_project,
        update_project=updater("project"),
    )
    monkeypatch.setattr(tools, "sdk", fake)
    return SimpleNamespace(store=store, calls=calls)


def ext(kind: str, spec: dict, id: str | None = None) -> dict:
    return {"kind": kind, "name": kind, "spec": spec, **({"id": id} if id else {})}


def test_get_entity_returns_the_dataitem_or_model_details(sdk):
    sdk.store[("dataitem", "credit", "applications")] = FakeEntity("applications", "table", spec={"path": "s3://x"})
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn")

    dataset = tools.get_entity("applications", "dataset", project="credit")
    model = tools.get_entity("scorer", "model", project="credit")

    assert dataset == {"name": "applications", "kind": "table", "extensions": None, "spec": {"path": "s3://x"}}
    assert model["kind"] == "sklearn"
    assert ("get_dataitem", "applications", "credit") in sdk.calls
    assert ("get_model", "scorer", "credit") in sdk.calls


def test_get_entity_accepts_a_store_key_and_reports_missing_entities_as_empty(sdk):
    sdk.store[("model", "other", "scorer")] = FakeEntity("scorer", "sklearn")

    assert tools.get_entity("store://other/model/sklearn/scorer", "model")["name"] == "scorer"
    assert ("get_model", "store://other/model/sklearn/scorer", None) in sdk.calls
    assert tools.get_entity("missing", "dataset", project="credit") == {}


@pytest.mark.parametrize("variable", ["DH_PROJECT", "PROJECT_NAME"])
def test_entity_names_need_an_explicit_project_even_when_environment_is_set(sdk, monkeypatch, variable):
    monkeypatch.setenv(variable, "credit")
    with pytest.raises(ValueError, match="Specify the DigitalHub project"):
        tools.get_entity("applications", "dataset")
    assert sdk.calls == []


def test_unsupported_entity_kind_is_rejected(sdk):
    with pytest.raises(ValueError, match="Unsupported entity kind"):
        tools.get_entity("x", "function")


def test_backend_failures_other_than_not_found_propagate(sdk):
    def broken(identifier, project=None):
        raise BackendError("unreachable")

    tools.sdk.get_dataitem = broken
    with pytest.raises(BackendError):
        tools.get_entity("applications", "dataset", project="credit")


def test_get_extension_returns_the_spec_of_the_extension_of_that_kind(sdk):
    sdk.store[("dataitem", "credit", "applications")] = FakeEntity(
        "applications", "table", [ext("quality", {"q": 1}), ext("data-compliance", {"scope": "TRAINING"}, id="e1")]
    )
    sdk.store[("project", None, "credit")] = FakeEntity("credit", "project", [ext("ai-compliance", {"r": "HIGH"})])

    assert tools.get_entity_extension("applications", "dataset", "data-compliance", project="credit") == {"scope": "TRAINING"}
    assert tools.get_project_extension("credit", "ai-compliance") == {"r": "HIGH"}


def test_get_extension_is_empty_without_extension_or_entity(sdk):
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn", None)
    sdk.store[("project", None, "credit")] = FakeEntity("credit", "project", [ext("other", {})])

    assert tools.get_entity_extension("scorer", "model", "model-compliance", project="credit") == {}
    assert tools.get_entity_extension("missing", "model", "model-compliance", project="credit") == {}
    assert tools.get_project_extension("credit", "ai-compliance") == {}
    assert tools.get_project_extension("missing", "ai-compliance") == {}


def test_save_adds_the_extension_and_keeps_the_others(sdk):
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn", [ext("quality", {"q": 1}, id="e0")])

    tools.save_entity_extension("scorer", "model", "model-compliance", {"objectives": []}, project="credit")

    (_, name, sent) = sdk.calls[-1]
    assert sdk.calls[-1][0] == "update_model" and name == "scorer"
    assert sent == [ext("quality", {"q": 1}, id="e0"), ext("model-compliance", {"objectives": []})]


def test_save_replaces_the_single_extension_of_that_kind_keeping_its_identity(sdk):
    sdk.store[("dataitem", "credit", "applications")] = FakeEntity(
        "applications",
        "table",
        [
            ext("data-compliance", {"old": True}, id="e1"),
            ext("quality", {"q": 1}, id="e2"),
            ext("data-compliance", {"duplicate": True}, id="e3"),
        ],
    )

    tools.save_entity_extension("applications", "dataset", "data-compliance", {"new": True}, project="credit")

    sent = sdk.calls[-1][2]
    compliance = [e for e in sent if e["kind"] == "data-compliance"]
    assert compliance == [ext("data-compliance", {"new": True}, id="e1")]  # one, same id, new spec
    assert ext("quality", {"q": 1}, id="e2") in sent


def test_save_project_extension_updates_the_project(sdk):
    sdk.store[("project", None, "credit")] = FakeEntity("credit", "project", [])

    tools.save_project_extension("credit", "ai-compliance", {"r": "HIGH"})

    assert sdk.calls[-1] == ("update_project", "credit", [ext("ai-compliance", {"r": "HIGH"})])
    assert tools.get_project_extension("credit", "ai-compliance") == {"r": "HIGH"}  # read back


def test_save_on_a_missing_entity_raises(sdk):
    with pytest.raises(EntityNotExistsError):
        tools.save_entity_extension("missing", "dataset", "data-compliance", {}, project="credit")
    with pytest.raises(EntityNotExistsError):
        tools.save_project_extension("missing", "ai-compliance", {})


@pytest.mark.parametrize("project", [None, "", "   "])
def test_extension_operations_reject_missing_projects_without_sdk_calls(sdk, monkeypatch, project):
    monkeypatch.setenv("DH_PROJECT", "credit")
    with pytest.raises(ValueError, match="Specify the DigitalHub project"):
        tools.get_entity_extension("scorer", "model", "model-compliance", project=project)
    with pytest.raises(ValueError, match="Specify the DigitalHub project"):
        tools.save_entity_extension("scorer", "model", "model-compliance", {}, project=project)
    assert sdk.calls == []


def tool_env():
    return ToolEnv(
        state=InMemoryStateStore(),
        bundle=get_bundle(),
        entities=DhEntityCatalog(),
        specifications=DhSpecificationRepository(),
    )


def test_core_operations_require_user_project_and_ignore_environment(sdk, monkeypatch):
    monkeypatch.setenv("DH_PROJECT", "credit")
    monkeypatch.setenv("PROJECT_NAME", "credit")
    env = tool_env()

    assert get_entity_details(env, "model", "scorer")["code"] == "missing_project"
    assert get_compliance_specification(env, "model", "scorer")["code"] == "missing_project"
    assert save_compliance_specification(
        env, "model", "scorer", specification={"objectives": []}
    )["code"] == "missing_project"
    assert sdk.calls == []
    assert dict(env.state) == {}


def test_explicit_project_routes_details_reads_and_writes_without_environment_fallback(sdk, monkeypatch):
    monkeypatch.setenv("DH_PROJECT", "wrong")
    for project in ("credit", "other"):
        sdk.store[("model", project, "scorer")] = FakeEntity(
            "scorer", "sklearn",
            [ext("model-compliance", {"objectives": []}), ext("quality", {"project": project})],
            project=project,
        )
    env = tool_env()
    env.state[PROJECT_KEY] = {"name": "other"}

    details = get_entity_details(env, "model", "scorer", project="credit")
    assert details["details"]["project"] == "credit"
    assert get_compliance_specification(env, "model", "scorer", project="credit")["specification"] == {"objectives": []}
    assert save_compliance_specification(
        env, "model", "scorer", specification={"objectives": []}, project="credit"
    )["saved"]
    assert ("get_model", "scorer", "credit") in sdk.calls
    assert not any(call[0] == "get_model" and call[2] != "credit" for call in sdk.calls)
    assert sdk.store[("model", "credit", "scorer")].extensions[0] == ext("quality", {"project": "credit"})


def test_entity_cache_is_scoped_to_the_user_project(sdk):
    for project in ("credit", "other"):
        sdk.store[("model", project, "scorer")] = FakeEntity("scorer", "sklearn", project=project)
    env = tool_env()
    first = get_entity_details(env, "model", "scorer", project="credit")
    second = get_entity_details(env, "model", "scorer", project="other")
    assert first["details"]["project"] == "credit"
    assert second["details"]["project"] == "other"
    assert second["source"] == "dh"
    assert get_entity_details(env, "model", "scorer", project="credit")["source"] == "session"
    env.state[PROJECT_KEY] = {"name": "other"}
    assert get_entity_details(env, "model", "scorer")["details"]["project"] == "other"
    assert len(sdk.calls) == 2


def test_core_accepts_explicit_store_keys_without_a_default_project(sdk):
    sdk.store[("model", "other", "scorer")] = FakeEntity(
        "scorer", "sklearn", [ext("model-compliance", {"objectives": []})]
    )
    env = tool_env()
    key = "store://other/model/sklearn/scorer"
    assert get_entity_details(env, "model", key)["details"]["name"] == "scorer"
    assert "specification" in get_compliance_specification(env, "model", key)
    assert save_compliance_specification(env, "model", key, specification={"objectives": []})["saved"]
    assert all(call[2] is None for call in sdk.calls if call[0] == "get_model")
