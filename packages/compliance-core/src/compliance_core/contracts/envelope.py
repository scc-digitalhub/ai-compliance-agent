# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Response envelope returned by the API and by the coordinator's tools."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AnalysisMeta(BaseModel):
    request_id: str
    agent: str
    model: str
    okf_version: str = Field(description="Content hash of the OKF bundle used for grounding")
    latency_ms: int
    attempts: int = Field(description="Model invocations, including validation retries")
    grounding: list[str] = Field(default_factory=list, description="OKF concept paths consulted")
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)


class AnalysisResponse(BaseModel, Generic[T]):
    data: T
    meta: AnalysisMeta


class ErrorResponse(BaseModel):
    detail: str
    code: str
    request_id: str | None = None
