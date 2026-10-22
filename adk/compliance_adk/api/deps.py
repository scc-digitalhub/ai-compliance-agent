"""Request-scoped dependencies: authentication and access to the runner registry."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from ..runtime import RunnerRegistry


def get_runner_registry(request: Request) -> RunnerRegistry:
    return request.app.state.registry


Registry = Annotated[RunnerRegistry, Depends(get_runner_registry)]


def request_id_of(request: Request) -> str:
    return request.state.request_id
