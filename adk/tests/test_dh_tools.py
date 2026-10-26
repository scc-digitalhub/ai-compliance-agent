from __future__ import annotations

from types import SimpleNamespace

import pytest
from digitalhub.utils.exceptions import BackendError, EntityNotExistsError

from compliance_adk.config import Settings
from compliance_adk.dh import tools


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
    monkeypatch.setattr(tools, "get_settings", lambda: Settings(dh_project="credit"))
    return SimpleNamespace(store=store, calls=calls)


def ext(kind: str, spec: dict, id: str | None = None) -> dict:
    return {"kind": kind, "name": kind, "spec": spec, **({"id": id} if id else {})}


def test_get_entity_returns_the_dataitem_or_model_details(sdk):
    sdk.store[("dataitem", "credit", "applications")] = FakeEntity("applications", "table", spec={"path": "s3://x"})
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn")

    dataset = tools.get_entity("applications", "dataset")
    model = tools.get_entity("scorer", "model")

    assert dataset == {"name": "applications", "kind": "table", "extensions": None, "spec": {"path": "s3://x"}}
    assert model["kind"] == "sklearn"
    assert ("get_dataitem", "applications", "credit") in sdk.calls  # name resolved in DH_PROJECT
    assert ("get_model", "scorer", "credit") in sdk.calls


def test_get_entity_accepts_a_store_key_and_reports_missing_entities_as_empty(sdk):
    sdk.store[("model", "other", "scorer")] = FakeEntity("scorer", "sklearn")

    assert tools.get_entity("store://other/model/sklearn/scorer", "model")["name"] == "scorer"
    assert ("get_model", "store://other/model/sklearn/scorer", None) in sdk.calls
    assert tools.get_entity("missing", "dataset") == {}


def test_entity_names_need_a_configured_project(sdk, monkeypatch):
    monkeypatch.setattr(tools, "get_settings", lambda: Settings(dh_project=None))
    with pytest.raises(ValueError, match="DH_PROJECT"):
        tools.get_entity("applications", "dataset")


def test_unsupported_entity_kind_is_rejected(sdk):
    with pytest.raises(ValueError, match="Unsupported entity kind"):
        tools.get_entity("x", "function")


def test_backend_failures_other_than_not_found_propagate(sdk):
    def broken(identifier, project=None):
        raise BackendError("unreachable")

    tools.sdk.get_dataitem = broken
    with pytest.raises(BackendError):
        tools.get_entity("applications", "dataset")


def test_get_extension_returns_the_spec_of_the_extension_of_that_kind(sdk):
    sdk.store[("dataitem", "credit", "applications")] = FakeEntity(
        "applications", "table", [ext("quality", {"q": 1}), ext("data-compliance", {"scope": "TRAINING"}, id="e1")]
    )
    sdk.store[("project", None, "credit")] = FakeEntity("credit", "project", [ext("ai-compliance", {"r": "HIGH"})])

    assert tools.get_entity_extension("applications", "dataset", "data-compliance") == {"scope": "TRAINING"}
    assert tools.get_project_extension("credit", "ai-compliance") == {"r": "HIGH"}


def test_get_extension_is_empty_without_extension_or_entity(sdk):
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn", None)
    sdk.store[("project", None, "credit")] = FakeEntity("credit", "project", [ext("other", {})])

    assert tools.get_entity_extension("scorer", "model", "model-compliance") == {}
    assert tools.get_entity_extension("missing", "model", "model-compliance") == {}
    assert tools.get_project_extension("credit", "ai-compliance") == {}
    assert tools.get_project_extension("missing", "ai-compliance") == {}


def test_save_adds_the_extension_and_keeps_the_others(sdk):
    sdk.store[("model", "credit", "scorer")] = FakeEntity("scorer", "sklearn", [ext("quality", {"q": 1}, id="e0")])

    tools.save_entity_extension("scorer", "model", "model-compliance", {"objectives": []})

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

    tools.save_entity_extension("applications", "dataset", "data-compliance", {"new": True})

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
        tools.save_entity_extension("missing", "dataset", "data-compliance", {})
    with pytest.raises(EntityNotExistsError):
        tools.save_project_extension("missing", "ai-compliance", {})
