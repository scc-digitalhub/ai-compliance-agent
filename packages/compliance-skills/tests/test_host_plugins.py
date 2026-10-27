from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_generated_host_integrations_are_fresh():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_host_plugins.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
