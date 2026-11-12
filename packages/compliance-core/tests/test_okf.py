# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from compliance_core.knowledge import get_bundle
from compliance_core.knowledge_tools import (
    get_metrics,
    get_requirements,
    read_okf_concept,
    search_catalog,
)
from compliance_core.state import InMemoryStateStore
from compliance_core.tools import ToolEnv


@pytest.fixture
def env():
    return ToolEnv(state=InMemoryStateStore(), bundle=get_bundle())


def test_bundle_loads_catalog(bundle):
    assert len(bundle.concepts) > 100
    assert "req-euai-art-10" in bundle.ids_of_type("Requirement")  # front-matter with unquoted colons
    assert len(bundle.version) == 12


def test_path_traversal_is_blocked(bundle, env):
    with pytest.raises(ValueError):
        bundle.resolve("../README.md")
    with pytest.raises(ValueError):
        bundle.resolve("../okf-evil/x.md")
    assert read_okf_concept(env, "../README.md").startswith("[INVALID PATH")


def test_requirements_tool_returns_instances(env):
    out = get_requirements(env, "eu-ai-act", "art10")
    assert out["count"] == 1
    item = out["items"][0]
    assert item["id"] == "req-euai-art-10"
    assert item["instance"]["source"]["framework"] == "EU_AI_ACT"
    assert item["path"].endswith("art10-data-governance.md")


def test_unknown_framework_lists_available(env):
    out = get_requirements(env, "nope")
    assert "eu-ai-act" in out["available"]


def test_metrics_tool_returns_ready_to_use_metric(env):
    out = get_metrics(env, "fairness", "Model")
    ids = {i["id"] for i in out["items"]}
    assert "metric-demographic-parity-difference" in ids
    assert all(i["instance"]["kind"] in ("PRIMITIVE", "COMPOSITE") for i in out["items"])


def test_search_catalog_ranks_matches(env):
    out = search_catalog(env, "fairness parity")
    assert out["total"] > 0
    assert out["items"][0]["path"].startswith("catalog/")
