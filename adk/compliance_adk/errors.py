"""Domain errors, each carrying the HTTP status the API maps it to."""
from __future__ import annotations


class ComplianceAdkError(Exception):
    status_code = 500
    code = "internal_error"


class ConfigError(ComplianceAdkError):
    code = "configuration_error"


class OutputValidationError(ComplianceAdkError):
    """The model kept returning output that fails schema or referential checks."""

    status_code = 502
    code = "invalid_model_output"

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or []


class UpstreamModelError(ComplianceAdkError):
    status_code = 502
    code = "upstream_model_error"


class UpstreamRateLimited(ComplianceAdkError):
    status_code = 429
    code = "upstream_rate_limited"


class AnalysisTimeout(ComplianceAdkError):
    status_code = 504
    code = "analysis_timeout"
