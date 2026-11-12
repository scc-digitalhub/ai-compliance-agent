# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.mcpserver")

from compliance_mcp.server import create_server


def test_mcp_server_exposes_host_driven_tools_without_engine() -> None:
    server = create_server(enable_dh=False)
    tools = {tool.name: tool for tool in server._tool_manager.list_tools()}
    resources = server._resource_manager.list_resources()
    templates = server._resource_manager.list_templates()
    prompts = server._prompt_manager.list_prompts()

    assert "record_compliance_analysis" in tools
    assert "get_output_schema" in tools
    assert "get_metric_computation" in tools
    assert "build_compliance_report" in tools
    assert "validate_compliance_report" in tools
    assert "generate_metric_evaluation_code" not in tools
    assert "generate_compliance_report_code" not in tools
    assert "analyze_project_context" not in tools
    assert "get_entity_details" not in tools
    assert "env" not in tools["record_compliance_analysis"].parameters["properties"]
    assert tools["record_compliance_analysis"].parameters["properties"]["kind"]["enum"] == [
        "project",
        "dataset",
        "model",
    ]
    assert tools["record_compliance_analysis"].annotations.read_only_hint is False
    assert [resource.uri for resource in resources] == ["okf://bundle/index"]
    assert [template.uri_template for template in templates] == ["okf://bundle/{path}"]
    assert {prompt.name for prompt in prompts} == {
        "compliance_analysis",
        "metric_evaluation_code",
        "compliance_report",
    }


def test_workspace_input_reader_is_bounded_and_confined(tmp_path) -> None:
    from compliance_mcp.server import _MAX_INPUT_BYTES, _workspace_input_reader

    reader = _workspace_input_reader(tmp_path)
    (tmp_path / "results.json").write_bytes(b'{"results":[]}')
    assert reader("results.json") == b'{"results":[]}'

    with pytest.raises(ValueError, match="workspace-relative"):
        reader(str(tmp_path / "results.json"))
    with pytest.raises(ValueError, match="workspace-relative"):
        reader("https://example.invalid/results.json")

    outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
    outside.write_bytes(b"{}")
    try:
        (tmp_path / "escape.json").symlink_to(outside)
        with pytest.raises(ValueError, match="inside"):
            reader("escape.json")
    finally:
        outside.unlink(missing_ok=True)

    (tmp_path / "large.json").write_bytes(b"x" * (_MAX_INPUT_BYTES + 1))
    with pytest.raises(ValueError, match="limit"):
        reader("large.json")


def test_digitalhub_tools_are_enabled_by_default_and_can_be_disabled() -> None:
    server = create_server()
    default_tools = {tool.name for tool in server._tool_manager.list_tools()}
    disabled_tools = {
        tool.name for tool in create_server(enable_dh=False)._tool_manager.list_tools()
    }

    assert {
        "get_entity_details",
        "get_compliance_specification",
        "save_compliance_specification",
        "get_compliance_report",
        "save_compliance_report",
    }.issubset(default_tools)
    assert {
        "get_entity_details",
        "get_compliance_specification",
        "save_compliance_specification",
        "get_compliance_report",
        "save_compliance_report",
    }.isdisjoint(disabled_tools)


def test_default_mcp_env_wires_report_repository_and_bounded_reader(tmp_path) -> None:
    from compliance_dh.repositories import DhReportRepository
    from compliance_mcp.server import _default_env

    enabled = _default_env(tmp_path, True)
    disabled = _default_env(tmp_path, False)
    assert isinstance(enabled.reports, DhReportRepository)
    (tmp_path / "input.json").write_bytes(b"{}")
    assert enabled.input_reader("input.json") == b"{}"
    assert disabled.reports is None
    assert disabled.input_reader is not None


def test_digitalhub_tool_schemas_expose_explicit_project() -> None:
    tools = {tool.name: tool for tool in create_server()._tool_manager.list_tools()}
    for name in ("get_entity_details", "get_compliance_specification", "save_compliance_specification"):
        assert "project" in tools[name].parameters["properties"]
        assert "env" not in tools[name].parameters["properties"]


def _main_server(monkeypatch, tmp_path, *args):
    from compliance_mcp import server as module

    captured = {}

    def capture(coroutine):
        captured["server"] = coroutine.cr_frame.f_locals["self"]
        coroutine.close()

    monkeypatch.setattr(module.asyncio, "run", capture)
    module.main(["--workspace", str(tmp_path), *args])
    return captured["server"]


def test_cli_delegated_option_exposes_the_litellm_analysis_tools(monkeypatch, tmp_path) -> None:
    pytest.importorskip("litellm")
    monkeypatch.setenv("STRUCTURED_MODEL", "openai/configured-for-test")
    server = _main_server(monkeypatch, tmp_path, "--delegated", "--no-dh")
    tools = {tool.name for tool in server._tool_manager.list_tools()}
    assert {"analyze_project_context", "analyze_dataset", "analyze_model"} <= tools
    assert {
        "generate_metric_evaluation_code",
        "generate_compliance_report_code",
    } <= tools
    assert "get_entity_details" not in tools

    default = {tool.name for tool in _main_server(monkeypatch, tmp_path)._tool_manager.list_tools()}
    assert "analyze_dataset" not in default and "get_entity_details" in default
    assert "generate_metric_evaluation_code" not in default


def test_cli_delegated_option_requires_a_configured_model(monkeypatch, tmp_path) -> None:
    pytest.importorskip("litellm")
    from compliance_core.errors import ConfigurationError

    for name in ("STRUCTURED_MODEL", "PROJECT_CONTEXT_AGENT_MODEL_NAME",
                 "DATA_ANALYSIS_AGENT_MODEL_NAME", "MODEL_ANALYSIS_AGENT_MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigurationError, match="STRUCTURED_MODEL"):
        _main_server(monkeypatch, tmp_path, "--delegated")


def test_delegated_analysis_runs_through_mcp_and_records_provenance(tmp_path) -> None:
    pytest.importorskip("litellm")
    import asyncio
    import json
    from importlib.resources import files
    from types import SimpleNamespace

    from compliance_api.config import ApiSettings
    from compliance_api.engine import AnalysisRegistry, DelegatedAnalysisEngine
    from compliance_core.knowledge import get_bundle
    from compliance_core.state import FileStateStore
    from compliance_core.tools import ToolEnv

    expected = json.loads(
        files("compliance_skills").joinpath("skills", "project-context", "references", "example.json").read_text()
    )

    async def completion(**kwargs):
        message = SimpleNamespace(content=json.dumps(expected), tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)

    engine = DelegatedAnalysisEngine(AnalysisRegistry(ApiSettings(structured_model="scripted"), completion=completion))
    store = FileStateStore(tmp_path / ".compliance")
    env = ToolEnv(state=store, bundle=get_bundle(), analysis_engine=engine)
    server = create_server(tmp_path, env=env, enable_dh=False, enable_delegated_analysis=True)
    project = {"name": "credit", "domain": "finance", "ai_task": "CLASSIFICATION", "goal": "Score loans"}

    asyncio.run(server._tool_manager.call_tool("analyze_project_context", {"project": project}, None))

    state = store.snapshot()
    assert state["analysis_active_project"] == "credit"
    assert state["analysis_project_context"]["risk_classification"]["risk_level"] == "HIGH"
    provenance = state["analysis_provenance"]["project"]
    assert provenance["mode"] == "delegated" and provenance["model"] == "scripted"
    assert provenance["okf_version"] == get_bundle().version
