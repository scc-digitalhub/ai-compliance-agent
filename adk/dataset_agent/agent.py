# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from compliance_adk.agents.specs import DATASET
from compliance_adk.agents.structured import build_structured_agent

root_agent = build_structured_agent(DATASET)
