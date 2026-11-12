<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# compliance_api

Standalone FastAPI service for project, dataset, and model compliance analysis. It uses the
framework-neutral core and LiteLLM engine and does not import Google ADK.

Install the unified distribution with its API extra, then run `compliance-api`. Configure
`STRUCTURED_MODEL` (or per-analysis model overrides) and provider credentials in the process
environment. The service stores no analysis state; workspace-local state remains the MCP host's
responsibility.

The `api` extra does not install Google ADK. The `compliance_api` import package is included in the
unified `ai-compliance-platform` distribution.
