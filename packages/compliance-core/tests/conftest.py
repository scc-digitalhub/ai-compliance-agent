from __future__ import annotations

import pytest

from compliance_core.knowledge import get_bundle


@pytest.fixture
def bundle():
    return get_bundle()
