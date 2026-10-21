from __future__ import annotations

import pytest

from compliance_adk.knowledge import tools


def test_bundle_loads_catalog(bundle):
    assert len(bundle.concepts) > 100
    assert "req-euai-art-10" in bundle.ids_of_type("Requirement")  # front-matter with unquoted colons
    assert len(bundle.version) == 12


def test_path_traversal_is_blocked(bundle):
    with pytest.raises(ValueError):
        bundle.resolve("../README.md")
    with pytest.raises(ValueError):
        bundle.resolve("../okf-evil/x.md")
    assert tools.read_okf_concept("../README.md").startswith("[INVALID PATH")


def test_requirements_tool_returns_instances():
    out = tools.get_requirements("eu-ai-act", "art10")
    assert out["count"] == 1
    item = out["items"][0]
    assert item["id"] == "req-euai-art-10"
    assert item["instance"]["source"]["framework"] == "EU_AI_ACT"
    assert item["path"].endswith("art10-data-governance.md")


def test_unknown_framework_lists_available():
    out = tools.get_requirements("nope")
    assert "eu-ai-act" in out["available"]


def test_metrics_tool_returns_ready_to_use_metric():
    out = tools.get_metrics("fairness", "Model")
    ids = {i["id"] for i in out["items"]}
    assert "metric-demographic-parity-difference" in ids
    assert all(i["instance"]["kind"] in ("PRIMITIVE", "COMPOSITE") for i in out["items"])


def test_search_catalog_ranks_matches():
    out = tools.search_catalog("fairness parity")
    assert out["total"] > 0
    assert out["items"][0]["path"].startswith("catalog/")
