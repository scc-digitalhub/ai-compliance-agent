# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Single source of the framework version: the installed distribution metadata."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

DISTRIBUTION = "ai-compliance-platform"


def framework_version() -> str:
    try:
        return version(DISTRIBUTION)
    except PackageNotFoundError:
        return "0+unknown"


__version__ = framework_version()

__all__ = ["DISTRIBUTION", "__version__", "framework_version"]
