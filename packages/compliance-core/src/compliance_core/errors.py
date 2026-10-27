"""Framework-neutral domain errors with transport-agnostic status metadata."""
from __future__ import annotations


class ComplianceError(Exception):
    status_code = 500
    code = "internal_error"


class ConfigurationError(ComplianceError):
    code = "configuration_error"


class OutputValidationError(ComplianceError):
    """The model kept returning output that fails schema or referential checks."""

    status_code = 502
    code = "invalid_model_output"

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or []


class UpstreamModelError(ComplianceError):
    status_code = 502
    code = "upstream_model_error"


class UpstreamRateLimited(ComplianceError):
    status_code = 429
    code = "upstream_rate_limited"


class AnalysisTimeout(ComplianceError):
    status_code = 504
    code = "analysis_timeout"


__all__ = [
    "AnalysisTimeout",
    "ComplianceError",
    "ConfigurationError",
    "OutputValidationError",
    "UpstreamModelError",
    "UpstreamRateLimited",
]
