# AI Compliance Framework

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/scc-digitalhub/ai-compliance-agent/release.yaml?event=release) [![license](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/scc-digitalhub/ai-compliance-agent/LICENSE) ![GitHub Release](https://img.shields.io/github/v/release/scc-digitalhub/ai-compliance-agent)
![Status](https://img.shields.io/badge/status-stable-gold)

Reusable AI compliance tools and analysis agents. The framework uses the packaged [Open Knowledge
Framework (OKF)](packages/compliance-core/src/compliance_core/data/okf/) catalog to produce typed
compliance context for projects and compliance objectives for datasets and models. It includes a
framework-neutral core, MCP and REST adapters for host-driven/delegated analysis, and a separate
Google ADK integration. This repository no longer contains the
earlier `src/compliance_agent` LangChain implementation.

## Architecture

- `packages/compliance-core/src/compliance_core/` contains reusable contracts, validation,
  knowledge access, state stores, service logic, ports, the canonical tool catalog and the shared
  structured-analysis engine (analysis definitions, analyst prompt, validate-and-retry loop and
  response metadata). The ADK and LiteLLM engines only implement how a message reaches the model. Core
  also owns evaluator/report-code contracts, deterministic report construction and the external
  `compliance-report` CLI. Core imports do not require Google ADK.
- `packages/compliance-dh/src/compliance_dh/` provides DigitalHub repositories and SDK operations
  without importing ADK.
- `packages/compliance-skills/src/compliance_skills/` packages the canonical portable coordinator
  definition in `agents/` together with its procedures in `skills/`.
- `packages/compliance-api/src/compliance_api/` provides the standalone FastAPI/LiteLLM service
  without Google ADK.
- `packages/compliance-mcp/src/compliance_mcp/` adapts the catalog to MCP tools, resources, and
  prompts. The MCP extra has no Google ADK dependency.
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
`api`, `mcp`, `adk`, or `server` (API and MCP without Google ADK).
The optional `acp` and `a2a` extras add protocol SDKs, ADK and SQLite persistence; `dev` adds the
test dependencies. Run the commands below from this checkout's root. For a local pip installation,
use `python -m pip install ".[server]"` (replace `server` with the desired extra); an index-based
installation requires a published distribution and is not assumed by these instructions.

The structured API accepts project, dataset, and model definitions directly. Dataset and model requests
can include project context from an earlier analysis. Responses have a `data` object and `meta` with
assumptions, warnings, OKF paths consulted, token usage, and the bundle version. Results are decision
support, not legal advice.

The assistant also generates catalog-grounded Python metric evaluators and reporting executables.
Reporting supports either generated Python/shell workflows (including a single external executable
that evaluates, builds reports, and publishes them) or agent-built reports from supplied evaluation
files/references. Shared deterministic helpers produce OKF `EVALUATION` measurements and separate
`TEST` objective assessments. Named `compliance-report` extensions preserve prior evidence and
require explicit project/target selection. Generated code is statically checked, never executed by
the service; external publishing uses the caller's runtime credentials. The current DigitalHub SDK
does not guarantee transactional conditional updates, so strict atomic publication is not claimed.
See the [end-to-end usage scenarios](docs/compliance-platform-usage-guide.md#end-to-end-scenarios-for-the-compliance-assistant)
for project/data/model analysis, evaluator generation, both reporting flavours, and combined runs.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- An LLM provider supported by LiteLLM is required for ADK and REST analysis/code-generation calls.
  The default host-driven MCP workflow uses the host's model and does not require separate LLM
  credentials. Deterministic report construction/validation and CLI preview need no model credentials.
- DigitalHub credentials are needed for entity lookup and specification/report retrieval or
  publication; DigitalHub integration is enabled by default.

## Installation choices

From the repository root, select the extra for the process you will run:

```bash
uv sync                         # core, contracts and report preview CLI
uv sync --extra mcp              # host-driven IDE assistant
uv sync --extra api              # REST analysis, code generation and deterministic reports
uv sync --extra server           # REST + MCP; also supports opt-in delegated MCP
uv sync --extra adk              # Google ADK coordinator and development UI
uv sync --extra acp --extra a2a  # optional editor/remote agent protocols
uv sync --extra dev              # tests
```

These are alternatives, not a required sequence. Keep the required extras on subsequent `uv run`
commands too; `uv` synchronizes the environment for the extras selected by each invocation.
GUI-launched hosts must be able to find `uv` (or use its absolute executable path).

## Google ADK setup

This installs the unified project with the optional Google ADK runtime dependencies:
```bash
uv sync --extra adk
test -e adk/.env || cp adk/.env.example adk/.env
```

Edit `adk/.env` and set `STRUCTURED_MODEL` and `COORDINATOR_MODEL` to LiteLLM model IDs. Configure
provider credentials using the variables expected by your LiteLLM provider. For a gateway, set
`LLM_API_BASE`, and optionally `LLM_API_KEY`. Do not commit `.env` or real credentials.

| Variable | Purpose |
|---|---|
| `STRUCTURED_MODEL` | Default model for project/dataset/model analyses and both code-generation operations |
| `COORDINATOR_MODEL` | Model for interactive compliance questions and reasoning |
| `PROJECT_CONTEXT_AGENT_MODEL_NAME`, `DATA_ANALYSIS_AGENT_MODEL_NAME`, `MODEL_ANALYSIS_AGENT_MODEL_NAME`, `ROOT_AGENT_MODEL_NAME` | Optional per-agent overrides and legacy names |
| `LLM_API_BASE`, `LLM_API_KEY` | Optional LiteLLM gateway URL and key |
| `MAX_CONCURRENCY`, `REQUEST_TIMEOUT_S`, `MAX_VALIDATION_RETRIES` | ADK runner concurrency, timeout, and validation retry limits |
| `OKF_PATH` | Optional OKF bundle path; defaults to the packaged core bundle |
| `COMPLIANCE_WORKSPACE` | Optional default MCP workspace path; defaults to the process working directory |

The optional `STRUCTURED_THINKING_BUDGET` and `COORDINATOR_THINKING_BUDGET` settings apply only to
Gemini models. See [`adk/.env.example`](adk/.env.example) for the complete configuration list.
ADK reads model/runtime settings from `adk/.env` in a source checkout. Export DigitalHub and
provider-specific credential variables in the process environment so their SDKs can read them;
copying the template does not export those variables. MCP and REST do not automatically load this
file. For installed deployments, prefer process environment configuration.

## MCP host integration

The MCP adapter defaults to host-driven analysis: the host model gathers inputs, uses the OKF tools,
requests the output schema, validates the generated result, and records valid results in the current
workspace's `.compliance/state.json`, together with their provenance. Analyses are kept per project:
switching projects archives the previous project's results instead of mixing them, and several
host processes can share one workspace safely. DigitalHub entity lookup and specification tools are enabled
by default; configure DigitalHub credentials in the environment. Delegated internal LLM analysis is
opt-in: run `uv run --extra server compliance-mcp --delegated` with `STRUCTURED_MODEL` and provider
credentials to also expose `analyze_*`, `generate_metric_evaluation_code`, and
`generate_compliance_report_code`. Use `--workspace PATH` to select the state/input workspace
and `--no-dh` to disable DigitalHub tools, including report retrieval/publication.

DigitalHub project selection is explicit, not environment-based. For specification and entity
operations, name the project in the request (for example, "retrieve dataset applications-2024 in
project credit") or refer to a project already established in the conversation. Dataset/model tools
accept a `project` argument; a full `store://` key also identifies its project. For project
specifications, `entity` is the project identifier. Saved specifications include a `provenance`
block (analysis mode, OKF version, consulted OKF paths, assumptions, warnings, framework version and
time). A save is refused with `conflict` when the stored specification changed since this workspace
retrieved it, or exists but was never retrieved, unless the user confirms `overwrite=True`. The
check compares content revisions immediately before writing; it narrows, but cannot eliminate, the
window for a concurrent write between the check and the save. The agent asks when the project is missing or
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
Replace `<repository>` with the absolute path to this checkout. Append
`--workspace /absolute/path/to/target-workspace` to select the IDE workspace explicitly rather than
relying on a host's launch directory. Merge configuration into existing files; do not overwrite
other servers, agents or skills.

- **Copilot/VS Code:** copy `integrations/copilot/.github/skills/` into the workspace's
  `.github/skills/`, copy `integrations/copilot/.github/agents/` into `.github/agents/`, and merge
  `integrations/copilot/.vscode/mcp.json` into `.vscode/mcp.json`. Select `compliance-assistant`
  in the agent picker.
- **Claude Code:** load `integrations/claude-code/` with `claude --plugin-dir` or install it as a
  plugin. Its manifest exposes the `compliance-mcp` executable, bundled skills and
  `ai-compliance:compliance-assistant` agent. Ask Claude to delegate to that agent; it preloads
  all eight plugin skills and inherits the plugin's MCP tools.
- **OpenCode:** copy `integrations/opencode/.opencode/skills/` and
  `integrations/opencode/.opencode/agents/` into the workspace's `.opencode/` directory, then merge
  `integrations/opencode/opencode.json` into the workspace OpenCode configuration. Switch to
  the `compliance-assistant` primary agent.

Each host launches the MCP server from its process environment. Set DigitalHub credentials there as
required; no credentials are stored in the bundles. Analysis state remains in the active workspace's
`.compliance/` directory. Regenerate or verify checked-in bundles with
`uv run python scripts/sync_host_plugins.py` and `uv run python scripts/sync_host_plugins.py --check`.

The eight skills are `compliance-framework`, `compliance-specifications`, `entity-details`,
`project-context`, `dataset-analysis`, `model-analysis`, `metric-evaluation-code`, and
`compliance-report`. Select the bundled assistant, then ask for the relevant workflow; do not
expect the delegated `generate_*` tools in default MCP mode. Generated source is returned/stored
as an artifact, not automatically written to an executable file or run in a terminal.
For full configuration examples for all three hosts, see the
[IDE setup instructions](docs/compliance-platform-usage-guide.md#coding-agent-hosts-through-mcp).

MCP can load JSON evidence using paths relative to its selected workspace (maximum 1,000,000
bytes; no URLs, absolute paths or symlinks). Other resource schemes require an explicitly
configured authorized reader in an embedding application; they are not enabled by these bundles.

The unified distribution builds as one wheel or source distribution. The ADK extra installs Google
ADK; the API, MCP, and server extras do not.

Claude Code can also install the plugin straight from this repository, which is a plugin
marketplace (`.claude-plugin/marketplace.json`):

```text
/plugin marketplace add scc-digitalhub/ai-compliance-agent
/plugin install ai-compliance@ai-compliance
```

## Releases and distribution

The version in `pyproject.toml` is the single source: the MCP server, ACP agent info, A2A Agent
Card, Claude plugin manifest and marketplace all report it (`compliance_core.version`).

- **Manual release preparation**: bump the version in `pyproject.toml`, regenerate host bundles with
  `uv run python scripts/sync_host_plugins.py`, run the tests and build with `uv build`. Use
  `scripts/check_wheel_extras.sh` to install each extra in a clean environment and verify that
  `mcp`, `api` and `server` do not pull in Google ADK. Publishing packages, host bundles and container
  images is a separate manual step; no automated publishing is configured.
- **Release host bundles** launch the published version without a local install:
  `uvx --from "ai-compliance-platform[mcp]==X.Y.Z" compliance-mcp`. Generate them locally with
  `uv run python scripts/sync_host_plugins.py --output <dir> --launcher uvx`. This launcher requires
  that version to be published and accessible on the configured index; it is not the local-checkout
  installation path. The checked-in bundles keep
  running `compliance-mcp` from `PATH` for source checkouts.
- **A2A container** (`deploy/a2a/Dockerfile`): `uv build` then
  `docker build -f deploy/a2a/Dockerfile -t compliance-a2a .`. It runs as a non-root user, keeps
  state in the `/data` volume and listens on port 8101; provide the bearer token, public URL, model
  and DigitalHub configuration through the environment.

Registration in the MCP Registry is not set up yet: it needs the PyPI package to be published and a
registry entry whose `uvx` launch selects the `compliance-mcp` command with the `mcp` extra.

## ACP and A2A agent exposure

Use `uv sync --extra acp --extra a2a` to install the optional protocol adapters, then configure the
coordinator model and provider credentials as in the ADK setup. Unlike host-driven MCP, these
adapters run their own model.

- `uv run --extra acp compliance-acp`: Agent Client Protocol over stdio, with persistent conversations, history replay,
  text/tool updates, cancellation and per-write editor permissions.
- `uv run --extra a2a compliance-a2a`: A2A 1.0 JSON-RPC/HTTP and SSE, with Agent Card discovery, durable tasks,
  input-required clarification, validated JSON artifacts and deferred per-write approval.

DigitalHub operations require an explicit user-selected project; DigitalHub enforces access using
the agent process's configured credentials, without a protocol-specific project allowlist.
Writes default to disabled. A2A additionally
requires `COMPLIANCE_PROTOCOL_BEARER_TOKEN` (at least 32 characters). Analyses are kept per
project, so a conversation may switch between DigitalHub projects.
Set `COMPLIANCE_PROTOCOL_ALLOW_WRITES=true` only when approval-gated specification/report
publication is intended. ACP/A2A do not provide editor-file or arbitrary URL loading: supply
canonical results inline or use authorized local files under the agent process's working directory
(not the editor's session directory). Other reference schemes require an injected authorized reader.

This is a single-tenant, single-worker deployment baseline. See the
[protocol setup, configuration, client examples and deployment boundaries](packages/compliance-protocols/README.md).

## Run the standalone API

Install the unified distribution with API dependencies, then run the service:

```bash
uv sync --extra api
uv run --extra api compliance-api
```

For analysis/code generation, configure `STRUCTURED_MODEL` and provider credentials (or
`LLM_API_BASE` and `LLM_API_KEY` for a LiteLLM gateway) in the API process environment.
Optional API keys, CORS, and request limits are
documented in [`packages/compliance-api/.env.example`](packages/compliance-api/.env.example). This
service uses LiteLLM and does not install Google ADK.
The CLI reads configuration from the process environment; `.env.example` is a reference, not an
automatically loaded dotenv file. Deterministic report endpoints work without model credentials.

- OpenAPI documentation: <http://127.0.0.1:8100/docs>
- Liveness: `GET /health`
- Readiness: `GET /ready`
- Project context: `POST /v1/compliance/context`
- Dataset compliance: `POST /v1/compliance/datasets`
- Model compliance: `POST /v1/compliance/models`
- Evaluator code generation: `POST /v1/compliance/metric-evaluation/code`
- Standalone/combined reporting code generation: `POST /v1/compliance/reports/code`
- Deterministic report construction: `POST /v1/compliance/reports`
- Report validation: `POST /v1/compliance/reports/validate`

Analysis and code-generation responses use `data`/`meta`. Report construction returns
`reports`, `issues`, `objective_references`, `assessments`, `provenance`, and `target`; validation
returns `valid` with errors or a normalized report. HTTP does not implicitly publish reports.
The default server accepts inline results; file/resource references require an authorized
`evaluation_input_reader` passed to `create_app` by an embedding application.

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

Use the unified distribution's ADK extra when using Google ADK:

```bash
uv run --extra adk adk web adk --port 8000
```

The ADK UI discovers the coordinator and the three structured agent entry points. It is for development.
Evaluator/report-code generation is available through the coordinator; no additional standalone
`adk web` launcher directories are provided for these operations. The development UI is
unauthenticated; keep it on a trusted local interface.
A React console is not included in this checkout; client
applications can integrate with the versioned endpoints.

## Tests

Tests use scripted models and fakes, so they do not require provider credentials or make real LLM
calls. From the repository root:

```bash
uv sync --extra dev
uv run --extra dev pytest
```

## Result quality

Every analysis result is checked against its schema and the OKF bundle before it is stored:

- **Cited sources**: host-driven results are recorded only with `grounding`, the OKF concept paths
  the host read; every path must exist in the bundle. Delegated results record the paths the engine
  actually read and warn when none were consulted. Sources are kept in the result's provenance.
- **Catalog consistency** (errors): unknown requirement ids in objectives, requirements attributed
  to a different framework than in the catalog, requirements citing a framework that is not among
  the declared regulations, out-of-range metric thresholds, and dataset scope mismatches.
- **Plausibility** (warnings): unknown frameworks or requirement ids, objectives linking
  requirements outside the project context, and risk levels inconsistent with the catalog's
  high-risk or prohibited-practice requirements that are listed. The OKF bundle has no structured
  Annex III mapping, so risk classification by domain is measured by the benchmark below rather
  than enforced.

### Benchmark

`evals/cases.json` holds benchmark cases (Annex III high-risk uses, transparency-only, minimal-risk
and prohibited practices, plus dataset and model analyses) with the legal basis of each expectation.
The expectations must be confirmed by a qualified reviewer before scores inform decisions.
`scripts/run_evals.py` runs them through the LiteLLM engine and compares models on validity, risk
accuracy, recall of expected catalog requirements and attributes, invented catalog ids, grounding,
retries, warnings, tokens and latency:

```bash
uv sync --extra api
uv run --extra api python scripts/run_evals.py --model openai/gpt-4.1 --model gemini/gemini-2.5-pro \
  --out eval-report.json --markdown eval-report.md
```

DigitalHub tools are disabled during evaluation unless `--with-dh` is given. Run the benchmark locally
when skills, the OKF bundle or the model change, supplying model credentials through the environment.

## Security Policy

The current release is the supported version. Security fixes are released together with all other fixes in each new release.

If you discover a security vulnerability in this project, please do not open a public issue.

Instead, report it privately by emailing us at digitalhub@fbk.eu. Include as much detail as possible to help us understand and address the issue quickly and responsibly.

## Contributing

To report a bug or request a feature, please first check the existing issues to avoid duplicates. If none exist, open a new issue with a clear title and a detailed description, including any steps to reproduce if it's a bug.

To contribute code, start by forking the repository. Clone your fork locally and create a new branch for your changes. Make sure your commits follow the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification to keep history readable and consistent.

Once your changes are ready, push your branch to your fork and open a pull request against the main branch. Be sure to include a summary of what you changed and why. If your pull request addresses an issue, mention it in the description (e.g., “Closes #123”).

Please note that new contributors may be asked to sign a Contributor License Agreement (CLA) before their pull requests can be merged. This helps us ensure compliance with open source licensing standards.

We appreciate contributions and help in improving the project!

## Authors

This project is developed and maintained by **DSLab – Fondazione Bruno Kessler**, with contributions from the open source community. A complete list of contributors is available in the project’s commit history and pull requests.

For questions or inquiries, please contact: [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu)

## Copyright and license

Copyright © 2025 DSLab – Fondazione Bruno Kessler and individual contributors.

This project is licensed under the Apache License, Version 2.0.
You may not use this file except in compliance with the License. Ownership of contributions remains with the original authors and is governed by the terms of the Apache 2.0 License, including the requirement to grant a license to the project.