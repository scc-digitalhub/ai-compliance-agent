# AI Compliance Framework

Reusable AI compliance tools and analysis agents. The framework uses the packaged [Open Knowledge
Framework (OKF)](packages/compliance-core/src/compliance_core/data/okf/) catalog to produce typed
compliance context for projects and compliance objectives for datasets and models. It includes a
framework-neutral core, MCP and REST adapters for host-driven/delegated analysis, and a separate
Google ADK integration. This repository no longer contains the
earlier `src/compliance_agent` LangChain implementation.

## Architecture

- `packages/compliance-core/src/compliance_core/` contains reusable contracts, validation,
  knowledge access, state stores, service logic, ports, and the canonical tool catalog. Core
  imports do not require Google ADK.
- `packages/compliance-dh/src/compliance_dh/` provides DigitalHub repositories and SDK operations
  without importing ADK.
- `packages/compliance-skills/src/compliance_skills/` packages the canonical portable coordinator
  definition in `agents/` together with its procedures in `skills/`.
- `packages/compliance-api/src/compliance_api/` provides the standalone FastAPI/LiteLLM service
  without Google ADK.
- `packages/compliance-mcp/src/compliance_mcp/` adapts the catalog to MCP tools, resources, and
  prompts. The MCP distribution has no Google ADK dependency.
- `packages/compliance-protocols/src/compliance_protocols/` exposes the ADK coordinator over
  Agent Client Protocol (stdio) and A2A 1.0 (authenticated HTTP/SSE).
- `packages/compliance-adk/src/compliance_adk/` provides the shared Google ADK implementation:
  agent builders, model settings, skill/tool adapters, and structured runners with output validation
  and grounding metadata. Both the ADK launchers and ACP/A2A adapters import this package.
- `integrations/` contains generated Copilot/VS Code, Claude Code, and OpenCode bundles. The
  generated agents and skill copies are synchronized from `compliance-skills`.
- `adk/{compliance_agent,project_context_agent,dataset_agent,model_agent}/` provides entry points for `adk web`.

The `compliance_adk` import namespace is unchanged. `adk/` retains launchers, local configuration,
tests, and manual scenarios; reusable ADK code lives under `packages/`. Source checkouts continue
to load ADK settings from `adk/.env`.

All Python components are shipped in one distribution, `ai-compliance-platform`. The component
directories under `packages/` and `adk/` remain separate source and import packages, but are no
longer independently installable distributions. Optional extras select runtime dependencies:
`api`, `mcp`, `adk`, or `server` (API and MCP without Google ADK). For example,
`pip install "ai-compliance-platform[server]"` installs the server adapters without Google ADK.
The optional `acp` and `a2a` extras add protocol SDKs, ADK and SQLite persistence.

The structured API accepts project, dataset, and model definitions directly. Dataset and model requests
can include project context from an earlier analysis. Responses have a `data` object and `meta` with
assumptions, warnings, OKF paths consulted, token usage, and the bundle version. Results are decision
support, not legal advice.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- An LLM provider supported by LiteLLM is required for the ADK integration and standalone REST API.
  The default host-driven MCP workflow uses the host's model and does not require separate LLM
  credentials.
- DigitalHub credentials are needed only when using DigitalHub entity lookup or specification
  operations; DigitalHub integration is enabled by default.

## Google ADK setup

This installs the unified project with the optional Google ADK runtime dependencies:
```bash
uv sync --extra adk
cp adk/.env.example adk/.env
```

Edit `adk/.env` and set `STRUCTURED_MODEL` and `COORDINATOR_MODEL` to LiteLLM model IDs. Configure
provider credentials using the variables expected by your LiteLLM provider. For a gateway, set
`LLM_API_BASE`, and optionally `LLM_API_KEY`. Do not commit `.env` or real credentials.

| Variable | Purpose |
|---|---|
| `STRUCTURED_MODEL` | Default model for project, dataset, and model analysis agents |
| `COORDINATOR_MODEL` | Model for interactive compliance questions and reasoning |
| `PROJECT_CONTEXT_AGENT_MODEL_NAME`, `DATA_ANALYSIS_AGENT_MODEL_NAME`, `MODEL_ANALYSIS_AGENT_MODEL_NAME`, `ROOT_AGENT_MODEL_NAME` | Optional per-agent overrides and legacy names |
| `LLM_API_BASE`, `LLM_API_KEY` | Optional LiteLLM gateway URL and key |
| `MAX_CONCURRENCY`, `REQUEST_TIMEOUT_S`, `MAX_VALIDATION_RETRIES` | ADK runner concurrency, timeout, and validation retry limits |
| `OKF_PATH` | Optional OKF bundle path; defaults to the packaged core bundle |
| `COMPLIANCE_WORKSPACE` | Optional default MCP workspace path; defaults to the process working directory |

The optional `STRUCTURED_THINKING_BUDGET` and `COORDINATOR_THINKING_BUDGET` settings apply only to
Gemini models. See [`adk/.env.example`](adk/.env.example) for the complete configuration list.

## MCP host integration

The MCP adapter defaults to host-driven analysis: the host model gathers inputs, uses the OKF tools,
requests the output schema, validates the generated result, and records valid results in the current
workspace's `.compliance/state.json`. DigitalHub entity lookup and specification tools are enabled
by default; configure DigitalHub credentials in the environment. Delegated internal LLM analysis is
opt-in.

DigitalHub project selection is explicit, not environment-based. For specification and entity
operations, name the project in the request (for example, "retrieve dataset applications-2024 in
project credit") or refer to a project already established in the conversation. Dataset/model tools
accept a `project` argument; a full `store://` key also identifies its project. For project
specifications, `entity` is the project identifier. The agent asks when the project is missing or
ambiguous rather than guessing a default.

Install the unified distribution with MCP dependencies and run the stdio server from the repository:

```bash
uv sync --extra mcp
uv run --extra mcp compliance-mcp
```

Host bundles include a native compliance assistant agent, copies of the portable skills and
host-specific MCP configuration. The ADK coordinator and all three host agents share the
[portable definition](packages/compliance-skills/src/compliance_skills/agents/compliance-assistant.md).
Install the MCP extra first (as above), then use the relevant bundle. The host process must be able to resolve
the `compliance-mcp` executable through its `PATH`; for a source checkout, configure the host to
launch the command through `uv run --project <repository> --extra mcp compliance-mcp`.
Replace `<repository>` with the absolute path to this checkout.

- **Copilot/VS Code:** copy `integrations/copilot/.github/skills/` into the workspace's
  `.github/skills/`, copy `integrations/copilot/.github/agents/` into `.github/agents/`, and merge
  `integrations/copilot/.vscode/mcp.json` into `.vscode/mcp.json`. Select `compliance-assistant`
  in the agent picker.
- **Claude Code:** load `integrations/claude-code/` with `claude --plugin-dir` or install it as a
  plugin. Its manifest exposes the `compliance-mcp` executable, bundled skills and
  `ai-compliance:compliance-assistant` agent. Ask Claude to delegate to that agent; it preloads
  the six plugin skills and inherits the plugin's MCP tools.
- **OpenCode:** copy `integrations/opencode/.opencode/skills/` and
  `integrations/opencode/.opencode/agents/` into the workspace's `.opencode/` directory, then merge
  `integrations/opencode/opencode.json` into the workspace OpenCode configuration. Switch to
  the `compliance-assistant` primary agent.

Each host launches the MCP server from its process environment. Set DigitalHub credentials there as
required; no credentials are stored in the bundles. Analysis state remains in the active workspace's
`.compliance/` directory. Regenerate or verify checked-in bundles with
`python scripts/sync_host_plugins.py` and `python scripts/sync_host_plugins.py --check`.

The unified distribution builds as one wheel or source distribution and is not yet published to a
package index. The ADK extra installs Google ADK; the API, MCP, and server extras do not.

## ACP and A2A agent exposure

Use `uv sync --extra acp --extra a2a` to install the optional protocol adapters, then configure the
coordinator model and provider credentials as in the ADK setup. Unlike host-driven MCP, these
adapters run their own model.

- `compliance-acp`: Agent Client Protocol over stdio, with persistent conversations, history replay,
  text/tool updates, cancellation and per-write editor permissions.
- `compliance-a2a`: A2A 1.0 JSON-RPC/HTTP and SSE, with Agent Card discovery, durable tasks,
  input-required clarification, validated JSON artifacts and deferred per-write approval.

DigitalHub operations require an explicit user-selected project and an authorization allowlist
(`COMPLIANCE_PROTOCOL_ALLOWED_PROJECTS`, a JSON array). Writes default to disabled. A2A additionally
requires `COMPLIANCE_PROTOCOL_BEARER_TOKEN` (at least 32 characters). A conversation cannot switch
DigitalHub projects; start a new one instead.

This is a single-tenant, single-worker deployment baseline. See the
[protocol setup, configuration, client examples and deployment boundaries](packages/compliance-protocols/README.md).

## Run the standalone API

Install the unified distribution with API dependencies, then run the service:

```bash
uv sync --extra api
uv run --extra api compliance-api
```

Configure `STRUCTURED_MODEL` and provider credentials (or `LLM_API_BASE` and `LLM_API_KEY` for a
LiteLLM gateway) in the API process environment. Optional API keys, CORS, and request limits are
documented in [`packages/compliance-api/.env.example`](packages/compliance-api/.env.example). This
service uses LiteLLM and does not install Google ADK.

- OpenAPI documentation: <http://127.0.0.1:8100/docs>
- Liveness: `GET /health`
- Readiness: `GET /ready`
- Project context: `POST /v1/compliance/context`
- Dataset compliance: `POST /v1/compliance/datasets`
- Model compliance: `POST /v1/compliance/models`

Example project request:

```bash
curl -X POST http://127.0.0.1:8100/v1/compliance/context \
	-H 'Content-Type: application/json' \
	-d '{
		"name": "Credit scoring",
		"domain": "finance",
		"ai_task": "CLASSIFICATION",
		"goal": "Assess creditworthiness of loan applicants",
		"geography": ["EU"]
	}'
```

If `API_KEYS` is configured, include
`-H 'X-API-Key: your-key'` in the request. Invalid request
payloads return 422; upstream, timeout, and repeatedly invalid model output errors return structured
error responses with request IDs.

## Interactive Development UI

Install the ADK package separately when using Google ADK:

```bash
uv run --project . --extra adk --directory adk adk web --port 8000
```

The ADK UI discovers the coordinator and the three structured agent entry points. It is for development.
A React console is not included in this checkout; client
applications can integrate with the versioned endpoints.

## Tests

Tests use scripted models and fakes, so they do not require provider credentials or make real LLM
calls. After syncing all workspace packages:

```bash
uv sync --extra dev
uv run pytest
```
