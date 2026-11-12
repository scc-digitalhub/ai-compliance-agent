# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from compliance_core.knowledge import get_bundle


@pytest.fixture
def bundle():
    return get_bundle()
