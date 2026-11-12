# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""MCP server exposing the framework-neutral compliance tool catalog."""
from __future__ import annotations

import asyncio
import inspect
import logging
import os
import stat
from functools import wraps
from pathlib import Path
from typing import Any, get_type_hints
from urllib.parse import urlsplit

from compliance_core.knowledge import get_bundle
from compliance_core.settings import get_core_settings
from compliance_core.state import FileStateStore, transaction
from compliance_core.tool_catalog import TOOL_SPECS
from compliance_core.tools import ToolEnv, ToolSpec
from compliance_core.validation_tools import AnalysisKind
from compliance_core.version import framework_version

logger = logging.getLogger(__name__)

_SERVER_INSTRUCTIONS = """\
Use the compliance tools in host-driven mode. Gather project, dataset, or model details from the
user and relevant workspace context. Check DigitalHub for an existing specification before
analysis; ask before re-running one, continue on not_found, and report other lookup failures. Use
the OKF knowledge tools to ground the analysis, obtain the required JSON Schema with
get_output_schema, then generate the structured result yourself. Call record_compliance_analysis
to validate and store it in this workspace. Correct validation errors before saving. DigitalHub
lookups and persistence are available by default; save only when the user asks to persist results
there. Metric-evaluation and reporting code generation are also host-driven by default; validate artifacts
statically and never execute generated source. For reports, either load authorized result data and
build reports directly, or generate a standalone/combined reporting executable. Delegated LLM
analysis and code generation are opt-in.
"""

_MAX_INPUT_BYTES = 1_000_000


def _workspace_input_reader(workspace: Path):
    root = workspace.resolve()

    def read(source: str) -> bytes:
        parsed = urlsplit(source)
        relative = Path(source)
        if (
            parsed.scheme
            or parsed.netloc
            or relative.is_absolute()
            or not source
            or any(part in ("", ".", "..") for part in relative.parts)
        ):
            raise ValueError("Only workspace-relative local result paths are supported")
        candidate = root / relative
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(f"Result path is unavailable: {exc}") from exc
        if not resolved.is_relative_to(root):
            raise ValueError("Result path must remain inside the configured workspace")
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for component in relative.parts[:-1]:
                child = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
                os.close(directory)
                directory = child
            descriptor = os.open(
                relative.parts[-1],
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            with os.fdopen(descriptor, "rb") as stream:
                details = os.fstat(stream.fileno())
                if not stat.S_ISREG(details.st_mode):
                    raise ValueError("Result path must identify a regular workspace file")
                if details.st_size > _MAX_INPUT_BYTES:
                    raise ValueError(f"Result file exceeds the {_MAX_INPUT_BYTES}-byte limit")
                content = stream.read(_MAX_INPUT_BYTES + 1)
            if len(content) > _MAX_INPUT_BYTES:
                raise ValueError(f"Result file exceeds the {_MAX_INPUT_BYTES}-byte limit")
            return content
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(f"Result path could not be read safely: {exc}") from exc
        finally:
            os.close(directory)

    return read


def _default_env(workspace: Path, enable_dh: bool) -> ToolEnv:
    env = ToolEnv(
        state=FileStateStore(workspace / ".compliance"),
        bundle=get_bundle(),
        input_reader=_workspace_input_reader(workspace),
    )
    if enable_dh:
        from compliance_dh.repositories import (
            DhEntityCatalog,
            DhReportRepository,
            DhSpecificationRepository,
        )

        env.entities = DhEntityCatalog()
        env.specifications = DhSpecificationRepository()
        env.reports = DhReportRepository()
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
        if spec.needs_llm:
            # Model calls can take minutes; their state updates are locked individually instead.
            result = spec.fn(env, **kwargs) if has_env else spec.fn(**kwargs)
            return await result if inspect.isawaitable(result) else result
        with transaction(env.state):
            result = spec.fn(env, **kwargs) if has_env else spec.fn(**kwargs)
            if inspect.isawaitable(result):
                result = await result
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
            "enable_delegated_analysis requires a configured structured analysis_engine in ToolEnv"
        )

    server = MCPServer(
        name="ai-compliance",
        version=framework_version(),
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

    def metric_evaluation_code() -> str:
        return (
            "Generate metric evaluation code using the requested catalog metric and explicit "
            "entity/data bindings. Retrieve its computation guidance, obtain the artifact schema, "
            "then statically validate and record the result. Do not execute generated code or "
            "claim that its output has been computed."
        )

    def compliance_report() -> str:
        return (
            "Build a compliance report from explicitly supplied or authorized result data, or "
            "generate a standalone/combined reporting executable. Resolve result sources only "
            "through supported bounded readers, preserve provenance, validate report schemas, and "
            "record artifacts locally. Never execute generated source. Attach reports to "
            "DigitalHub only when explicitly requested."
        )

    server.prompt(
        name="compliance_analysis",
        description="Start a host-driven compliance analysis for a project, dataset, or model.",
    )(compliance_analysis)
    server.prompt(
        name="metric_evaluation_code",
        description="Generate and statically validate a metric evaluation artifact.",
    )(metric_evaluation_code)
    server.prompt(
        name="compliance_report",
        description="Build reports from supplied results or generate reporting code.",
    )(compliance_report)
    return server


def _delegated_engine():
    try:
        from compliance_api.engine import create_delegated_engine
    except ImportError as exc:
        raise RuntimeError(
            "Delegated analysis and code generation need LiteLLM; install the 'server' extra "
            "(or 'mcp' together with 'api')."
        ) from exc
    return create_delegated_engine()


def main(argv: list[str] | None = None) -> None:
    """Run the MCP server over stdio."""
    import argparse

    parser = argparse.ArgumentParser(prog="compliance-mcp", description=main.__doc__)
    parser.add_argument("--workspace", help="Workspace whose .compliance/ directory holds analysis state")
    parser.add_argument(
        "--delegated", action="store_true",
        help="Also expose delegated analysis and code-generation tools backed by LiteLLM "
        "(requires model configuration and provider credentials)",
    )
    parser.add_argument("--no-dh", action="store_true", help="Disable DigitalHub entity and specification tools")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace or get_core_settings().workspace_path).expanduser().resolve()
    env = _default_env(workspace, not args.no_dh)
    if args.delegated:
        env.analysis_engine = _delegated_engine()
    server = create_server(
        workspace, env=env, enable_dh=not args.no_dh, enable_delegated_analysis=args.delegated,
    )
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
