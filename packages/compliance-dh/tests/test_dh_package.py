from __future__ import annotations

from compliance_dh import tools
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository


def test_dh_adapters_implement_core_repository_ports(monkeypatch) -> None:
    calls: list[tuple] = []
    stored = {"description": "catalog value", "managed": "keep"}

    monkeypatch.setattr(
        tools,
        "get_entity",
        lambda entity, kind, project=None: {"name": entity, "kind": kind},
    )
    monkeypatch.setattr(
        tools,
        "get_project_extension",
        lambda entity, extension: dict(stored),
    )
    monkeypatch.setattr(
        tools,
        "save_project_extension",
        lambda entity, extension, spec: calls.append((entity, extension, spec)),
    )

    entities = DhEntityCatalog()
    specifications = DhSpecificationRepository()

    assert entities.get("dataset", "applications") == {
        "name": "applications",
        "kind": "dataset",
    }
    assert specifications.get("project", "credit") == stored
    specifications.save("project", "credit", {"context": {"risk": "HIGH"}})

    assert calls == [
        (
            "credit",
            "ai-compliance",
            {"description": "catalog value", "managed": "keep", "context": {"risk": "HIGH"}},
        )
    ]
