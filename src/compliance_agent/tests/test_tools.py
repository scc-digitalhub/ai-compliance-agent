"""Tests for OKF bundle navigation tools — no LLM required."""
from __future__ import annotations

import pytest
from pathlib import Path


# ── Helpers ────────────────────────────────────────────────────────────────────

def _okf_available() -> bool:
    from config import settings
    return settings.okf_bundle_path.is_dir()


skip_no_okf = pytest.mark.skipif(not _okf_available(), reason="OKF bundle not found")


# ── list_okf_directory ─────────────────────────────────────────────────────────

@skip_no_okf
def test_list_root_catalog():
    from agent.tools import list_okf_directory
    result = list_okf_directory.invoke({"path": "catalog"})
    assert "regulatory-refs" in result or "Regulatory" in result


@skip_no_okf
def test_list_regulatory_refs_dir():
    from agent.tools import list_okf_directory
    result = list_okf_directory.invoke({"path": "catalog/regulatory-refs"})
    assert "eu-ai-act" in result.lower()
    assert "gdpr" in result.lower()


@skip_no_okf
def test_list_metrics_dir():
    from agent.tools import list_okf_directory
    result = list_okf_directory.invoke({"path": "catalog/metrics"})
    assert "fairness" in result.lower()
    assert "performance" in result.lower()
    assert "privacy" in result.lower()


@skip_no_okf
def test_list_nonexistent_returns_not_found():
    from agent.tools import list_okf_directory
    result = list_okf_directory.invoke({"path": "catalog/does-not-exist"})
    assert "NOT FOUND" in result or "not found" in result.lower()


# ── read_okf_concept ───────────────────────────────────────────────────────────

@skip_no_okf
def test_read_eu_ai_act_ref():
    from agent.tools import read_okf_concept
    result = read_okf_concept.invoke({"path": "catalog/regulatory-refs/eu-ai-act.md"})
    assert "EU_AI_ACT" in result
    assert "2024/1689" in result


@skip_no_okf
def test_read_gdpr_ref():
    from agent.tools import read_okf_concept
    result = read_okf_concept.invoke({"path": "catalog/regulatory-refs/gdpr.md"})
    assert "GDPR" in result
    assert "2016/679" in result


@skip_no_okf
def test_read_fairness_metric():
    from agent.tools import read_okf_concept
    result = read_okf_concept.invoke(
        {"path": "catalog/metrics/fairness/demographic-parity-difference.md"}
    )
    assert "demographic_parity_difference" in result
    assert "fairlearn" in result.lower()


@skip_no_okf
def test_read_nonexistent_returns_marker():
    from agent.tools import read_okf_concept
    result = read_okf_concept.invoke({"path": "catalog/does-not-exist.md"})
    assert "NOT FOUND" in result


def test_read_path_traversal_blocked():
    from agent.tools import read_okf_concept
    with pytest.raises(ValueError, match="traversal"):
        read_okf_concept.invoke({"path": "../../etc/passwd"})


# ── search_catalog ─────────────────────────────────────────────────────────────

@skip_no_okf
def test_search_fairness():
    from agent.tools import search_catalog
    result = search_catalog.invoke({"query": "fairness demographic parity"})
    assert "demographic-parity" in result.lower()


@skip_no_okf
def test_search_scoped_to_category():
    from agent.tools import search_catalog
    result = search_catalog.invoke({"query": "accuracy", "category": "catalog/metrics/performance"})
    assert "accuracy" in result.lower()
    # Should not bleed into other categories
    assert "fairness" not in result.lower() or "performance" in result.lower()


@skip_no_okf
def test_search_no_match_returns_message():
    from agent.tools import search_catalog
    result = search_catalog.invoke({"query": "xyzzy_nonexistent_term_42"})
    assert "No concepts found" in result or "no concepts" in result.lower()


# ── get_regulatory_refs ────────────────────────────────────────────────────────

@skip_no_okf
def test_get_all_regulatory_refs():
    from agent.tools import get_regulatory_refs
    result = get_regulatory_refs.invoke({"frameworks": ""})
    assert "eu-ai-act" in result.lower()
    assert "gdpr" in result.lower()
    assert "nist" in result.lower()


@skip_no_okf
def test_get_filtered_regulatory_refs():
    from agent.tools import get_regulatory_refs
    result = get_regulatory_refs.invoke({"frameworks": "gdpr"})
    assert "gdpr" in result.lower()


# ── get_requirements ──────────────────────────────────────────────────────────

@skip_no_okf
def test_get_eu_ai_act_requirements():
    from agent.tools import get_requirements
    result = get_requirements.invoke({"framework": "eu-ai-act", "article": ""})
    assert "art" in result.lower()
    assert len(result.splitlines()) >= 5


@skip_no_okf
def test_get_specific_article():
    from agent.tools import get_requirements
    result = get_requirements.invoke({"framework": "eu-ai-act", "article": "art10"})
    assert "data" in result.lower() or "governance" in result.lower()


@skip_no_okf
def test_get_unknown_framework_lists_available():
    from agent.tools import get_requirements
    result = get_requirements.invoke({"framework": "unknown-xyz", "article": ""})
    assert "not found" in result.lower() or "available" in result.lower()


# ── get_groups ────────────────────────────────────────────────────────────────

@skip_no_okf
def test_get_all_groups():
    from agent.tools import get_groups
    result = get_groups.invoke({"vulnerability_or_kind": ""})
    assert "minors" in result.lower() or "children" in result.lower()
    # concept file is persons-with-disabilities.md; description uses 'impairments'
    assert "disabilit" in result.lower() or "impairment" in result.lower()


@skip_no_okf
def test_get_vulnerable_groups():
    from agent.tools import get_groups
    result = get_groups.invoke({"vulnerability_or_kind": "vulnerable"})
    assert len(result.splitlines()) >= 3


# ── get_attributes ────────────────────────────────────────────────────────────

@skip_no_okf
def test_get_gdpr_attributes():
    from agent.tools import get_attributes
    result = get_attributes.invoke({"concern": "gdpr"})
    assert "health" in result.lower() or "biometric" in result.lower()


@skip_no_okf
def test_get_gender_attribute():
    from agent.tools import get_attributes
    result = get_attributes.invoke({"concern": "gender"})
    assert "gender" in result.lower()


# ── get_metrics ───────────────────────────────────────────────────────────────

@skip_no_okf
def test_get_fairness_metrics():
    from agent.tools import get_metrics
    result = get_metrics.invoke({"concern_area": "fairness", "applies_to": ""})
    assert "parity" in result.lower() or "equalized" in result.lower()


@skip_no_okf
def test_get_privacy_metrics():
    from agent.tools import get_metrics
    result = get_metrics.invoke({"concern_area": "privacy", "applies_to": ""})
    assert "anonymity" in result.lower() or "epsilon" in result.lower()


@skip_no_okf
def test_get_metrics_unknown_area():
    from agent.tools import get_metrics
    result = get_metrics.invoke({"concern_area": "nonexistent", "applies_to": ""})
    assert "not found" in result.lower() or "available" in result.lower()


# ── get_misuse_scenarios ──────────────────────────────────────────────────────

@skip_no_okf
def test_get_all_misuse_scenarios():
    from agent.tools import get_misuse_scenarios
    result = get_misuse_scenarios.invoke({"domain_or_kind": ""})
    assert "injection" in result.lower() or "poisoning" in result.lower()


@skip_no_okf
def test_get_adversarial_misuse():
    from agent.tools import get_misuse_scenarios
    result = get_misuse_scenarios.invoke({"domain_or_kind": "adversarial"})
    assert len(result.splitlines()) >= 2
