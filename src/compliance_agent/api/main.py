"""FastAPI application exposing the compliance agent over HTTP."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.agent import ComplianceAgent
from agent.schemas import (
    ComplianceContextResponse,
    DataComplianceResponse,
    ModelComplianceResponse,
)
from api.models import DatasetInput, ErrorResponse, ModelInput, ProjectInput

logger = logging.getLogger(__name__)


# ── Startup / shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the agent singleton (loads LLM client, validates OKF path)
    ComplianceAgent.get()
    logger.info("ComplianceAgent ready")
    yield


app = FastAPI(
    title="AI Compliance Agent API",
    description=(
        "LangChain-based agent that navigates the OKF compliance bundle to suggest "
        "ComplianceContext, data compliance objectives, and model compliance objectives."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handler ─────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


# ── Task 1: Compliance Context ────────────────────────────────────────────────

@app.post(
    "/compliance/context",
    response_model=ComplianceContextResponse,
    tags=["compliance"],
    summary="Build a ComplianceContext for an AI project",
    description=(
        "Given project metadata (domain, AI task, goal, deployment, …), the agent "
        "navigates the OKF bundle to identify applicable regulations, requirements, "
        "affected groups, protected attributes, misuse scenarios, and risk level."
    ),
)
async def build_compliance_context(project: ProjectInput) -> ComplianceContextResponse:
    try:
        return ComplianceAgent.get().build_compliance_context(project.model_dump())
    except Exception as exc:
        logger.error("Error analyzing context: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Task 2: Dataset Compliance ────────────────────────────────────────────────

@app.post(
    "/compliance/dataset",
    response_model=DataComplianceResponse,
    tags=["compliance"],
    summary="Analyse dataset compliance and suggest ComplianceObjectives",
    description=(
        "Given dataset metadata, schema fields, and optional sample records, the agent "
        "identifies protected attributes, data quality issues, and proposes concrete "
        "ComplianceObjective instances with metric thresholds."
    ),
)
async def analyze_dataset(dataset: DatasetInput) -> DataComplianceResponse:
    try:
        return ComplianceAgent.get().analyze_dataset(dataset.model_dump())
    except Exception as exc:
        logger.error("Error analyzing dataset: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Task 3: Model Compliance ──────────────────────────────────────────────────

@app.post(
    "/compliance/model",
    response_model=ModelComplianceResponse,
    tags=["compliance"],
    summary="Analyse model compliance and suggest ComplianceObjectives",
    description=(
        "Given model metadata (AI task, framework, output type, …) and optional prior "
        "requirements, the agent proposes compliance objectives covering fairness, "
        "robustness, transparency, calibration, and privacy."
    ),
)
async def analyze_model(model: ModelInput) -> ModelComplianceResponse:
    try:
        prior = model.prior_requirements or []
        return ComplianceAgent.get().analyze_model(model.model_dump(), prior)
    except Exception as exc:
        logger.error("Error analyzing model: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    from config import settings

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
