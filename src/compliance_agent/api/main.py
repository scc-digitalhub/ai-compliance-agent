"""FastAPI application exposing the compliance agent over HTTP."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.agent import ComplianceAgent
from agent.schemas import (
    ComplianceContextResponse,
    DataComplianceResponse,
    ModelComplianceResponse,
)
from api.crud import router as crud_router
from api.models import ErrorResponse, ProjectInput, DatasetInput, ModelInput
import stores

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

app.include_router(crud_router)


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
    "/compliance/context/{project_id}",
    response_model=ComplianceContextResponse,
    tags=["compliance"],
    summary="Build a ComplianceContext for a stored project",
    description=(
        "Loads the project by ID from storage, then navigates the OKF bundle to "
        "identify applicable regulations, requirements, affected groups, protected "
        "attributes, misuse scenarios, and risk level."
    ),
)
async def build_compliance_context(project_id: str) -> ComplianceContextResponse:
    entity = stores.projects.get(project_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    try:
        return ComplianceAgent.get().build_compliance_context(entity)
    except Exception as exc:
        logger.error("Error analyzing context: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/compliance/context",
    response_model=ComplianceContextResponse,
    tags=["compliance"],
    summary="Build a ComplianceContext for a project definition",
    description=(
        "Builds a ComplianceContext directly from the provided project definition, "
        "navigating the OKF bundle to identify applicable regulations, requirements, "
        "affected groups, protected attributes, misuse scenarios, and risk level."
    ),
)
async def build_compliance_context_from_definition(project: ProjectInput) -> ComplianceContextResponse:
    entity = project.model_dump()
    try:
        return ComplianceAgent.get().build_compliance_context(entity)
    except Exception as exc:
        logger.error("Error analyzing context: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Task 2: Dataset Compliance ────────────────────────────────────────────────

@app.post(
    "/compliance/dataset/{dataset_id}",
    response_model=DataComplianceResponse,
    tags=["compliance"],
    summary="Analyse compliance for a stored dataset",
    description=(
        "Loads the dataset by ID from storage, then identifies protected attributes, "
        "data quality issues, and proposes ComplianceObjective instances with metric thresholds."
    ),
)
async def analyze_dataset(dataset_id: str) -> DataComplianceResponse:
    entity = stores.datasets.get(dataset_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    try:
        return ComplianceAgent.get().analyze_dataset(entity)
    except Exception as exc:
        logger.error("Error analyzing dataset: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/compliance/dataset",
    response_model=DataComplianceResponse,
    tags=["compliance"],
    summary="Analyse compliance for a dataset definition",
    description=(
        "Identifies protected attributes, data quality issues, and proposes "
        "ComplianceObjective instances with metric thresholds."
    ),
)
async def analyze_dataset_from_definition(dataset: DatasetInput) -> DataComplianceResponse:
    entity = dataset.model_dump()
    try:
        return ComplianceAgent.get().analyze_dataset(entity)
    except Exception as exc:
        logger.error("Error analyzing dataset: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# ── Task 3: Model Compliance ──────────────────────────────────────────────────

@app.post(
    "/compliance/model/{model_id}",
    response_model=ModelComplianceResponse,
    tags=["compliance"],
    summary="Analyse compliance for a stored model",
    description=(
        "Loads the model by ID from storage. Pass an optional `project_id` query "
        "parameter to load the corresponding project and include it as context for "
        "the compliance analysis."
    ),
)
async def analyze_model(
    model_id: str, project_id: Optional[str] = None
) -> ModelComplianceResponse:
    entity = stores.models.get(model_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    prior = entity.pop("prior_requirements", [])
    if project_id:
        project = stores.projects.get(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        entity["project"] = project
    try:
        return ComplianceAgent.get().analyze_model(entity, prior)
    except Exception as exc:
        logger.error("Error analyzing model: %s", exc, exc_info=True, stack_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post(
    "/compliance/model",
    response_model=ModelComplianceResponse,
    tags=["compliance"],
    summary="Analyse compliance for a model definition",
    description=(
        "Analyses compliance for a model based on its definition. Identifies "
        "applicable regulations, requirements, affected groups, protected "
        "attributes, misuse scenarios, and risk level."
    ),
)
async def analyze_model_from_definition(model: ModelInput) -> ModelComplianceResponse:
    entity = model.model_dump()
    prior = entity.pop("prior_requirements", [])
    try:
        return ComplianceAgent.get().analyze_model(entity, prior)
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
