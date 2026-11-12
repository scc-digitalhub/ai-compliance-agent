# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from types import SimpleNamespace

import pytest

from compliance_dh import tools
from compliance_dh.repositories import DhReportRepository


def report(summary="Measured"):
    return {
        "kind": "EVALUATION",
        "content": {"evaluation": {"metrics": [], "summary": summary}},
        "objectives": ["objective::one"],
    }


@pytest.fixture
def backend(monkeypatch):
    entity = SimpleNamespace(extensions=[
        {"kind": "model-compliance", "name": "model-compliance", "id": "spec-1", "spec": {"objectives": []}},
        {"kind": "compliance-report", "name": "previous", "id": "report-1", "spec": report("Old")},
    ])
    writes = []
    sdk = SimpleNamespace(
        get_model=lambda identifier, project=None: entity,
        update_model=lambda value: writes.append(deepcopy(value.extensions)),
    )
    monkeypatch.setattr(tools, "sdk", sdk)
    return entity, writes


def test_named_reports_preserve_other_extensions_and_are_idempotent(backend):
    entity, writes = backend
    before = deepcopy(entity.extensions)
    repo = DhReportRepository()
    repo.save("model", "scorer", "today", report(), project="credit")
    assert entity.extensions[:2] == before
    assert repo.get("model", "scorer", "previous", "credit")["content"]["evaluation"]["summary"] == "Old"
    assert repo.get("model", "scorer", "today", "credit")["kind"] == "EVALUATION"
    repo.save("model", "scorer", "today", report(), project="credit")
    assert len(writes) == 1
    repo.save("model", "scorer", "previous", report("New"), project="credit")
    assert next(ext for ext in entity.extensions if ext["name"] == "previous")["id"] == "report-1"


def test_batch_stages_all_reports_in_one_update(backend):
    _, writes = backend
    DhReportRepository().save_batch("model", "scorer", {"a": report(), "b": report("Two")}, "credit")
    assert len(writes) == 1
    assert {"a", "b"} <= {ext["name"] for ext in writes[0]}


def test_strict_atomicity_rejected_before_backend_write(backend):
    _, writes = backend
    with pytest.raises(ValueError, match="atomic"):
        DhReportRepository().save_batch("model", "scorer", {"a": report()}, "credit", strict_atomic=True)
    assert writes == []


def test_project_mismatch_is_not_ignored(backend):
    with pytest.raises(ValueError, match="conflicts"):
        DhReportRepository().save("model", "store://other/model/scorer", "a", report(), "credit")
    assert backend[1] == []


def test_invalid_batch_does_not_mutate_entity(backend):
    entity, writes = backend
    before = deepcopy(entity.extensions)
    with pytest.raises(ValueError):
        DhReportRepository().save_batch("model", "scorer", {"a": report(), "b": {"kind": "WRONG"}}, "credit")
    assert entity.extensions == before
    assert writes == []


def test_backend_failure_is_not_a_success(backend, monkeypatch):
    def fail(value):
        raise PermissionError("Denied")
    monkeypatch.setattr(tools.sdk, "update_model", fail)
    with pytest.raises(PermissionError, match="Denied"):
        DhReportRepository().save("model", "scorer", "a", report(), "credit")


def test_duplicate_named_extensions_are_rejected(backend):
    entity, writes = backend
    entity.extensions.append(deepcopy(entity.extensions[1]))
    with pytest.raises(ValueError, match="Duplicate"):
        DhReportRepository().save("model", "scorer", "previous", report(), "credit")
    assert writes == []


def test_subject_revision_reader_uses_existing_specification_fingerprint(backend):
    from compliance_core.specification_tools import specification_revision

    repository = DhReportRepository()
    assert repository.get_specification_revision("model", "scorer", "credit") == specification_revision(
        {"objectives": []}
    )
    backend[0].extensions = [
        ext for ext in backend[0].extensions if ext["kind"] != "model-compliance"
    ]
    assert repository.get_specification_revision("model", "scorer", "credit") is None
