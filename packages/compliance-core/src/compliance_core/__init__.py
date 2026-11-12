# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Framework-neutral AI compliance contracts, knowledge, validation, and domain errors."""

from .errors import ComplianceError, ConfigurationError
from .settings import CoreSettings, get_core_settings

__all__ = ["ComplianceError", "ConfigurationError", "CoreSettings", "get_core_settings"]
