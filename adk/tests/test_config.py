from pathlib import Path

from compliance_adk.config import ADK_DIR, PACKAGE_DIR, Settings
from compliance_core.errors import ConfigurationError


def test_extracted_package_preserves_checkout_env_location():
    root = Path(__file__).resolve().parents[2]
    assert PACKAGE_DIR == root / "packages/compliance-adk/src/compliance_adk"
    assert ADK_DIR == root / "adk"
    assert Settings.model_config["env_file"] == root / "adk/.env"


def test_code_generation_roles_use_structured_model_fallback():
    settings = Settings(structured_model="shared-model")
    assert settings.model_name_for("metric_evaluation_code") == "shared-model"
    assert settings.model_name_for("compliance_report_code") == "shared-model"


def test_code_generation_roles_require_a_configured_model():
    settings = Settings(_env_file=None)
    for role in ("metric_evaluation_code", "compliance_report_code"):
        try:
            settings.model_name_for(role)
        except ConfigurationError as exc:
            assert "STRUCTURED_MODEL" in str(exc)
        else:
            raise AssertionError(f"{role} should require a model")
