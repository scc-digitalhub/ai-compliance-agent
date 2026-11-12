# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Structured analysis endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from compliance_core.contracts import (
    AnalysisResponse,
    ComplianceContextOut,
    DataComplianceOut,
    DatasetAnalysisRequest,
    ErrorResponse,
    ModelAnalysisRequest,
    ModelComplianceOut,
    ProjectInput,
)

ERRORS = {
    401: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}

router = APIRouter(prefix="/v1/compliance", tags=["compliance"])


def _request_id(request: Request) -> str:
    return request.state.request_id


@router.post(
    "/context",
    response_model=AnalysisResponse[ComplianceContextOut],
    responses=ERRORS,
    summary="Build the compliance context of a project definition",
)
async def build_context(body: ProjectInput, request: Request):
    return await request.app.state.registry.get("project_context").run(
        "project_context", body, _request_id(request)
    )


@router.post(
    "/datasets",
    response_model=AnalysisResponse[DataComplianceOut],
    responses=ERRORS,
    summary="Derive the data compliance specification of a dataset definition",
)
async def analyze_dataset(body: DatasetAnalysisRequest, request: Request):
    return await request.app.state.registry.get("dataset").run(
        "dataset", body, _request_id(request)
    )


@router.post(
    "/models",
    response_model=AnalysisResponse[ModelComplianceOut],
    responses=ERRORS,
    summary="Derive the model compliance specification of a model definition",
)
async def analyze_model(body: ModelAnalysisRequest, request: Request):
    return await request.app.state.registry.get("model").run("model", body, _request_id(request))


__all__ = ["router"]
