from pathlib import Path

from compliance_adk.config import ADK_DIR, PACKAGE_DIR, Settings


def test_extracted_package_preserves_checkout_env_location():
    root = Path(__file__).resolve().parents[2]
    assert PACKAGE_DIR == root / "packages/compliance-adk/src/compliance_adk"
    assert ADK_DIR == root / "adk"
    assert Settings.model_config["env_file"] == root / "adk/.env"
