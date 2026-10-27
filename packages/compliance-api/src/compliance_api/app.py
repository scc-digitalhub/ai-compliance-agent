"""Standalone FastAPI service for compliance analysis."""
from __future__ import annotations

import logging
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from compliance_core.contracts import ErrorResponse
from compliance_core.errors import ComplianceError

from .config import ApiSettings, get_settings
from .engine import AnalysisRegistry
from .routers.analysis import router as analysis_router

logger = logging.getLogger(__name__)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_PUBLIC_PATHS = {"/health", "/ready", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}


def create_app(settings: ApiSettings | None = None, registry: Any | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.registry = registry or AnalysisRegistry(settings)
        if not settings.api_key_list:
            logger.warning("API_KEYS is empty: authentication is disabled")
        yield

    app = FastAPI(
        title="AI Compliance Analysis API",
        version="1.0.0",
        lifespan=lifespan,
    )
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["*"],
            allow_headers=["*"],
        )
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
                    detail="Missing or invalid API key",
                    code="unauthorized",
                    request_id=request.state.request_id,
                ).model_dump(),
            )
        elif length.isdigit() and int(length) > settings.max_body_bytes:
            response = JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    detail="Request body too large",
                    code="payload_too_large",
                    request_id=request.state.request_id,
                ).model_dump(),
            )
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ComplianceError)
    async def domain_error(request: Request, exc: ComplianceError):
        logger.warning("request_id=%s %s: %s", request.state.request_id, exc.code, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=str(exc), code=exc.code, request_id=request.state.request_id
            ).model_dump(),
        )

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["system"])
    async def ready(request: Request):
        analysis_registry = getattr(request.app.state, "registry", None)
        if analysis_registry is None or not analysis_registry.bundle.concepts:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {
            "status": "ready",
            "okf_version": analysis_registry.bundle.version,
            "concepts": len(analysis_registry.bundle.concepts),
        }

    app.include_router(analysis_router)
    return app


def main() -> None:
    import uvicorn

    uvicorn.run("compliance_api.app:app", host="127.0.0.1", port=8100)


app = create_app()


__all__ = ["app", "create_app", "main"]
