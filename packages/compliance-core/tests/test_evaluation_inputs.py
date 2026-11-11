from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from compliance_core.evaluation_inputs import InputError, load_results


def record():
    metric = {"id": "accuracy", "name": "Accuracy", "kind": "PRIMITIVE", "scale": "RATIO"}
    return {"project": "p", "entity": "m", "objective_ref": "o",
            "objective": {"id": "o", "metric": metric,
                          "condition": {"threshold": {"operator": "GEQ", "value": .9}}},
            "metric_result": {"metric": metric, "value": .95, "computed_at": "2026-01-01T00:00:00Z"}}


@pytest.fixture
def evidence_dir():
    # Keep evidence files inside the repository rather than system temp directories.
    directory = Path(__file__).parent / f".evidence-inputs-{os.getpid()}"
    directory.mkdir()
    try:
        yield directory
    finally:
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()


def test_canonical_json_loaded_once_and_content_digest_retained():
    raw = json.dumps({"results": [record()]}).encode()
    calls = []

    def reader(source):
        calls.append(source)
        return raw

    result = load_results("resource:run/version-1", reader=reader)
    assert calls == ["resource:run/version-1"]
    assert len(result["source"]["sha256"]) == 64
    assert result["results"][0]["provenance"]["external_source"] == result["source"]
    assert result["results"][0]["provenance"]["verification"].startswith("externally_supplied")


def test_explicit_mapping_not_filename_inference():
    wrapped = {"external": record()}
    mapping = {key: f"/external/{key}" for key in record()}
    result = load_results("arbitrary-name", reader=lambda _: json.dumps(wrapped).encode(), mapping=mapping)
    assert result["results"][0]["objective_ref"] == "o"
    assert result["source"]["mapping"] == mapping
    with pytest.raises(InputError):
        load_results("accuracy.json", reader=lambda _: b'{"value":0.95}')
    with pytest.raises(InputError):
        load_results("r", reader=lambda _: b"{}", mapping={"made_up": ""})


def test_local_regular_file_root_and_symlink_boundaries(evidence_dir):
    raw = json.dumps([record()])
    file = evidence_dir / "results.json"
    file.write_text(raw)
    assert load_results("results.json", allowed_root=evidence_dir)["results"][0]["entity"] == "m"
    link = evidence_dir / "link.json"
    link.symlink_to(file.name)
    with pytest.raises(InputError):
        load_results("link.json", allowed_root=evidence_dir)
    with pytest.raises(InputError):
        load_results("../test_evaluation_inputs.py", allowed_root=evidence_dir)
    with pytest.raises(InputError):
        load_results(".", allowed_root=evidence_dir)


@pytest.mark.parametrize("source", ["https://example.invalid/results", "store://p/result/a", "file://evil/path"])
def test_unknown_or_remote_sources_need_authorized_reader(source):
    with pytest.raises(InputError):
        load_results(source)


@pytest.mark.parametrize("raw", [
    b"not-json", b"\xff", b'{"results":[]}', b'{"a":1,"a":2}', b'{"value":NaN}',
    b'{"value":Infinity}', b'{"value":-Infinity}',
])
def test_malformed_ambiguous_or_empty_json_is_rejected(raw):
    with pytest.raises(InputError):
        load_results("source", reader=lambda _: raw)


def test_limits_formats_and_reader_failure(evidence_dir):
    with pytest.raises(InputError, match="size limit"):
        load_results("large", reader=lambda _: b" " * 11, max_bytes=10)
    file = evidence_dir / "big.json"
    file.write_bytes(b" " * 20)
    with pytest.raises(InputError, match="size limit"):
        load_results("big.json", allowed_root=evidence_dir, max_bytes=10)
    with pytest.raises(InputError, match="Only canonical JSON"):
        load_results("csv", format="csv")
    with pytest.raises(InputError, match="immutable bytes"):
        load_results("r", reader=lambda _: "{}")
    with pytest.raises(InputError, match="could not resolve"):
        load_results("r", reader=lambda _: (_ for _ in ()).throw(PermissionError("denied")))
