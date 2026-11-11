from __future__ import annotations

from compliance_core.knowledge import get_bundle
from compliance_core.metric_computation import _code_blocks, _section, resolve_metric_computation


def test_computation_resolution_returns_exact_metric_and_all_python_blocks(bundle):
    result = resolve_metric_computation(bundle, "metric-data-completeness", entity_kind="dataset")

    assert result["supported"] is True
    assert result["status"] == "available"
    assert result["metric"]["instance"]["id"] == "metric-data-completeness"
    assert result["source_path"] == "catalog/metrics/data-quality/completeness.md"
    assert result["bundle_version"] == bundle.version
    assert result["computation_section"].startswith("# Computation")
    assert "Overall completeness" in result["computation_section"]
    assert len(result["code_blocks"]) == 1
    assert "def completeness" in result["code_blocks"][0]["source"]
    assert "print(" in result["code_blocks"][0]["source"]


def test_computation_resolution_does_not_invent_missing_metric():
    result = resolve_metric_computation(get_bundle(), "metric-does-not-exist")

    assert result["supported"] is False
    assert result["status"] == "unsupported"
    assert "No catalog metric matched" in result["reason"]


def test_computation_resolution_rejects_wrong_applicability(bundle):
    result = resolve_metric_computation(
        bundle, "metric-data-completeness", entity_kind="model",
    )

    assert result["supported"] is False
    assert result["status"] == "unsupported"
    assert "does not include model" in result["reason"]


def test_computation_section_keeps_headings_inside_fenced_code_and_ordered_blocks():
    text = (
        "## Computation\nProse\n"
        "```python\n# This is code, not a markdown section\nfirst()\n```\n"
        "Between\n```text\nformula\n```\n"
        "```python\nsecond()\n```\n## Notes\nnot computation\n"
    )

    section = _section(text)
    blocks = _code_blocks(section or "")

    assert section is not None
    assert "## Notes" not in section
    assert len(blocks) == 3
    assert [item["language"] for item in blocks] == ["python", "text", "python"]
    assert blocks[0]["source"].startswith("# This is code")
    assert blocks[2]["source"] == "second()"
