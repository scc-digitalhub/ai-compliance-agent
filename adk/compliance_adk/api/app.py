"""FastAPI service exposing the structured agents.

Run: uvicorn compliance_adk.api.app:app --port 8100   (from the adk directory)
"""
from __future__ import annotations

import logging
import re
import secrets
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app

from ..config import ADK_DIR, Settings, get_settings
from ..contracts import ErrorResponse
from ..errors import ComplianceAdkError
from ..runtime import RunnerRegistry, get_registry
from .routers import analysis, health

logger = logging.getLogger(__name__)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_PUBLIC_PATHS = {"/health", "/ready", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}


def create_app(settings: Settings | None = None, registry: RunnerRegistry | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Building the registry validates model configuration and loads skills and the OKF bundle.
        app.state.registry = registry or get_registry()
        if not settings.api_key_list:
            logger.warning("API_KEYS is empty: authentication is disabled")
        yield

    app = get_fast_api_app(
        agents_dir=str(ADK_DIR),
        web=False,
        lifespan=lifespan,
        allow_origins=settings.cors_origin_list or None,
    )
    app.title = "AI Compliance Analysis API"
    app.version = "1.0.0"
    app.state.settings = settings

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request.state.request_id = incoming if _REQUEST_ID.match(incoming) else uuid.uuid4().hex
        length = request.headers.get("content-length", "")
        if (
            settings.api_key_list
            and request.method != "OPTIONS"
            and request.url.path not in _PUBLIC_PATHS
            and not any(
                secrets.compare_digest(request.headers.get("x-api-key", ""), key)
                for key in settings.api_key_list
            )
        ):
            response = JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    detail="Missing or invalid API key", code="unauthorized", request_id=request.state.request_id
                ).model_dump(),
            )
        elif length.isdigit() and int(length) > settings.max_body_bytes:
            response = JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    detail="Request body too large", code="payload_too_large", request_id=request.state.request_id
                ).model_dump(),
            )
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ComplianceAdkError)
    async def domain_error(request: Request, exc: ComplianceAdkError):
        logger.warning("request_id=%s %s: %s", request.state.request_id, exc.code, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=str(exc), code=exc.code, request_id=request.state.request_id
            ).model_dump(),
        )

    # ADK already owns /health and its production agent/session/artifact routes.
    # Add only the compliance-specific readiness and analysis endpoints.
    app.include_router(health.router)
    app.include_router(analysis.router)
    return app


app = create_app()
