"""MCP server exposing the framework-neutral compliance tool catalog."""
from __future__ import annotations

import asyncio
import inspect
import logging
from functools import wraps
from pathlib import Path
from typing import Any, get_type_hints

from compliance_core.knowledge import get_bundle
from compliance_core.settings import get_core_settings
from compliance_core.state import FileStateStore
from compliance_core.tool_catalog import TOOL_SPECS
from compliance_core.tools import ToolEnv, ToolSpec
from compliance_core.validation_tools import AnalysisKind

logger = logging.getLogger(__name__)

_SERVER_INSTRUCTIONS = """\
Use the compliance tools in host-driven mode. Gather project, dataset, or model details from the
user and relevant workspace context. Check DigitalHub for an existing specification before
analysis; ask before re-running one, continue on not_found, and report other lookup failures. Use
the OKF knowledge tools to ground the analysis, obtain the required JSON Schema with
get_output_schema, then generate the structured result yourself. Call record_compliance_analysis
to validate and store it in this workspace. Correct validation errors before saving. DigitalHub
lookups and persistence are available by default; save only when the user asks to persist results
there. Delegated LLM analysis is opt-in.
"""


def _default_env(workspace: Path, enable_dh: bool) -> ToolEnv:
    env = ToolEnv(
        state=FileStateStore(workspace / ".compliance"),
        bundle=get_bundle(),
    )
    if enable_dh:
        from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository

        env.entities = DhEntityCatalog()
        env.specifications = DhSpecificationRepository()
    return env


def _tool_wrapper(spec: ToolSpec, env: ToolEnv):
    signature = inspect.signature(spec.fn)
    parameters = list(signature.parameters.values())
    has_env = bool(parameters and parameters[0].name == "env")
    annotations = get_type_hints(spec.fn)
    annotations.pop("env", None)
    public_parameters = parameters[1:] if has_env else parameters
    public_parameters = [
        parameter.replace(annotation=annotations.get(parameter.name, parameter.annotation))
        for parameter in public_parameters
    ]
    public_signature = signature.replace(
        parameters=public_parameters,
        return_annotation=annotations.get("return", signature.return_annotation),
    )

    @wraps(spec.fn)
    async def invoke(**kwargs: Any) -> Any:
        result = spec.fn(env, **kwargs) if has_env else spec.fn(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    invoke.__name__ = spec.name
    invoke.__doc__ = spec.description
    invoke.__signature__ = public_signature
    invoke.__annotations__ = annotations
    return invoke


def create_server(
    workspace: str | Path | None = None,
    *,
    env: ToolEnv | None = None,
    enable_dh: bool = True,
    enable_delegated_analysis: bool = False,
):
    """Create an MCP server with workspace state and DigitalHub integration by default."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "The MCP SDK is required; install the 'mcp' optional dependency."
        ) from exc

    workspace_path = Path(workspace or get_core_settings().workspace_path).expanduser().resolve()
    tool_env = env or _default_env(workspace_path, enable_dh)
    if enable_delegated_analysis and tool_env.analysis_engine is None:
        raise ValueError(
            "enable_delegated_analysis requires a configured analysis_engine in ToolEnv"
        )

    server = MCPServer(
        name="ai-compliance",
        version="0.1.0",
        instructions=_SERVER_INSTRUCTIONS,
    )
    from mcp.types import ToolAnnotations

    for spec in TOOL_SPECS:
        if spec.needs_llm and not enable_delegated_analysis:
            continue
        if spec.group == "dh" and not enable_dh:
            continue
        server.add_tool(
            _tool_wrapper(spec, tool_env),
            name=spec.name,
            description=spec.description,
            annotations=ToolAnnotations(
                readOnlyHint=spec.read_only,
                destructiveHint=spec.destructive,
                openWorldHint=spec.group == "dh",
            ),
        )

    def okf_index() -> str:
        return tool_env.bundle.list_directory("")

    def okf_path(path: str) -> str:
        if path.endswith(".md"):
            return tool_env.bundle.read(path)
        return tool_env.bundle.list_directory(path)

    server.resource(
        "okf://bundle/index",
        name="okf-index",
        description="Top-level index of the compliance knowledge framework.",
        mime_type="text/markdown",
    )(okf_index)
    server.resource(
        "okf://bundle/{path}",
        name="okf-path",
        description="Read an OKF Markdown concept or directory index by bundle-relative path.",
        mime_type="text/markdown",
    )(okf_path)

    def compliance_analysis(kind: AnalysisKind) -> str:
        return (
            f"Perform a host-driven {kind} compliance analysis. Gather the relevant inputs and "
            "workspace context, consult the OKF resources and tools, call get_output_schema with "
            f"kind='{kind}', generate a result that follows that schema, and call "
            "record_compliance_analysis with the original request and generated output. "
            "Correct any validation errors and record again. Do not write to DigitalHub unless "
            "the user asks; use save_compliance_specification for that explicit persistence."
        )

    server.prompt(
        name="compliance_analysis",
        description="Start a host-driven compliance analysis for a project, dataset, or model.",
    )(compliance_analysis)
    return server


def main() -> None:
    """Run the MCP server over stdio."""
    server = create_server()
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
