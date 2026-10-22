"""Structured analysis endpoints; each wraps one structured agent."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ...contracts import (
    AnalysisResponse,
    ComplianceContextOut,
    DataComplianceOut,
    DatasetAnalysisRequest,
    ErrorResponse,
    ModelAnalysisRequest,
    ModelComplianceOut,
    ProjectInput,
)
from ..deps import Registry, request_id_of

ERRORS = {
    401: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}

router = APIRouter(prefix="/v1/compliance", tags=["compliance"])


@router.post(
    "/context",
    response_model=AnalysisResponse[ComplianceContextOut],
    responses=ERRORS,
    summary="Build the compliance context of a project definition",
)
async def build_context(body: ProjectInput, request: Request, registry: Registry):
    return await registry.get("project_context").run(body, request_id_of(request))


@router.post(
    "/datasets",
    response_model=AnalysisResponse[DataComplianceOut],
    responses=ERRORS,
    summary="Derive the data compliance specification of a dataset definition",
)
async def analyze_dataset(body: DatasetAnalysisRequest, request: Request, registry: Registry):
    return await registry.get("dataset").run(body, request_id_of(request))


@router.post(
    "/models",
    response_model=AnalysisResponse[ModelComplianceOut],
    responses=ERRORS,
    summary="Derive the model compliance specification of a model definition",
)
async def analyze_model(body: ModelAnalysisRequest, request: Request, registry: Registry):
    return await registry.get("model").run(body, request_id_of(request))
