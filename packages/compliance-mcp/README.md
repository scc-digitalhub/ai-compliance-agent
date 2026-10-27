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

The `mcp` extra does not install Google ADK. The `compliance_mcp` import package is included in the
unified `ai-compliance-platform` distribution.
