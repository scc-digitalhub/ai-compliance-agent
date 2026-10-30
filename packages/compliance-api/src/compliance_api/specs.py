"""Analysis definitions served by the API; the single source is the core analysis engine."""
from __future__ import annotations

from compliance_core.analysis_engine import (
    ANALYSES as ALL_SPECS,
    DATASET,
    MODEL,
    PROJECT_CONTEXT,
    AnalysisDefinition as AnalysisSpec,
    AnalysisKey,
)

__all__ = ["ALL_SPECS", "AnalysisKey", "AnalysisSpec", "DATASET", "MODEL", "PROJECT_CONTEXT"]
