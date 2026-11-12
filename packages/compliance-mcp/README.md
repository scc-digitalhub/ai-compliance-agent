<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# compliance_mcp

An MCP stdio server exposing the compliance tool catalog, OKF resources, and the
`compliance_analysis` prompt. Host-driven analysis is the default: the host model gathers inputs,
validates its generated result, and records valid results in workspace-local `.compliance/` state.
DigitalHub tools are enabled by default. This package does not depend on Google ADK.

Install the unified distribution with its MCP dependencies and run the server:

```bash
uv sync --extra mcp
uv run --extra mcp compliance-mcp
```

Options: `--workspace PATH` selects the workspace, `--no-dh` disables DigitalHub tools, and
`--delegated` also exposes the `analyze_*` tools backed by the LiteLLM analysis engine. Delegated
mode needs LiteLLM (install the `server` extra, or `mcp` with `api`) and `STRUCTURED_MODEL`; the
server refuses to start without a configured model.

Each tool call holds a lock on the workspace state, so several hosts can share one workspace.

The `mcp` extra does not install Google ADK. The `compliance_mcp` import package is included in the
unified `ai-compliance-platform` distribution.
