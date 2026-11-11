"""Code-generation and deterministic evaluation-report endpoints."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from compliance_core.contracts.evaluation_code import (
    MetricEvaluationCodeArtifact,
    MetricEvaluationCodeRequest,
)
from compliance_core.contracts.envelope import AnalysisResponse
from compliance_core.contracts.metric_evaluation import MeasurementEnvelope
from compliance_core.contracts.report_code import ReportCodeArtifact, ReportCodeRequest
from compliance_core.contracts.reports import ReportSpec
from compliance_core.evaluation_inputs import InputError, load_results
from compliance_core.reporting import build_reports, validate_report

from .analysis import ERRORS

router = APIRouter(prefix="/v1/compliance", tags=["compliance"])


class BuildReportsBody(BaseModel):
    results: list[MeasurementEnvelope] | None = Field(default=None, min_length=1)
    source: str | None = None
    format: str = "json"
    mapping: dict[str, str] | None = None
    variants: list[Literal["EVALUATION", "TEST"]] = Field(
        default_factory=lambda: ["EVALUATION", "TEST"], min_length=1
    )
    lineage: dict[str, Any] | None = None

    @model_validator(mode="after")
    def one_input(self) -> "BuildReportsBody":
        if (self.results is None) == (self.source is None):
            raise ValueError("provide exactly one of inline results or an authorized source reference")
        if self.source is not None and not self.source.strip():
            raise ValueError("source reference must not be empty")
        return self


class ValidateReportBody(BaseModel):
    report: dict[str, Any]


class ReportBuildResponse(BaseModel):
    reports: dict[str, dict[str, Any]]
    issues: list[dict[str, Any]]
    objective_references: list[dict[str, Any]]
    assessments: list[dict[str, Any]]
    provenance: list[dict[str, Any]]
    target: dict[str, Any]
    input_source: dict[str, Any] | None = None


class ReportValidationResponse(BaseModel):
    valid: bool
    errors: list[dict[str, str]] = Field(default_factory=list)
    report: ReportSpec | None = None


@router.post(
    "/metric-evaluation/code",
    response_model=AnalysisResponse[MetricEvaluationCodeArtifact],
    responses=ERRORS,
    summary="Generate and statically validate metric evaluation code",
)
async def generate_metric_evaluation_code(
    body: MetricEvaluationCodeRequest, request: Request,
):
    return await request.app.state.registry.get("metric_evaluation_code").run(
        "metric_evaluation_code", body, request.state.request_id
    )


@router.post(
    "/reports/code",
    response_model=AnalysisResponse[ReportCodeArtifact],
    responses=ERRORS,
    summary="Generate and statically validate standalone or combined reporting code",
)
async def generate_report_code(body: ReportCodeRequest, request: Request):
    return await request.app.state.registry.get("compliance_report_code").run(
        "compliance_report_code", body, request.state.request_id
    )


@router.post(
    "/reports",
    response_model=ReportBuildResponse,
    summary="Build reports from supplied measurement results",
)
async def build_compliance_reports(body: BuildReportsBody, request: Request):
    results: Any
    source_identity = None
    if body.source is not None:
        reader = getattr(request.app.state, "evaluation_input_reader", None)
        if reader is None:
            raise HTTPException(
                status_code=422,
                detail="No authorized evaluation input reader is configured for source references",
            )
        try:
            loaded = load_results(
                body.source, format=body.format, mapping=body.mapping, reader=reader,
            )
        except InputError as exc:
            raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from exc
        results = loaded["results"]
        source_identity = loaded["source"]
    else:
        results = [item.model_dump(mode="json", exclude_none=True) for item in body.results or []]

    try:
        result = build_reports(results, variants=body.variants, lineage=body.lineage)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if source_identity is not None:
        result["input_source"] = source_identity
    return result


@router.post(
    "/reports/validate",
    response_model=ReportValidationResponse,
    summary="Validate an OKF compliance report",
)
async def validate_compliance_report(body: ValidateReportBody):
    try:
        normalized: ReportSpec = validate_report(body.report)
    except (TypeError, ValueError) as exc:
        return {"valid": False, "errors": [{"message": str(exc)}]}
    return {
        "valid": True,
        "report": normalized.model_dump(mode="json", exclude_none=True, by_alias=True),
    }


__all__ = [
    "BuildReportsBody",
    "ReportBuildResponse",
    "ReportValidationResponse",
    "ValidateReportBody",
    "router",
]
