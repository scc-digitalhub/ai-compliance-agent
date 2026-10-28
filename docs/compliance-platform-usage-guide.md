# AI Compliance Platform: Architecture and Usage Guide

This guide covers the framework-neutral core, the standalone API, the MCP server used by coding
agents, and the optional Google ADK integration. The Python components ship in one distribution,
`ai-compliance-platform`; source and import packages remain separated by responsibility.

## Choose a component

| Component | Use it when | LLM and persistence |
|---|---|---|
| `compliance_core` | Building a Python integration or using the contracts, catalog, knowledge reader, validators, and state abstractions directly | No agent runtime required. Choose a state store and engine in your application. |
| `compliance_skills` | Giving an agent a portable, repeatable compliance workflow | Skills are Markdown instructions; a host must expose the named tools. |
| `compliance_mcp` | Integrating with Copilot/VS Code, Claude Code, OpenCode, or another MCP client | Host-driven analysis is the default and uses the host model. Results are saved to workspace-local `.compliance/state.json`. |
| `compliance_api` | Calling compliance analysis from a service or script over HTTP | Uses the LiteLLM engine. Requires a configured model/provider. Does not persist analysis state. |
| `compliance_dh` | Connecting core tools to DigitalHub entities and specification extensions | DigitalHub SDK adapter; no Google ADK dependency. Enabled by default in MCP. |
| `compliance_adk` | Running the existing Google ADK agents or `adk web` | Install the `adk` extra and configure a model/provider. |

The API and MCP extras do not install Google ADK. The `server` extra combines the API and MCP
dependencies without ADK; the `adk` extra adds Google ADK. The distribution is not yet published,
so commands below assume a checkout of this repository.

## Install and configure

Install only the dependencies needed by the integration you plan to use:

```bash
uv sync --extra api       # REST API
uv sync --extra mcp       # host-driven MCP server
uv sync --extra server    # API and MCP server
uv sync --extra adk       # Google ADK integration
uv sync --extra dev       # tests and all adapters
```

Set secrets through the process environment or your organization's secret manager; do not commit
tokens or provider keys. MCP uses the host's model for host-driven analysis, so the MCP process does
not need separate model credentials. DigitalHub tools are enabled by default. To use them, provide
the DigitalHub environment settings supported by the installed SDK, including `DHCORE_ENDPOINT`,
an access credential, and `DH_PROJECT`.

The MCP workspace defaults to the process working directory. Set `COMPLIANCE_WORKSPACE` if the
agent should write analysis state to a different project directory. State files can contain
workspace or dataset information; inspect them locally and do not commit or share them without
review.

## Standalone REST API

The API accepts project, dataset, and model inputs directly. It runs its own LiteLLM tool-calling
engine, independent of MCP hosts and Google ADK.

1. Install the API extra:

   ```bash
   uv sync --extra api
   ```

2. Configure a LiteLLM model ID and provider credentials. For example, with a LiteLLM gateway:

   ```bash
   export STRUCTURED_MODEL="your-litellm-model-id"
   export LLM_API_BASE="http://localhost:4000"
   export LLM_API_KEY="set-this-through-your-secret-manager"
   ```

   Alternatively, configure the provider's standard environment variables. Per-analysis model
   overrides, authentication, CORS, and request limits are listed in
   [`packages/compliance-api/.env.example`](../packages/compliance-api/.env.example).

3. Start the service:

   ```bash
   uv run --extra api compliance-api
   ```

The service listens on `127.0.0.1:8100`. `/health` is a liveness check, `/ready` checks that the
knowledge bundle is loaded, and `/docs` exposes the OpenAPI interface. If `API_KEYS` is configured,
send one of the configured keys in the `X-API-Key` header. The API creates a request ID and returns
it in both the response header and metadata/error body.

### Project context request

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8100/v1/compliance/context \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "eu-credit-risk-demo",
    "domain": {"domain": "finance", "subdomain": "consumer lending"},
    "ai_task": "CLASSIFICATION",
    "goal": "Estimate repayment risk to support a human-reviewed loan decision.",
    "purpose": "Provide a risk signal to loan officers.",
    "audience": "Loan officers",
    "geography": ["EU"],
    "deployment": "CLOUD",
    "environment": "PRODUCTION"
  }'
```

### Dataset and model requests

`POST /v1/compliance/datasets` expects a `dataset` object. A prior project and project context can
be supplied to reuse their requirement IDs and context:

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8100/v1/compliance/datasets \
  -H 'Content-Type: application/json' \
  -d '{
    "dataset": {
      "name": "loan-training-v1",
      "description": "Historical loan applications and repayment outcomes.",
      "scope": "TRAINING",
      "domain": "finance",
      "sensitivity": "PII",
      "n_records": 100000,
      "schema_fields": [
        {"name": "age", "dtype": "integer", "sensitivity": "PII"},
        {"name": "income", "dtype": "number", "sensitivity": "PII"},
        {"name": "repaid", "dtype": "boolean"}
      ],
      "known_protected_attributes": ["age"]
    }
  }'
```

`POST /v1/compliance/models` expects a `model` object and optionally accepts the project context and
dataset analyses:

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8100/v1/compliance/models \
  -H 'Content-Type: application/json' \
  -d '{
    "model": {
      "name": "credit-risk-v1",
      "description": "Predicts probability of loan repayment.",
      "ai_task": "CLASSIFICATION",
      "domain": "finance",
      "framework": "SKLEARN",
      "output_type": "BINARY_CLASSIFICATION",
      "produces_probabilities": true,
      "trained_on_sensitive_data": true
    }
  }'
```

All three endpoints return an envelope with `data` and `meta`. `data` is the normalized result for
the requested analysis; `meta` includes the request ID, model, number of attempts, grounding paths,
assumptions, warnings, latency, and token usage. A typical response excerpt is:

```json
{
  "data": {
    "geography": ["EU"],
    "risk_classification": {
      "risk_level": "HIGH",
      "classification_status": "PRELIMINARY",
      "rationale": "Illustrative only; the actual result depends on the submitted facts and OKF evidence."
    }
  },
  "meta": {
    "request_id": "generated-request-id",
    "agent": "project_context_agent",
    "model": "configured-model-id",
    "grounding": ["catalog/regulatory-refs/..."],
    "attempts": 1,
    "warnings": []
  }
}
```

This is an abbreviated shape, not a complete response or guaranteed risk assessment. The full
`data` object follows the relevant schema. Compliance analysis is decision support, not legal
advice; a `PRELIMINARY` classification requires review by qualified people.

### Verify API execution

- Confirm `GET /health` returns `{"status":"ok"}` and `GET /ready` returns `{"status":"ready"}`.
- Confirm the analysis response has a request ID and a non-empty `meta.grounding` list for an input
  that calls knowledge tools. Grounding paths should correspond to the returned requirements,
  regulations, or metrics.
- Inspect `meta.attempts`, `meta.warnings`, `meta.usage`, and the normalized `data`. Validation
  failures are retried up to `MAX_VALIDATION_RETRIES`; request/schema errors return 422 and provider
  failures return structured error responses.
- The REST response does not expose a full internal tool-call trace. To confirm each named tool call,
  use an MCP host's tool-call transcript or a test/instrumented engine. Do not infer tool use only
  from the model's narrative.

## Coding-agent hosts through MCP

The MCP server exposes core knowledge, schema, validation, result-recording, entity, and
DigitalHub specification tools. Host-driven analysis is the default: the host model reads the
portable skill, calls the tools, produces the structured result, and asks the core to validate and
record it. No separate LLM key is needed by MCP. The default `FileStateStore` writes to
`.compliance/state.json` in the selected workspace.

Install the extra once for command-line testing:

```bash
uv sync --extra mcp
uv run --extra mcp compliance-mcp
```

For an MCP host, configure the host to launch the server on demand. The generated host manifests use
`compliance-mcp` directly, which works when the executable is on the host's `PATH`. Since this
distribution is not published yet, a source checkout can launch it with `uv` instead. Replace
`/absolute/path/to/ai-compliance-agent` with the checkout path. Keep the MCP process environment
configured with `DHCORE_ENDPOINT`, the DigitalHub credential, `DH_PROJECT`, and optionally
`COMPLIANCE_WORKSPACE`.

### VS Code / GitHub Copilot

1. Copy `integrations/copilot/.github/skills/` into the repository where you use Copilot as
   `.github/skills/`.
2. Copy `integrations/copilot/.vscode/mcp.json` to that repository's `.vscode/mcp.json`.
3. For a local checkout, set the server command to `uv` and its arguments to:

   ```json
   [
     "run",
     "--project",
     "/absolute/path/to/ai-compliance-agent",
     "--extra",
     "mcp",
     "compliance-mcp"
   ]
   ```

4. Ensure the Copilot model is enabled for tools/MCP, then ask it to use the `project-context`,
   `dataset-analysis`, or `model-analysis` skill.

### Claude Code

Start Claude Code with the checked-in plugin:

```bash
claude --plugin-dir /absolute/path/to/ai-compliance-agent/integrations/claude-code
```

The plugin contains the portable skills and an MCP server entry in
`integrations/claude-code/.claude-plugin/plugin.json`. For a checkout where `compliance-mcp` is
not on `PATH`, change that server entry to:

```json
{
  "command": "uv",
  "args": [
    "run",
    "--project",
    "/absolute/path/to/ai-compliance-agent",
    "--extra",
    "mcp",
    "compliance-mcp"
  ]
}
```

Use the plugin's project/dataset/model skills in the conversation. Confirm Claude Code is showing
MCP tool calls; a final answer without the validation and record calls is not sufficient evidence.

### OpenCode

1. Copy `integrations/opencode/.opencode/skills/` into the target workspace's `.opencode/skills/`.
2. Merge the `mcp` block in `integrations/opencode/opencode.json` into the workspace OpenCode
   configuration. For a local checkout, use:

   ```json
   {
     "type": "local",
     "command": [
       "uv",
       "run",
       "--project",
       "/absolute/path/to/ai-compliance-agent",
       "--extra",
       "mcp",
       "compliance-mcp"
     ],
     "enabled": true
   }
   ```

3. Restart or reload OpenCode so it discovers the skills and MCP tools.

### Example host conversation and expected tool evidence

For the full flow, configure DigitalHub credentials first. The skills check whether a specification
already exists before analysis. If the check returns `not_found`, the new analysis can proceed. A
different DigitalHub error must be reported and resolved rather than silently ignored.

**User**

> Analyze `eu-credit-risk-demo`: a cloud-deployed EU system that classifies consumer loan
> applications and gives loan officers a repayment-risk signal. Use the compliance tools, validate
> and record the result in this workspace. Do not save a specification to DigitalHub.

**Expected tool-call sequence (abbreviated)**

1. `get_compliance_specification(kind="project", entity="eu-credit-risk-demo")` checks for an
   existing specification. If none exists, the expected result is:

   ```json
   {
     "error": "No compliance specification is stored for project 'eu-credit-risk-demo'",
     "code": "not_found"
   }
   ```

2. Knowledge calls such as `get_regulatory_refs`, `get_requirements`, `get_groups`,
   `get_attributes`, and `get_misuse_scenarios` retrieve relevant catalog records. The agent should
   copy IDs and enum values from these results rather than inventing them.
3. `get_output_schema(kind="project")` supplies the exact result shape.
4. The host generates a candidate and calls
   `validate_project_context(request=<original project>, output=<candidate>)`. A successful
   response has `"valid": true`, `"errors": []`, and a `"normalized"` result. If invalid, the host
   corrects the candidate and validates again.
5. `record_compliance_analysis(kind="project", request=<original project>, output=<candidate>)`
   validates again and records it in the workspace. Success includes `"valid": true` and
   `"stored": true`.
6. The final host response follows the skill's output contract: a JSON object with `result` and
   `assumptions`. An illustrative assessment might be `HIGH` with status `PRELIMINARY` if the
   retrieved evidence supports it; exact regulations, IDs, classification, and rationale must come
   from the run, not this example.

The request explicitly forbids DigitalHub persistence, so the agent must **not** call
`save_compliance_specification`. `record_compliance_analysis` writes locally; saving to DigitalHub
is a separate action requiring user authorization.

### Verify MCP tool use and stored state

1. In the host's MCP/tool-call view, confirm the calls above are present. At minimum, verify the
   schema call, the appropriate `validate_*` call with a successful response, and
   `record_compliance_analysis` with `"stored": true`. Tool availability alone does not prove that
   the agent used the tools.
2. Inspect the state file in the selected workspace. For the project example, the recorded context
   is under `analysis_project_context`:

   ```bash
   python -c 'import json; s=json.load(open(".compliance/state.json")); print(s["analysis_project_context"]["risk_classification"])'
   ```

   If `COMPLIANCE_WORKSPACE` is set, inspect its `.compliance/state.json` instead. Do not commit this
   file by default; it may contain sensitive analysis inputs.
3. Check that the final answer's references and IDs match the knowledge-tool results and that
   validation warnings were addressed or disclosed. A plausible-sounding final answer without the
   calls and successful validation is not a successful tool-driven run.
4. To check that generated skills have not drifted from their canonical source, run:

   ```bash
   python scripts/sync_host_plugins.py --check
   ```

## Google ADK integration

The `adk` extra adds Google ADK while using the same core contracts, skills, DigitalHub adapters,
and knowledge data. It is an alternative runtime, not a dependency of the standalone API or MCP
server.

```bash
uv sync --extra adk
cp adk/.env.example adk/.env
# Set STRUCTURED_MODEL, COORDINATOR_MODEL, and provider credentials in adk/.env.
uv run --project . --extra adk --directory adk adk web --port 8000
```

Open `http://127.0.0.1:8000` and select the coordinator or structured project, dataset, and model
agents. As with other agent runtimes, inspect the agent's tool-call events and confirm validation
succeeds before treating an output as complete.

## Core and extension points

- Contracts and request/result models: `compliance_core.contracts`.
- OKF reader and packaged knowledge: `compliance_core.knowledge`; override the bundle with
  `OKF_PATH` when appropriate.
- Canonical tool definitions: `compliance_core.tool_catalog.TOOL_CATALOG`.
- Output schemas and semantic checks: `compliance_core.validation_tools`.
- State interfaces and implementations: `compliance_core.state`, including
  `InMemoryStateStore`, `MappingStateStore`, and `FileStateStore`.
- DigitalHub ports/adapters: `compliance_core.ports` and `compliance_dh`.
- Portable skill sources: `packages/compliance-skills/src/compliance_skills/skills/`; generated
  host copies live under `integrations/`.

For example, a Python extension can inspect the framework-neutral tools and obtain the project
output schema without importing Google ADK:

```python
from compliance_core.tool_catalog import TOOL_CATALOG
from compliance_core.validation_tools import get_output_schema

print(sorted(TOOL_CATALOG))
project_schema = get_output_schema("project")
```

The core deliberately does not choose an LLM, host, or persistence destination. Adapters provide
those dependencies, while the shared contracts and validators preserve consistent input/output
behavior.
