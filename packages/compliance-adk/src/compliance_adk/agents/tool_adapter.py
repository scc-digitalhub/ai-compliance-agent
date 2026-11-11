"""Bridge ADK invocation context to the runtime-neutral ToolEnv."""
from __future__ import annotations

import inspect
import os
import stat
from typing import Any
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from urllib.parse import urlsplit

from google.adk.tools import ToolContext
from pydantic import BaseModel

from compliance_core.contracts.envelope import AnalysisResponse
from compliance_core.state import MappingStateStore
from compliance_core.tools import ToolEnv
from compliance_core.settings import get_core_settings

from compliance_core.knowledge import get_bundle
from compliance_dh.repositories import DhEntityCatalog, DhReportRepository, DhSpecificationRepository

TOOL_ENV_FACTORY: ContextVar[Callable[[ToolContext], ToolEnv] | None] = ContextVar(
    "compliance_tool_env_factory", default=None
)
_MAX_INPUT_BYTES = 1_000_000


def workspace_input_reader(workspace: str | Path) -> Callable[[str], bytes]:
    root = Path(workspace).resolve()

    def read(source: str) -> bytes:
        relative = Path(source)
        parsed = urlsplit(source)
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
        except OSError as exc:
            raise ValueError(f"Result path could not be read safely: {exc}") from exc
        finally:
            os.close(directory)

    return read


class AdkAnalysisEngine:
    async def run(
        self, analysis: str, request: BaseModel, request_id: str | None = None
    ) -> AnalysisResponse[Any]:
        from ..runtime import get_registry

        return await get_registry().get(analysis).run(request, request_id)


def tool_env(tool_context: ToolContext) -> ToolEnv:
    factory = TOOL_ENV_FACTORY.get()
    if factory is not None:
        return factory(tool_context)
    return ToolEnv(
        state=MappingStateStore(tool_context.state),
        bundle=get_bundle(),
        specifications=DhSpecificationRepository(),
        entities=DhEntityCatalog(),
        analysis_engine=AdkAnalysisEngine(),
        reports=DhReportRepository(),
        input_reader=workspace_input_reader(get_core_settings().workspace_path),
    )


def wrap_core_tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Expose a core env-first tool through ADK's injected ToolContext parameter."""
    signature = inspect.signature(fn)
    parameters = list(signature.parameters.values())
    has_env = bool(parameters and parameters[0].name == "env")
    public = parameters[1:] if has_env else parameters
    annotations = inspect.get_annotations(fn, eval_str=True)
    annotations.pop("env", None)
    context_parameter = inspect.Parameter(
        "tool_context",
        inspect.Parameter.KEYWORD_ONLY,
        annotation=ToolContext,
    )
    public_signature = signature.replace(parameters=[*public, context_parameter])

    async def invoke(*args: Any, **kwargs: Any) -> Any:
        context = kwargs.pop("tool_context")
        result = fn(tool_env(context), *args, **kwargs) if has_env else fn(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    invoke.__name__ = fn.__name__
    invoke.__doc__ = fn.__doc__
    invoke.__signature__ = public_signature
    invoke.__annotations__ = {
        **{parameter.name: annotations.get(parameter.name, parameter.annotation)
           for parameter in public},
        "tool_context": ToolContext,
        "return": annotations.get("return", signature.return_annotation),
    }
    return invoke


__all__ = ["AdkAnalysisEngine", "tool_env", "workspace_input_reader", "wrap_core_tool"]
