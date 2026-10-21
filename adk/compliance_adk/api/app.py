"""FastAPI service exposing the structured agents.

Run: uvicorn compliance_adk.api.app:app --port 8100   (from the adk directory)
"""
from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings, get_settings
from ..contracts import ErrorResponse
from ..errors import ComplianceAdkError
from ..runtime import RunnerRegistry, get_registry
from .routers import analysis, health

logger = logging.getLogger(__name__)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def create_app(settings: Settings | None = None, registry: RunnerRegistry | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Building the registry validates model configuration and loads skills and the OKF bundle.
        app.state.registry = registry or get_registry()
        if not settings.api_key_list:
            logger.warning("API_KEYS is empty: authentication is disabled")
        yield

    app = FastAPI(title="AI Compliance Analysis API", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["GET", "POST"],
            allow_headers=["X-API-Key", "Content-Type", "X-Request-ID"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request.state.request_id = incoming if _REQUEST_ID.match(incoming) else uuid.uuid4().hex
        length = request.headers.get("content-length", "")
        if length.isdigit() and int(length) > settings.max_body_bytes:
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

    app.include_router(health.router)
    app.include_router(analysis.router)
    return app


app = create_app()
