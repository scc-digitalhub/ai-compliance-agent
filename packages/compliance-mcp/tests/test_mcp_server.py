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
    assert [prompt.name for prompt in prompts] == ["compliance_analysis"]


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
    }.issubset(default_tools)
    assert {
        "get_entity_details",
        "get_compliance_specification",
        "save_compliance_specification",
    }.isdisjoint(disabled_tools)


def test_digitalhub_tool_schemas_expose_explicit_project() -> None:
    tools = {tool.name: tool for tool in create_server()._tool_manager.list_tools()}
    for name in ("get_entity_details", "get_compliance_specification", "save_compliance_specification"):
        assert "project" in tools[name].parameters["properties"]
        assert "env" not in tools[name].parameters["properties"]
