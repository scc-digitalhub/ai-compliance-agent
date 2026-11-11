"""Analysis definitions served by the API; the single source is the core analysis engine."""
from __future__ import annotations

from compliance_core.analysis_engine import (
    ANALYSES as ALL_SPECS,
    CODE_GENERATIONS,
    DATASET,
    MODEL,
    PROJECT_CONTEXT,
    AnalysisDefinition as AnalysisSpec,
    AnalysisKey,
)

CODE_GENERATION_SPECS = CODE_GENERATIONS
STRUCTURED_SPECS = (*ALL_SPECS, *CODE_GENERATION_SPECS)

__all__ = [
    "ALL_SPECS",
    "AnalysisKey",
    "AnalysisSpec",
    "CODE_GENERATION_SPECS",
    "DATASET",
    "MODEL",
    "PROJECT_CONTEXT",
    "STRUCTURED_SPECS",
]
