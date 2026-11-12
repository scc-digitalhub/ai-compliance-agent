# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from compliance_core.reporting import build_reports


ROOT = Path(__file__).resolve().parents[1]


def canonical_results():
    guide = (ROOT / "docs/compliance-platform-usage-guide.md").read_text()
    section = guide.split("### Canonical result file and reporting CLI", 1)[1]
    return json.loads(re.search(r"```json\n(.*?)\n```", section, re.S).group(1))


def test_usage_guide_result_file_builds_both_report_variants():
    built = build_reports(canonical_results())
    assert "error" not in built, built
    encoded = json.dumps(built)
    assert '"EVALUATION"' in encoded
    assert '"TEST"' in encoded
    assert '"PASS"' in encoded


def test_usage_guide_cli_preview_works_without_model_or_dh(tmp_path):
    results = tmp_path / "results.json"
    results.write_text(json.dumps(canonical_results()))
    completed = subprocess.run(
        [
            sys.executable, "-m", "compliance_core.report_cli", "preview",
            "--results", str(results), "--project", "credit", "--entity-kind", "model",
            "--entity", "loan-scorer-v1", "--variants", "EVALUATION,TEST",
            "--report-name", "EVALUATION=validation-2026-11-11-measurements",
            "--report-name", "TEST=validation-2026-11-11-checks",
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert "error" not in result, result


def test_documented_http_report_scenarios_without_model_calls():
    from fastapi.testclient import TestClient

    from compliance_api.app import create_app
    from compliance_api.config import ApiSettings

    reports = build_reports(canonical_results())["reports"]
    with TestClient(create_app(ApiSettings(enable_dh=False))) as client:
        built = client.post(
            "/v1/compliance/reports",
            json={"results": canonical_results(), "variants": ["EVALUATION", "TEST"]},
        )
        assert built.status_code == 200, built.text
        assert "error" not in built.json()
        for report in reports.values():
            valid = client.post("/v1/compliance/reports/validate", json={"report": report})
            assert valid.status_code == 200, valid.text
            assert valid.json()["valid"] is True


def test_usage_reports_conform_to_packaged_okf_schemas():
    from importlib.resources import files

    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource

    schemas = files("compliance_core").joinpath("data", "okb", "schemas")
    resources = []
    for path in schemas.iterdir():
        if path.name.endswith(".json"):
            schema = json.loads(path.read_text())
            resources.append((schema["$id"] + ".json", Resource.from_contents(schema)))
    registry = Registry().with_resources(resources)
    schema = json.loads(schemas.joinpath("ReportSpec.json").read_text())
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    for report in build_reports(canonical_results())["reports"].values():
        validator.validate(report)


def test_two_report_variants_cannot_silently_overwrite_one_named_extension():
    from compliance_core.report_cli import run_report_workflow

    class Repository:
        supports_atomic_batch = False

        def __init__(self):
            self.writes = []

        def get(self, kind, entity, name, project=None):
            return {}

        def save_batch(self, *args, **kwargs):
            self.writes.append((args, kwargs))

    repository = Repository()
    with pytest.raises(ValueError):
        run_report_workflow(
            canonical_results(), mode="publish", project="credit", entity_kind="model",
            entity="loan-scorer-v1", variants=("EVALUATION", "TEST"),
            names={"EVALUATION": "same-run", "TEST": "same-run"}, repository=repository,
        )
    assert repository.writes == []
