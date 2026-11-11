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
| `compliance_api` | Calling analysis, code generation or deterministic reporting over HTTP | Analysis/code generation use LiteLLM; report building/validation need no model. No persistent analysis workspace or implicit report publication. |
| `compliance_dh` | Connecting core tools to DigitalHub entities and specification/report extensions | DigitalHub SDK adapter; no Google ADK dependency. Enabled by default in MCP. |
| `compliance_adk` | Running the existing Google ADK agents or `adk web` | Install the `adk` extra and configure a model/provider. |
| `compliance_protocols` | Exposing the ADK coordinator over ACP stdio or A2A HTTP/SSE | Install `acp`/`a2a`; own model, durable conversations and approval-gated writes. |

The API and MCP extras do not install Google ADK. The `server` extra combines the API and MCP
dependencies without ADK; the `adk` extra adds Google ADK. Commands below use a local checkout
and do not require a published package. Run them from the checkout root unless a command specifies
an absolute `--project` path. Install/configuration instructions are below; scenarios are examples
of requests after the relevant host or service has been configured.

## End-to-end scenarios for the compliance assistant

The following prompts work with the portable assistant in MCP hosts and with the ADK/ACP/A2A
coordinator. Replace example project/entity identifiers with your own. The assistant uses the
matching skill, retrieves existing specifications before re-analysis, and asks for missing inputs.
Analysis selects objectives; it does not measure a dataset or certify legal compliance.

### 1. Analyse a project, then its data and model

Start by establishing the project:

> In DigitalHub project `credit`, analyse our consumer-loan decision-support system for EU use.
> Its classification model estimates repayment risk for loan officers; people review the final
> decision. Build the project compliance context, explaining risk classification, applicable
> requirements, protected groups, and oversight. Do not save it yet.

If a specification already exists, review it and explicitly request re-analysis if needed. Then:

> Save the reviewed project compliance specification in project `credit`.

Analyse a registered dataset with the established project context:

> Retrieve dataitem `loan-training-v1` in project `credit` and analyse its data compliance.
> It is TRAINING data containing age, income and repayment labels. Reuse the project context;
> identify protected attributes and propose data-quality, fairness and privacy objectives.
> Explain the suggested thresholds and assumptions. Do not compute any metric yet.

For an unregistered dataset, provide its scope, schema, sensitivity, description and any known
protected attributes directly instead of asking for a DigitalHub lookup.

Analyse the model:

> Retrieve model `loan-scorer-v1` in project `credit`. It performs CLASSIFICATION to predict
> repayment risk. Analyse its compliance using the project context and the dataset analysis.
> Propose appropriate accuracy, fairness, calibration and robustness objectives.

Review thresholds before asking to save each entity's specification. Saving an analysis changes
its compliance specification, not its evaluation evidence. Existing specifications are never
re-run or overwritten merely because you request an evaluation.

### 2. Generate a dataset evaluator without running it

> For dataitem `loan-training-v1` in project `credit`, generate a Python evaluator for the
> Dataset Completeness objective in its reviewed specification. The input is an in-memory pandas
> DataFrame loaded by our pipeline. Assess only columns `age`, `income` and `repaid`, use their
> overall non-null fraction, and compare it with the objective's existing threshold.
> Return the function, input/result contract, required dependencies, invocation example and
> catalog grounding. Do not execute it and do not attach a report.

The evaluator takes the assessed entity or its explicitly documented in-memory representation.
It returns a structured measurement and objective assessment, not just console output.
Dependencies belong to your external evaluation environment; the assistant does not install or
execute them. Inspect generated source before running it. Static validation checks structure and
bindings, not mathematical correctness or safety of arbitrary Python.

### 3. Generate a model evaluator with explicit evaluation inputs

> Generate Python evaluation code for the accuracy and equalized-odds objectives of
> `loan-scorer-v1` in project `credit`. Our external pipeline passes the model, a held-out feature
> DataFrame, true labels and the `age_group` sensitive-feature series. Use the model's `predict`
> method, binary labels 0/1 with positive label 1, and the reviewed objective conditions.
> Return per-objective functions and their result schemas, without executing or publishing.

Model metadata alone cannot establish accuracy or fairness. If labels, evaluation data, protected
group bindings or a multi-output metric selector are missing, the assistant returns required
inputs (`needs_input`) or an explicit unsupported reason rather than inventing a score.

### 4. Generate standalone reporting code for existing results

> Our pipeline already computes the objective/metric results for model `loan-scorer-v1` in
> project `credit`. Generate Python reporting code that reads `results.json`, validates metric IDs,
> timestamps and objective snapshots, builds separate EVALUATION and TEST report specifications,
> and attaches them as named compliance-report extensions on this model. Use run name
> `validation-2026-11-11`; preserve prior reports. Include a no-write preview and an explicit
> publish invocation, runtime dependencies, and structured success/failure output.

For a shell-oriented pipeline:

> Generate a shell reporting wrapper instead, using the packaged compliance-report CLI and
> the same result contract. Quote all file paths and identifiers. Credentials must come from the
> runtime's DigitalHub SDK configuration, never from literals in the generated script.

Reporting code uses shared deterministic report/condition helpers. It can consume results from
another evaluator; generating evaluator code is not a prerequisite. Unsupported languages or
ambiguous input formats require clarification rather than a runnable-looking placeholder.

### 5. Generate one executable for evaluation and publication

> Generate one Python executable for `loan-scorer-v1` in project `credit` that evaluates the
> selected accuracy and fairness objectives, gathers their results, constructs the report
> specifications and attaches them to this model. Use our explicit held-out-data/label/group
> bindings from above. Stage and validate all reports before publication. Provide preview and
> publish invocations and preserve unrelated extensions. I will review and run it outside the
> assistant.

This workflow does not require returning to the assistant between evaluation and reporting.
The per-metric functions compute; a separate generated entry point assembles and publishes.
A compliance `FAIL` can be a successfully published outcome; an execution failure is different.
An operational computation/validation failure must not publish partial success evidence.

One executable invocation is not a distributed transaction. Report extensions can be staged
into one entity update, but the current DigitalHub SDK does not guarantee conditional atomic
publication. Requests for strict transaction guarantees must be rejected when unsupported.
Do not assume rollback across model execution, files, multiple entities or remote side effects.
Stable run/report names and conflict checks support safe retries; review uncertain write outcomes.

### 6. Have the assistant build and attach a report from a file or reference

> Read `evaluation/results.json` in this workspace. These are externally computed results for
> `loan-scorer-v1` in project `credit`. Build an EVALUATION report and a separate TEST report
> against the reviewed objective snapshots. Show source provenance and validation issues first;
> do not save until I approve.

Then:

> Attach the reviewed reports to `loan-scorer-v1` in project `credit`, using the named run
> `validation-2026-11-11`. Do not replace any differently named report.

MCP and standalone ADK support regular JSON files relative to their configured workspace, up to
1,000,000 bytes; absolute paths, symlinks and URLs are rejected. The default REST server requires
inline results; source references need an authorized `evaluation_input_reader` injected into
`create_app`. ACP/A2A do not transfer editor files; absent an injected reader, their shared loader
accepts local files within the agent process's working directory (2 MiB limit), not the client's
session directory. For other artifact/resource schemes, an embedding application must inject
an authorized reader; checked-in host bundles do not provide one. Provide an
explicit field mapping for noncanonical results; include metric IDs, actual computation timestamps,
objective references/snapshots and target identity. A filename is not evidence of those facts.
Missing or inaccessible content, unsupported formats and ambiguous mappings are reported explicitly.
Source identity and content fingerprints are retained; generated code is not required in this flavour.

### Report and permission boundaries

- `EVALUATION` records metric measurements. `TEST` records comparisons with objective conditions,
  with `PASS`, `FAIL`, `INCONCLUSIVE` or `ERROR`. They are separate report specifications.
- Generating a publishing executable does not execute it or approve an immediate agent-side write.
  External execution uses your runtime credentials and declared publication policy.
- Agent-side DigitalHub writes remain explicit. ACP/A2A deployments must enable writes and approve
  the exact prepared operation; pending approval is not a successful save.
- Retrieve/review a conflicting named report before confirming replacement. Do not overwrite
  evidence just to make a retry succeed.
- Host-driven code generation uses the host model. Delegated generation is opt-in. Deterministic
  report construction needs neither a model nor generated-source execution.

### Canonical result file and reporting CLI

Save this illustrative result array as `results.json`, replacing the objective snapshot, reference,
target and measured value with your actual reviewed specification and external measurement.
The timestamp is when the metric was computed, not when the report was requested:

```json
[
  {
    "project": "credit",
    "entity": "loan-scorer-v1",
    "objective_ref": "objective::accuracy-check",
    "objective": {
      "name": "Accuracy at least 0.9",
      "metric": {
        "id": "metric-accuracy",
        "name": "Classification Accuracy",
        "kind": "PRIMITIVE",
        "scale": "RATIO"
      },
      "condition": {"threshold": {"operator": "GEQ", "value": 0.9}},
      "priority": "MANDATORY",
      "severity": "HIGH",
      "requirements": []
    },
    "metric_result": {
      "metric": {
        "id": "metric-accuracy",
        "name": "Classification Accuracy",
        "kind": "PRIMITIVE",
        "scale": "RATIO"
      },
      "value": 0.93,
      "computed_at": "2026-11-11T08:00:00Z"
    },
    "provenance": {"producer": "external-validation-pipeline", "run": "validation-2026-11-11"}
  }
]
```

An objective reference must identify the actual supplied snapshot. Preserve authoritative IDs when
available; framework-generated snapshot references are not catalog IDs. Add result entries for
other metrics/objectives rather than combining multiple values under an arbitrary scalar condition.

Install the base project with `uv sync` first. Preview needs no model or DigitalHub connection:

```bash
uv run compliance-report preview \
  --results results.json --project credit --entity-kind model --entity loan-scorer-v1 \
  --variants EVALUATION,TEST \
  --report-name EVALUATION=validation-2026-11-11-measurements \
  --report-name TEST=validation-2026-11-11-checks
```

After review, use the same arguments with `publish`:

```bash
uv run --extra mcp compliance-report publish \
  --results results.json --project credit --entity-kind model --entity loan-scorer-v1 \
  --variants EVALUATION,TEST \
  --report-name EVALUATION=validation-2026-11-11-measurements \
  --report-name TEST=validation-2026-11-11-checks
```

Supply DigitalHub credentials through the SDK's runtime configuration. Use `--overwrite` only after
reviewing an intentional replacement. `--strict-atomic` requests a guarantee that the current
DigitalHub adapter cannot provide and therefore fails before publication. The CLI outputs JSON
and returns a nonzero exit status for operational errors. It never evaluates source supplied in
the result file. Shell reporting code can wrap these commands; generated Python can call the
same core report builder and publisher directly.

The CLI accepts canonical UTF-8 JSON arrays (or `{"results": [...]}`) from a local path or
`--results -` for standard input, with a 10 MiB input limit. This external CLI has a different
file-access boundary from MCP's workspace reader. Only canonical/mapped JSON is supported by
the evidence loader, not CSV or arbitrary formats.

### Equivalent HTTP workflows

The REST service exposes the following additional operations under `/v1/compliance`:

| Endpoint | Input and result |
|---|---|
| `POST /metric-evaluation/code` | An objective, target and explicit bindings; returns a statically validated Python evaluator artifact. Requires the configured model. |
| `POST /reports/code` | Target, `language` (`python` or `shell`), `mode` (`standalone` or `combined`), input contract and optional evaluator artifacts; returns reporting executable artifacts. Requires the configured model. |
| `POST /reports` | `{"results": [...], "variants": ["EVALUATION", "TEST"]}`; builds deterministic report specifications without a model call. |
| `POST /reports/validate` | `{"report": {...}}`; validates the report specification without running code or persisting it. |

For example, prepare evaluator/report requests from the canonical file above:

```python
import json
from pathlib import Path

results = json.loads(Path("results.json").read_text())
first = results[0]
evaluator_request = {
    "project": "credit",
    "entity_kind": "model",
    "entity": "loan-scorer-v1",
    "objective_ref": first["objective_ref"],
    "objective": first["objective"],
    "bindings": {"predict_method": "predict", "label_field": "repaid"},
    "evaluation_data": {
        "features": "evaluation_data['features']",
        "labels": "evaluation_data['labels']",
        "prediction_method": "predict"
    }
}
Path("evaluator-request.json").write_text(json.dumps(evaluator_request))
Path("report-request.json").write_text(json.dumps({
    "results": results,
    "variants": ["EVALUATION", "TEST"]
}))
```

```bash
curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8100/v1/compliance/metric-evaluation/code \
  -H 'Content-Type: application/json' --data-binary @evaluator-request.json

curl --fail-with-body --silent --show-error \
  -X POST http://127.0.0.1:8100/v1/compliance/reports \
  -H 'Content-Type: application/json' --data-binary @report-request.json
```

Add your configured `X-API-Key` header when authentication is enabled. The evaluator bindings describe
your external runtime's data; this request does not upload data or run `predict` in the service.
Review any `needs_input`/`unsupported` response rather than treating it as executable success.
REST report construction returns specifications; attachment uses the explicit tool/coordinator
save workflow or the externally invoked reporting publisher, not an implicit HTTP side effect.

## Install and configure

Prerequisites: Python 3.11 or newer, `uv`, and a local checkout. Run from the checkout root.
Select the dependencies needed by the process you plan to use (these commands are alternatives):

```bash
uv sync                   # core and report preview CLI
uv sync --extra api       # REST API
uv sync --extra mcp       # host-driven MCP server
uv sync --extra server    # API and MCP server
uv sync --extra adk       # Google ADK integration
uv sync --extra acp --extra a2a  # protocol adapters and persistence dependencies
uv sync --extra dev       # test dependencies and adapter SDKs
```

Repeat the required extras on `uv run` too: for example, `uv run --extra mcp compliance-mcp`,
`uv run --extra server compliance-mcp --delegated`, and `uv run --extra dev pytest`.
Each `uv` invocation can resynchronize the environment for its selected extras; do not rely on an
earlier `uv sync --extra ...` to keep an optional runtime installed for a later plain `uv run`.
To use pip instead, install this unified project from its root, e.g.
`python -m pip install ".[mcp]"`; component directories are not separately installable packages.

Set secrets through the process environment or your organization's secret manager; do not commit
tokens or provider keys. MCP uses the host's model for host-driven analysis, so the MCP process does
not need separate model credentials. DigitalHub tools are enabled by default. To use them, provide
the DigitalHub environment settings supported by the installed SDK, including `DHCORE_ENDPOINT`,
and an access credential. The user must identify the DigitalHub project in the conversation, not
through environment settings. Pass the selected project to entity/specification tools with `project`,
reuse a project already established in workspace context, or supply a full `store://` key.
For project specifications, `entity` is the explicit project identifier. Ask when the project is
missing or ambiguous.

MCP and the REST CLI read environment variables; they do not automatically load `adk/.env` or
`packages/compliance-api/.env.example`. The ADK settings loader reads `adk/.env` in a source
checkout, but provider-specific and DigitalHub SDK credentials must still be exported to the
process environment. Keep existing configuration/secrets when copying templates.

The MCP workspace defaults to the process working directory. Set `--workspace PATH` or
`COMPLIANCE_WORKSPACE` to select the state and result-file root explicitly. `uv --project`
selects the Python checkout, not the workspace to assess or a DigitalHub project. State files can contain
workspace or dataset information; inspect them locally and do not commit or share them without
review.

## Standalone REST API

The API accepts project/dataset/model inputs and both code-generation requests directly. These use
its LiteLLM engine, independent of MCP hosts and Google ADK. Deterministic report routes use shared
core functions and can run without model/provider configuration.

1. Install the API extra:

   ```bash
   uv sync --extra api
   ```

2. For analysis/code generation, configure a LiteLLM model ID and provider credentials. For example,
   with a LiteLLM gateway:

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
it in the response header and analysis/code-generation metadata or structured error bodies.
Report construction/validation use the distinct response shapes described in
[Equivalent HTTP workflows](#equivalent-http-workflows); they do not return a `data`/`meta` envelope.

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

- Confirm `GET /health` returns `{"status":"ok"}` and `GET /ready` includes `"status":"ready"`,
  `okf_version`, and `concepts`. Readiness checks the bundle, not provider or DigitalHub access.
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

The MCP server exposes core knowledge, schema, validation, analysis/code/report recording, entity,
and DigitalHub specification/report tools. Host-driven analysis and code generation are the
default: the host model reads the
portable skill, calls the tools, produces the structured result, and asks the core to validate and
record it. No separate LLM key is needed by MCP. The default `FileStateStore` writes to
`.compliance/state.json` in the selected workspace. Analyses are kept per project; the flat
`analysis_*` keys hold the active project and `analysis_workspaces` the others. Each tool call holds
a lock on `.compliance/state.lock` for local state updates, so several hosts can share a workspace.
Code artifacts and report evidence use project-scoped `evaluation_codes` and `evaluation_reports`
stores. Report evidence may be recorded locally before an explicit DigitalHub save.

Install the extra once for command-line testing:

```bash
uv sync --extra mcp
uv run --extra mcp compliance-mcp
```

For an MCP host, configure the host to launch the server on demand. The generated host manifests use
`compliance-mcp` directly, which works when the executable is on the host's `PATH`. Since this
index-based installation is not assumed here, a source checkout can launch it with `uv` instead. Replace
`/absolute/path/to/ai-compliance-agent` with the checkout path. Keep the MCP process environment
configured with `DHCORE_ENDPOINT` and the DigitalHub credential. Use an explicit `--workspace`
argument below (or `COMPLIANCE_WORKSPACE`) for state and evidence-file lookup.
Select the DigitalHub project explicitly in the user request or conversation context.

All hosts share these eight canonical skills:

- `compliance-framework`: concepts and catalog navigation.
- `compliance-specifications`: subject specification retrieval/publication.
- `entity-details`: registered dataitem/model details.
- `project-context`, `dataset-analysis`, `model-analysis`: structured assessments.
- `metric-evaluation-code`: Python evaluator generation.
- `compliance-report`: standalone/combined report executables and reports from supplied results.

Host-driven workflows do not require `analyze_*` or delegated `generate_*` tools. To enable them,
replace the MCP launch extra with `server`, append `--delegated`, and set `STRUCTURED_MODEL`
and provider credentials in the MCP process environment. `--no-dh` removes DigitalHub tools,
including report retrieval/publication; local validation, code artifacts and report building remain.

The generated agent definitions restrict file edits/terminal execution (Claude/OpenCode explicitly
deny writes/bash; Copilot grants read/search and MCP tools). Expect source artifacts in responses
and workspace state, not automatically created executable files. Save/review generated source
yourself and run it outside the assistant.

### VS Code / GitHub Copilot

1. Copy the contents of `integrations/copilot/.github/skills/` into the target workspace's
   `.github/skills/`, preserving the individual skill directories.
2. Copy `integrations/copilot/.github/agents/compliance-assistant.agent.md` into the target
   workspace's `.github/agents/`.
3. Merge the `ai-compliance` server from `integrations/copilot/.vscode/mcp.json` into the target
   workspace's `.vscode/mcp.json`; preserve other servers and settings. For a local checkout:

   ```json
   {
     "servers": {
       "ai-compliance": {
         "type": "stdio",
         "command": "uv",
         "args": [
           "run", "--project", "/absolute/path/to/ai-compliance-agent",
           "--extra", "mcp", "compliance-mcp",
           "--workspace", "/absolute/path/to/target-workspace"
         ]
       }
     }
   }
   ```

4. Ensure `uv` is on VS Code's process `PATH` or set `command` to its absolute executable path.
   Start/restart the `ai-compliance` MCP server in VS Code, review any trust/tool prompts, and
   select a Copilot model that supports tools.
5. Select **compliance-assistant** in the agent picker. Ask for project/data/model analysis,
   evaluator code, or either reporting workflow; the assistant loads the matching bundled skill.
   Verify schema/validation/recording calls in the tool transcript. Copying skills alone does not
   install the custom agent or start MCP.

### Claude Code

Start Claude Code with the checked-in plugin:

```bash
claude --plugin-dir /absolute/path/to/ai-compliance-agent/integrations/claude-code
```

The plugin contains the `ai-compliance:compliance-assistant` agent, all eight portable skills,
and an MCP server entry in
`integrations/claude-code/.claude-plugin/plugin.json`. For a checkout where `compliance-mcp` is
not on `PATH`, change only `mcpServers.ai-compliance` in that manifest to the following object;
preserve the manifest's `name`, `version`, and other metadata:

```json
{
  "command": "uv",
  "args": [
    "run",
    "--project",
    "/absolute/path/to/ai-compliance-agent",
    "--extra",
    "mcp",
    "compliance-mcp",
    "--workspace",
    "/absolute/path/to/target-workspace"
  ]
}
```

Ask Claude to delegate to **ai-compliance:compliance-assistant**; it preloads the eight plugin
skills and inherits plugin MCP tools. Skills are namespaced, e.g. `ai-compliance:metric-evaluation-code`
and `ai-compliance:compliance-report`. Restart/reload the plugin after changing the launcher,
and confirm MCP connects. `uv` and credentials must be available to the Claude process.
A final answer without the required validation/record calls is not sufficient evidence.

The repository also contains a marketplace descriptor:

```text
/plugin marketplace add scc-digitalhub/ai-compliance-agent
/plugin install ai-compliance@ai-compliance
```

This installs the plugin bundle, not the Python distribution. Its default MCP command remains
`compliance-mcp`; install the checkout's MCP extra and expose that executable on the host's `PATH`,
or configure an equivalent `uv` launcher in the installed plugin. For local launcher customization,
`--plugin-dir` with the checkout is the most direct option.

### OpenCode

1. Copy the contents of `integrations/opencode/.opencode/skills/` into the target workspace's
   `.opencode/skills/`.
2. Copy `integrations/opencode/.opencode/agents/compliance-assistant.md` into the target workspace's
   `.opencode/agents/`.
3. Merge the `mcp` block in `integrations/opencode/opencode.json` into the workspace's
   `opencode.json`, preserving other entries. For a local checkout:

   ```json
   {
     "mcp": {
       "ai-compliance": {
         "type": "local",
         "command": [
           "uv", "run", "--project", "/absolute/path/to/ai-compliance-agent",
           "--extra", "mcp", "compliance-mcp",
           "--workspace", "/absolute/path/to/target-workspace"
         ],
         "enabled": true
       }
     }
   }
   ```

4. Make `uv` and credentials available to the OpenCode process. Restart/reload OpenCode, verify
   the MCP server connects, and switch to the **compliance-assistant** primary agent. Use any
   of the eight bundled skills through that agent.

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
5. `record_compliance_analysis(kind="project", request=<original project>, output=<candidate>,
   grounding=<actual OKF concept paths read>)`
   validates again and records it in the workspace. Success includes `"valid": true` and
   `"stored": true`. `grounding` must contain existing bundle paths actually consulted; a list of
   IDs or invented paths is not accepted. Use the paths returned by knowledge tools.
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

   If `--workspace` or `COMPLIANCE_WORKSPACE` selects another root, inspect its `.compliance/state.json`
   instead. Do not commit this
   file by default; it may contain sensitive analysis inputs.
3. Check that the final answer's references and IDs match the knowledge-tool results and that
   validation warnings were addressed or disclosed. A plausible-sounding final answer without the
   calls and successful validation is not a successful tool-driven run.
4. To check that generated skills have not drifted from their canonical source, run:

   ```bash
   uv run python scripts/sync_host_plugins.py --check
   ```

## Google ADK integration

The `adk` extra adds Google ADK while using the same core contracts, skills, DigitalHub adapters,
and knowledge data. It is an alternative runtime, not a dependency of the standalone API or MCP
server.

```bash
uv sync --extra adk
test -e adk/.env || cp adk/.env.example adk/.env
# Set STRUCTURED_MODEL and COORDINATOR_MODEL in adk/.env.
# Export provider-specific and DigitalHub SDK credentials in the process environment.
uv run --extra adk adk web adk --port 8000
```

Open `http://127.0.0.1:8000` and select the coordinator or structured project, dataset, and model
agents. As with other agent runtimes, inspect the agent's tool-call events and confirm validation
succeeds before treating an output as complete.

The coordinator supports evaluator/report-code generation and deterministic reports; these do not
have additional standalone UI launcher directories. Set `COMPLIANCE_WORKSPACE` explicitly for
result-file loading if the default working directory is not your intended workspace. The ADK UI is
for trusted local development and is unauthenticated; do not expose it on an untrusted interface.

## ACP and A2A integrations

These are optional ADK coordinator transports, not host-driven MCP clients. Configure
`COORDINATOR_MODEL`, `STRUCTURED_MODEL` (for delegated analysis/code generation), provider
credentials and DigitalHub credentials as needed in the process environment:

```bash
uv sync --extra acp --extra a2a
uv run --extra acp compliance-acp
# For A2A, first export COMPLIANCE_PROTOCOL_BEARER_TOKEN (at least 32 characters).
uv run --extra a2a compliance-a2a
```

The ACP command is launched by the editor and uses stdio for protocol frames. For a source checkout,
merge the [Zed example](../integrations/acp/zed-settings.json), replacing its command with `uv`
and arguments with
`["run", "--project", "/absolute/path/to/ai-compliance-agent", "--extra", "acp", "compliance-acp"]`.
A2A listens on `127.0.0.1:8101` by default, serves discovery at
`/.well-known/agent-card.json`, and accepts authenticated JSON-RPC at `/a2a` with
`A2A-Version: 1.0`.

Writes are disabled by default; enabling `COMPLIANCE_PROTOCOL_ALLOW_WRITES=true` still requires
approval of each exact named specification/report write. Editor `cwd` does not select a DigitalHub
project, grant arbitrary file access, or change the shared loader's process-local root.
See the [protocol adapter guide](../packages/compliance-protocols/README.md) for all transport,
credential, state, approval and deployment settings.

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
