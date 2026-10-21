"""Request-scoped dependencies: authentication and access to the runner registry."""
from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from ..runtime import RunnerRegistry


async def require_api_key(request: Request, x_api_key: Annotated[str | None, Header()] = None) -> None:
    keys = request.app.state.settings.api_key_list
    if not keys:  # auth disabled (development)
        return
    if not x_api_key or not any(secrets.compare_digest(x_api_key, k) for k in keys):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid API key")


def get_runner_registry(request: Request) -> RunnerRegistry:
    return request.app.state.registry


Registry = Annotated[RunnerRegistry, Depends(get_runner_registry)]


def request_id_of(request: Request) -> str:
    return request.state.request_id
