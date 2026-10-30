# Refactoring plan: from an ADK application to reusable compliance components

Status: in progress · Scope: `packages/`, `adk/`, `integrations/` · Target: reuse of compliance
capabilities in Google ADK, MCP-capable hosts (VS Code / GitHub Copilot, Claude Code, OpenCode),
REST clients, and other agent frameworks. Gemini CLI integration is deferred.

### Implementation progress

- Extracted framework-neutral contracts, errors, OKF reader, semantic validation, tool catalog,
  state stores, and analysis/entity/specification services into `compliance-core`.
- Added ADK adapters for `ToolContext` and the existing structured analysis runner.
- Added host-driven validation and recording: generated results are normalized and stored in
  workspace state only after validation succeeds.
- Added an MCP stdio adapter. Host-driven mode is its default, workspace state is stored in
  `.compliance/`, DH tools are enabled by default, and delegated LLM analysis is opt-in. The MCP SDK
  is an optional dependency.
- Converted all six skill frontmatters to portable string metadata and `allowed-tools`; the ADK
  loader supports the portable format and the legacy fallback. Analysis skills now document the
  host-driven validate-and-record flow, and ADK coordinator instructions default to host-driven
  mode while preserving delegated tools for explicit requests.
- Moved the canonical OKF/OKB assets into `compliance-core` package data; root data symlinks have
  been removed.
- Added framework-neutral `CoreSettings` for OKF and workspace paths; the legacy ADK settings now
  inherit these fields.
- Extracted DigitalHub operations and repository adapters into the ADK-independent `compliance-dh`
  package.
- Split core, DH, MCP, Skills, and API into separately owned source/import packages under
  `packages/`. Source symlinks and compatibility facades have been removed; `adk/` contains
  ADK-related functionality.
- Consolidated all Python components into the single `ai-compliance-platform` distribution.
  Optional extras select API, MCP, ADK, or server dependencies; server extras do not install
  Google ADK. The unified distribution is not yet published.
- Moved the canonical portable skills into the `compliance-skills` package. Added generated
  Copilot/VS Code, Claude Code, and OpenCode bundles with MCP launch configuration and a
  stale-output check. Gemini CLI integration is intentionally deferred.
- Added the standalone `compliance-api` package and LiteLLM engine, which do not import Google ADK.
- Added project-scoped workspace state, provenance on saved specifications, revision-based write
  conflict detection and cross-process workspace locking.
- Moved analysis definitions, the analyst prompt and the validate-and-retry loop into
  `compliance_core.analysis_engine`; the ADK and LiteLLM engines only implement model calls. MCP
  exposes delegated analysis with `compliance-mcp --delegated`.
- Added CI, a single version source, tag-driven releases (PyPI, GitHub release with uvx-pinned host
  bundles, A2A container image) and a Claude Code marketplace.
- Remaining: adapter-conformance and native host tests, and MCP Registry registration.

---

## 1. Goals and non-goals

**Goals**

1. A **framework-neutral core** (contracts, knowledge, tools, validation, persistence, analysis
   logic) with **no `google.adk` / `google.genai` imports**.
2. **One definition per capability**, exposed through thin adapters: ADK, MCP, REST, and optionally
   LangChain/OpenAI-style function tools.
3. **Portable skills** that follow the [Agent Skills](https://agentskills.io) format and load
   unchanged in ADK, VS Code, Claude Code and OpenCode.
4. **Installable plugins** for coding-agent hosts: portable skills plus host-specific MCP
   configuration for Copilot/VS Code, Claude Code, and OpenCode. Gemini CLI integration is deferred.
5. Two **execution modes** for every analysis:
   - *host-driven*: the host's own LLM follows the skill and calls the tools, and a validation tool
     enforces the contract;
   - *delegated*: a tool runs the internal structured analyser, which is what the current ADK runner
     does.
6. Existing behaviour is preserved: the REST API (`/v1/compliance/*`), `adk web` entry points, and
   the test suite (84 tests).

**Non-goals.** This plan does not change the OKF/OKB content model or the output contracts, and it
does not rewrite the prompts beyond what portability requires.

---

## 2. Current state: where the coupling is

Several modules have no ADK dependency today: `contracts/`, `knowledge/okf.py`,
`knowledge/tools.py`, `runtime/validation.py`, `dh/tools.py` and `errors.py`. The ADK coupling is
concentrated in a few places:

| # | Location | ADK coupling | Consequence |
|---|---|---|---|
| C1 | `agents/coordinator_tools.py`, `specification_tools.py`, `entity_tools.py` | Tools take `google.adk.tools.ToolContext` and read/write `tool_context.state` | The tools can't be called from MCP, REST or tests without ADK. State keys are implicit. |
| C2 | `skill_loader.py` | `google.adk.skills.load_skill_from_dir`, `Skill` model, and a central `TOOL_REGISTRY` that imports every tool module | Skills and tools are resolved only through ADK. The loader imports agents, so the dependency direction is inverted. |
| C3 | `skills/*/SKILL.md` | `metadata.adk_additional_tools` is a **YAML list**. The Agent Skills spec requires `metadata` to be a string-to-string map, and OpenCode validates this. Structured skills rely on ADK `output_schema` ("the object defined by the output schema"). | The skills aren't valid portable skills. The output contract is invisible outside ADK. |
| C4 | `runtime/runner.py`, `runtime/registry.py` | ADK `Runner`, `InMemorySessionService`, `Event`, `genai.types`. Grounding and token usage are scraped from ADK events. | The analysis engine, retry/validation loop and grounding trace can't be reused with another LLM runtime. |
| C5 | `agents/llm.py`, `agents/structured.py`, `agents/coordinator.py` | `LiteLlm`, `BuiltInPlanner`, `LlmAgent`. The persona prompt is a Python string. | The coordinator persona can't be shipped to hosts as an agent definition. |
| C6 | `api/app.py` | `get_fast_api_app(agents_dir=ADK_DIR)` builds the REST app on top of the ADK web server | The REST API always carries the ADK runtime and its routes. |
| C7 | `config.py` | A single `Settings` object mixes LLM, API, DH and paths. `okf_path` defaults to `REPO_DIR/okf` and `.env` to `ADK_DIR` | This breaks when installed as a wheel or run via `uvx`. Every consumer pays for every setting. |
| C8 | `knowledge/okf.py`, `dh/tools.py` | `get_bundle()` and `get_settings()` are process-global singletons | Hard to inject a different bundle or DH client per host or session. |

---

## 3. Target architecture

```
                 ┌──────────────────────────── hosts ─────────────────────────────┐
                 │ VS Code/Copilot · Claude Code · OpenCode · Gemini CLI · ADK web │
                 │            · REST clients · LangChain / other frameworks         │
                 └───────▲──────────────▲──────────────────▲───────────────▲───────┘
   skills/agents/plugins │      MCP     │       REST       │   ADK         │ other
   (static files)        │              │                  │               │
             ┌───────────┴───┐ ┌────────┴────────┐ ┌───────┴──────┐ ┌──────┴───────┐
             │ plugin bundles│ │ compliance-mcp  │ │compliance-api│ │compliance-adk│  adapters
             └───────────────┘ └────────┬────────┘ └───────┬──────┘ └──────┬───────┘
                                        └──────────┬───────┴───────────────┘
                              ┌────────────────────▼─────────────────────┐
                              │              compliance-core              │
                              │ contracts · knowledge (OKF) · validation  │
                              │ tool catalog (ToolSpec) · services        │
                              │ ports: StateStore, SpecRepository,        │
                              │        EntityCatalog, AnalysisEngine      │
                              └───────┬──────────────────────┬───────────┘
                                      │ implements           │ implements
                         ┌────────────▼─────────┐  ┌─────────▼────────────────┐
                         │ compliance-dh        │  │ engines: adk / litellm /  │
                         │ (digitalhub SDK)     │  │ mcp-sampling              │
                         └──────────────────────┘  └──────────────────────────┘
       knowledge pack (okf/ + okb/ + JSON Schemas) ── shipped as package data / MCP resources
```

This is a hexagonal (ports-and-adapters) design. The core owns the domain logic and the interface
definitions ("ports"). Adapters only translate between those interfaces and a runtime: ADK, MCP,
FastAPI or the DH SDK. Every dependency points inward.

---

## 4. Inventory of reusable components

### 4.1 Knowledge pack (data)

| Asset | Today | Target representation |
|---|---|---|
| OKF bundle (`okf/`) | Read from the repo path | Versioned **data package** (`ai-compliance-knowledge`) with `okf/`, `okb/` and a generated `manifest.json` (version, content hash = current `OkfBundle.version`). Shipped inside the core wheel and overridable with `OKF_PATH`. |
| OKB JSON Schemas (`okb/schemas`) | Not used at runtime | Published as MCP resources (`okb://schemas/{name}`) and referenced from skills. |
| Output contract schemas | Pydantic only | Generated JSON Schemas (`ComplianceContextOut`, `DataComplianceOut`, `ModelComplianceOut`, input models) written to `knowledge/contracts/*.schema.json` by a build step. Shipped in skill `references/` and exposed as MCP resources. |

In MCP the OKF becomes **resources**: `okf://index`, `okf://{path}` (for example
`okf://catalog/metrics/fairness/theil-index.md`) and a resource template for directories. Hosts that
support resources can browse the catalog without spending tool calls. The navigation tools remain
for hosts that don't.

### 4.2 Tool catalog

All tools become plain functions in `compliance_core.tools`, each registered with a `ToolSpec`:

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str                      # stable, snake_case, host-neutral
    fn: Callable[..., Any]         # pure function; receives ToolEnv when declared
    group: Literal["knowledge", "validation", "analysis", "session", "dh"]
    read_only: bool                # -> MCP annotations.readOnlyHint
    destructive: bool = False      # -> MCP annotations.destructiveHint
    needs_llm: bool = False        # delegated-mode tools
    output_model: type[BaseModel] | None = None   # -> MCP outputSchema / structuredContent
```

Tools that need context declare a `env: ToolEnv` parameter instead of `ToolContext`:

```python
@dataclass
class ToolEnv:
    state: StateStore          # replaces tool_context.state (C1)
    bundle: OkfBundle          # replaces get_bundle() (C8)
    specs: SpecRepository      # replaces direct dh.* calls
    entities: EntityCatalog
    engine: AnalysisEngine | None
    recorder: GroundingRecorder   # replaces ADK-event scraping (C4)
```

Adapters hide `env` from the LLM-visible signature. The ADK adapter builds it from `ToolContext`, the
MCP adapter from the server lifespan and session, and REST from the request.

| Tool | Group | Read-only | Today | Notes |
|---|---|---|---|---|
| `list_all_concepts`, `list_okf_directory`, `read_okf_concept`, `search_catalog` | knowledge | ✓ | `knowledge/tools.py` | Already pure. Add `env.bundle` and grounding recording. |
| `get_regulatory_refs`, `get_requirements`, `get_groups`, `get_attributes`, `get_metrics`, `get_misuse_scenarios` | knowledge | ✓ | `knowledge/tools.py` | Already pure. Return typed models so MCP can emit `structuredContent`. |
| **`validate_project_context`**, **`validate_dataset_compliance`**, **`validate_model_compliance`** | validation | ✓ | *new*, wraps `runtime/validation.py` + Pydantic | **Key enabler for host-driven mode.** Returns `{valid, errors[], warnings[], normalized}`. |
| **`get_output_schema(kind)`** | validation | ✓ | *new* | Lets hosts without resource support fetch the contract. |
| `analyze_project_context`, `analyze_dataset`, `analyze_model` | analysis | ✗ | `coordinator_tools.py` | Delegated mode. Use `env.engine` and `env.state`. Keep the "stored on DH → ask before rerun" behaviour. |
| **`record_analysis(kind, name, result)`** | session | ✗ | *new* | Host-driven mode: after validation passes, stores the result so later analyses and the save tool reuse it. |
| `get_session_analyses` | session | ✓ | `coordinator_tools.py` | Reads the `StateStore`. |
| `get_compliance_specification`, `save_compliance_specification` | dh | ✗ / destructive | `specification_tools.py` | Go through `SpecRepository`. Save is marked destructive (it replaces the stored spec). |
| `get_entity_details` | dh | ✓ (caches in state) | `entity_tools.py` | Goes through `EntityCatalog`. |

**Tool profiles.** Hosts degrade when too many tools are loaded, so the MCP server and plugin
expose profiles:

- `knowledge`: knowledge and validation tools;
- `analysis`: `knowledge` plus session tools plus `analyze_*`;
- `dh`: DH tools;
- `full`: everything (the default for the Copilot/Claude plugins).

Profiles are selected with `--profile` or `COMPLIANCE_TOOL_PROFILE`.

### 4.3 Ports (interfaces) and their implementations

| Port | Responsibility | Implementations |
|---|---|---|
| `StateStore` | Conversation working set: project, context, datasets, models, entities (today's `session_state.py` keys become a typed `ComplianceWorkspace` model) | `InMemoryStateStore` (tests, MCP default per session); `AdkStateStore` (wraps `ToolContext.state`); **`FileStateStore`** (`.compliance/` folder in the workspace: `project.json`, `datasets/<name>.json`, `models/<name>.json`). The file store is the natural fit for coding hosts, because specs are versioned with git and survive across chat sessions. |
| `SpecRepository` | Load and save specifications by kind and entity | `DhSpecRepository` (current `dh/tools.py` extension logic); `FileSpecRepository` (offline/local); `NullSpecRepository` (feature off). |
| `EntityCatalog` | Resolve dataset/model details by name | `DhEntityCatalog`; `NullEntityCatalog`. |
| `AnalysisEngine` | `run(spec: AnalysisSpec, request) -> AnalysisResponse` with the validate-and-retry loop | `AdkEngine` (current runner, moved to the adapter); **`LiteLlmEngine`** (a tool-calling loop over `litellm` with no ADK, useful for MCP/REST deployments); optional **`McpSamplingEngine`** (uses the host's model via MCP `sampling/createMessage` where the host supports it, so no separate LLM key is needed). |
| `GroundingRecorder` | Collects the OKF paths read by tools | Implemented in core and called by the knowledge tools themselves, replacing `_Trace._collect_paths` over ADK events. |

The validate-and-retry loop (`_run_validated`, `_parse_and_validate`, `VALIDATORS`) moves into the
core as an engine-independent `StructuredAnalysis` helper. Engines only supply `invoke(messages) ->
text` plus usage.

### 4.4 Skills

The canonical skills live in `packages/compliance-skills/src/compliance_skills/skills/` and follow
the Agent Skills spec. Host-specific copies are generated into `integrations/`.

| Skill | Kind | Portable changes |
|---|---|---|
| `compliance-framework` | Knowledge / Q&A | Replace the `adk_additional_tools` list with `allowed-tools: list_all_concepts list_okf_directory …` (space-delimited, Agent Skills experimental field) and `metadata: {tool-server: ai-compliance}`. Mention `okf://` resources as an alternative. |
| `project-context` | Structured analysis procedure | Add `references/output.schema.json` (generated) next to `example.json`. Replace "the object defined by the output schema" with explicit instructions: read the schema reference → produce JSON → **call `validate_project_context`**, fix and re-validate until valid → `record_analysis`. Add a short **"Delegated mode"** section: if `analyze_project_context` is available and the user prefers it, call it instead. |
| `dataset-analysis`, `model-analysis` | Structured analysis procedure | Same changes as `project-context`. |
| `compliance-specifications` | DH workflow | Keep the content. Tool names stay logical. Add a note that the feature needs the `dh` profile. |
| `entity-details` | DH workflow | Same as `compliance-specifications`. |
| **`ai-compliance-assistant`** *(new)* | Persona / orchestration | The coordinator `INSTRUCTION` from `coordinator.py` turned into a skill: when to use which skill, required inputs, the project-before-dataset/model ordering, and the "not legal advice" rule. Hosts without custom agents (OpenCode, plain Claude Code sessions) still get the workflow. |
| *(optional)* `ai-system-repo-review` | New use case for coding hosts | Inspect the current repository (README, model cards, data schemas, training code) to draft `ProjectInput`/`DatasetInput`/`ModelInput`, then run the analyses. This is the main value for VS Code, Claude Code and OpenCode users. |

**Skill authoring rules** (checked by a lint test):

- `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$` and the folder name; `description` is at most 1024 chars.
- `metadata` values are strings only.
- Every tool in `allowed-tools` exists in the `ToolSpec` catalog.
- Bodies refer to tools by their **logical name** (`get_metrics`). Hosts add their own prefixes,
  such as `mcp__ai-compliance__get_metrics` in Claude Code or `ai-compliance/get_metrics` in VS
  Code, so the skills don't hard-code them.
- Large content lives in `references/`: schemas, examples, a cheat sheet of framework ids.

The ADK adapter keeps working by reading `allowed-tools` (with a fallback to the legacy
`metadata.adk_additional_tools` during migration) and resolving names against the `ToolSpec`
catalog. `render_instruction` keeps inlining `example.json` for ADK structured agents. For ADK,
`output_schema` still enforces the contract, so the "call validate" step is skipped by giving those
agents only the knowledge tools.

### 4.5 Agent personas and prompts

| Artifact | Source | Rendered to |
|---|---|---|
| Coordinator persona | `agents/personas/compliance-assistant.md` (front-matter: name, description, tools; body: today's `INSTRUCTION`) | ADK `LlmAgent.instruction`; VS Code `com.github.copilot/agents/compliance.agent.md`; Claude Code `agents/compliance-assistant.md`; OpenCode `.opencode/agent/compliance.md`; Gemini CLI context file (`GEMINI.md`) |
| Structured analyst role prompt | `ROLE_PROMPT` in `structured.py` → `agents/personas/structured-analyst.md` | ADK structured agents and `LiteLlmEngine` |
| Slash commands / MCP prompts | *new*: `/compliance-project`, `/compliance-dataset`, `/compliance-model`, `/compliance-explain` | MCP `prompts` (portable) plus Claude/Copilot command files generated from the same templates |

A small generator (`tools/build_plugins.py`) renders one persona source into each host format,
which differ only in front-matter keys such as tool lists and model hints.

---

## 5. Execution modes

| | Host-driven | Delegated |
|---|---|---|
| Who reasons | The host LLM (Copilot, Claude, …) following the analysis skill | The internal analyser (`AnalysisEngine`) |
| Tools used | Knowledge tools → `validate_*` → `record_analysis` | `analyze_*` |
| Needs an LLM key on the server | No | Yes, unless `McpSamplingEngine` is used |
| Determinism and contract guarantee | Enforced by the validation tool; quality depends on the host model | Enforced by the engine's retry loop; same as today |
| Grounding metadata | Collected by `GroundingRecorder` during the session and returned by `record_analysis` | Returned in `AnalysisMeta` as today |
| Best for | IDE and coding agents, offline use, local-first users | REST API, DH platform automation, CI, ADK |

Both modes produce the same `AnalysisResponse` envelope and the same `StateStore` entries, so
specification saving and follow-up questions behave identically.

---

## 6. Packaging and distribution

### 6.1 Repository layout (single distribution, monorepo)

```
ai-compliance/
├── packages/
│   ├── compliance-core/           # source for compliance_core
│   ├── compliance-dh/             # source for compliance_dh
│   ├── compliance-skills/         # source and data for compliance_skills
│   ├── compliance-mcp/            # source for compliance_mcp
│   └── compliance-api/            # source for compliance_api
├── adk/                           # only Google ADK adapters and agent entry points
├── integrations/                  # generated Copilot, Claude Code and OpenCode bundles
├── pyproject.toml                 # unified ai-compliance-platform distribution
└── scripts/sync_host_plugins.py   # generates and freshness-checks host skill copies
```

The source/import packages are shipped together in `ai-compliance-platform`. Optional `api`, `mcp`,
and `adk` extras install the respective runtime dependencies; `server` combines API and MCP
dependencies and **does not install `google-adk`**. Install the distribution with, for example,
`pip install "ai-compliance-platform[server]"` or use `uv sync --extra server` from the repository.

### 6.2 MCP server component (`compliance_mcp`)

- Built with the official Python MCP SDK (FastMCP). Transports: `stdio` for local plugins and
  `streamable-http` for shared and remote deployments (Docker image, DH platform).
- Tools are generated from the `ToolSpec` catalog. Each gets `annotations` (readOnly, destructive),
  an `outputSchema`, and `structuredContent`.
- Resources: `okf://…`, `okb://schemas/…`, `compliance://contracts/{kind}.schema.json`,
  `compliance://workspace` (current `StateStore` snapshot).
- Prompts: the slash-command templates from section 4.5.
- Configuration comes from the environment only:
  - `COMPLIANCE_TOOL_PROFILE`;
  - `COMPLIANCE_STATE=file:.compliance` by default; state is stored in the workspace, not plugin
    data or a process-global cache;
  - `OKF_PATH`;
  - `DHCORE_*`, which configure credentials for the enabled-by-default DH tools. The project is
    explicitly identified by the user in context, never by an environment variable. The tools remain
    visible if credentials are missing and return an actionable configuration error when invoked;
  - `COMPLIANCE_MODE=host|delegated` (`host` by default). Host mode exposes validation and
    `record_analysis`; delegated mode additionally enables `analyze_*` with
    `STRUCTURED_MODEL` and `LLM_API_*`.
- Run with `uv run --extra mcp compliance-mcp`.

### 6.3 Plugin bundle (one tree, several hosts)

```
plugins/ai-compliance/
├── plugin.json                 # Agent Plugins 1.0 ($schema …/1.0.0/plugin.schema.json)
├── mcp.json                    # portable: {"mcpServers": {"ai-compliance": {"type":"stdio","command":"uvx",
│                               #   "args":["--from","ai-compliance-platform[mcp]","compliance-mcp"]}}}
├── skills/                     # copied from /skills
├── com.github.copilot/         # Copilot/VS Code-only extras
│   ├── agents/compliance.agent.md
│   └── commands/*.md
├── .claude-plugin/plugin.json  # Claude Code manifest (name, version, userConfig for DH endpoint/token)
├── .mcp.json                   # Claude-format MCP config (uses ${CLAUDE_PLUGIN_ROOT}/user_config)
├── agents/compliance-assistant.md   # Claude Code subagent
└── commands/*.md                    # Claude Code slash commands
```

| Host | How it is installed | What it gets |
|---|---|---|
| **VS Code / GitHub Copilot** (and Copilot CLI) | `Chat: Install Plugin From Source` → repo URL, or via the marketplace (`/plugin marketplace add scc-digitalhub/ai-compliance-agent`) | Skills, MCP server, `compliance` custom agent, commands |
| **Claude Code** | `/plugin marketplace add …` then `/plugin install ai-compliance@ai-compliance` | Skills, MCP server, subagent, commands, `userConfig` prompts for DH credentials |
| **OpenCode** | Copy the `opencode.json` `mcp` block. Skills are discovered from `.claude/skills`, `.agents/skills` or `~/.config/opencode/skills`, so `npx skills add`-style copying or a symlink is enough | Skills, MCP server, agent |
| **Gemini CLI** | `gemini extensions install <repo>/plugins/gemini-cli` | MCP server and context file |
| **Any MCP client** (Cursor, Codex, Zed, Windsurf, …) | MCP Registry or `uvx --from "ai-compliance-platform[mcp]" compliance-mcp` | Tools, resources, prompts |
| **Google ADK** | `pip install "ai-compliance-platform[adk]"`; `from compliance_adk import build_coordinator_agent` | Same agents as today, with tools and skills from the core |
| **REST** | `pip install "ai-compliance-platform[api]"`; standalone FastAPI + LiteLLM engine, no ADK | `/v1/compliance/*` unchanged |

Secrets are never committed to manifests. DH integration and its tools are enabled by default;
credentials come from the host's secret handling: Claude `userConfig` with `sensitive: true`,
VS Code `inputs` with `password: true`, or the environment. If credentials are absent, tools report
the missing setup explicitly rather than silently disabling DH support.

---

## 7. Refactoring roadmap

Each phase leaves the suite green and the API and `adk web` working. Phases 1–3 are internal
moves; phases 4–7 add the new surfaces.

### Phase 0 – Safety net (½ day)
1. Freeze the current behavior with focused unit and API tests.
2. Introduce the unified distribution metadata and package boundary tests.

**Done when** the golden tests pass on `main`.

### Phase 1 – Extract `compliance-core` (1–2 days)
1. Create `packages/compliance-core` and move, without logic changes:
   - `contracts/` → `compliance_core.contracts`;
   - `knowledge/okf.py` → `compliance_core.knowledge`;
   - `runtime/validation.py` → `compliance_core.validation`;
   - `errors.py` → `compliance_core.errors`.
2. Split `config.py` into:
   - `CoreSettings` (`OKF_PATH`, state, profile);
   - `LlmSettings` (models, temperature, thinking);
   - `ApiSettings` (keys, CORS, body size).
   DigitalHub credentials are handled by the SDK; project selection comes from explicit user context.
   Resolve the default OKF path from package data (`importlib.resources`) instead of `REPO_DIR` (C7).
3. Package OKF/OKB knowledge as data inside the core wheel; repository-root data symlinks are
   intentionally not retained.

**Status: Complete.** Core imports and tests run without Google ADK; compatibility re-exports and
source-tree symlinks have been removed.

### Phase 2 – Tool catalog and state port (2–3 days), fixes C1, C2, C8
1. Add `ToolSpec`, `ToolEnv`, `StateStore` (with a typed `ComplianceWorkspace` replacing
   `session_state.py` keys), `SpecRepository`, `EntityCatalog` and `GroundingRecorder` to the core.
2. Move the knowledge tools into the core and add a `env` parameter. Recording happens inside the
   tools.
3. Rewrite the specification, entity and session tools against the ports, removing `ToolContext`.
   Move the DH extension logic from `dh/tools.py` into `compliance-dh` as `DhSpecRepository` and
   `DhEntityCatalog`.
4. Add the new tools: `validate_*`, `get_output_schema`, `record_analysis`.
5. In `compliance-adk`, add `adk_tools(specs, env_factory)`, which wraps each `ToolSpec` as an ADK
   `FunctionTool`. It hides `env`, builds `AdkStateStore` from `ToolContext` and keeps the original
   signature and docstring.
6. Replace the central `TOOL_REGISTRY` in `skill_loader.py` with catalog lookups, so the loader no
   longer imports agent modules.

**Done when** the golden ADK tool-declaration snapshots are unchanged, and the core tool tests run
without ADK using `InMemoryStateStore` and fake repositories.

**Status: Core ports and catalog implemented.** Cross-adapter schema parity snapshots remain.

### Phase 3 – Engine port (2–3 days), fixes C4, C5
1. Move the retry/validation loop and the envelope construction from `runtime/runner.py` into
   `compliance_core.analysis.StructuredAnalysis`. Engines implement only `invoke()`.
2. Make `StructuredAgentSpec` (`specs.py`) runtime-neutral: drop `ModelRole` from the core and keep
   the input/output schema, skill name and validator key.
3. Turn `AdkEngine` (today's `StructuredRunner` internals, `build_structured_agent`, `llm.py`) into
   an implementation in `compliance-adk`.
4. Add `LiteLlmEngine` in its own package, a minimal tool-calling loop over the same `ToolSpec`
   catalog.
5. Make `RunnerRegistry` generic over `AnalysisEngine`.

**Done when** the `test_runner.py` scenarios pass against both `AdkEngine` (the existing
`ScriptedLlm`) and `LiteLlmEngine` (a scripted litellm mock), and grounding and usage are identical.

**Status: Standalone LiteLLM execution is implemented in `compliance-api`; shared engine parity
tests and extracting reusable persona prompts remain.**

### Phase 4 – Portable skills and personas (1–2 days), fixes C3
1. Move `adk/compliance_adk/skills` → `/skills` and convert the frontmatter to `allowed-tools` and
   string `metadata`.
2. Generate `references/output.schema.json` and the input schemas with `tools/gen_schemas.py`.
3. Add the host-driven steps (validate → record) and the delegated-mode note to the three analysis
   skills.
4. Extract `INSTRUCTION` and `ROLE_PROMPT` into `agents/personas/*.md`, and add the
   `ai-compliance-assistant` skill.
5. Update the ADK loader to read the new format. It keeps the legacy fallback for one release.
6. Turn on the strict skill lint (spec rules plus tool existence).

**Done when** `skills-ref validate` (or the equivalent lint) passes for every skill, ADK agents
behave identically (golden tests), and the package skills load in Claude Code and VS Code with no
warnings.

**Status: Portable skills and generated host bundles implemented.** Coordinator/analyst persona
extraction, generated input/output schema references, native host validation, and Gemini CLI are
not part of this completed slice; Gemini is deferred.

### Phase 5 – MCP server (2–3 days)
1. Create `packages/compliance-mcp`: FastMCP app factory, tool registration from the catalog,
   resources, prompts, profiles and state selection.
2. Lifecycle: per-session `InMemoryStateStore` keyed by MCP session id, or a shared
   `FileStateStore`. Wire `DhSpecRepository` only when the DH settings are present.
3. Expose `analyze_*` only when an engine is configured, and implement the optional
   `McpSamplingEngine` behind a flag.
4. Tests: in-memory MCP client tests for list_tools (snapshot), call_tool on each group, resources
   read, and a host-driven end-to-end flow (knowledge → validate → record → save via a fake repo).

**Done when** `npx @modelcontextprotocol/inspector uvx --from 'ai-compliance-platform[mcp]' compliance-mcp` lists the expected tools,
resources and prompts, and the test flow passes.

**Status: MCP adapter, stdio entry point, resources, prompts, DH tools, and host-driven tests are
implemented.** Published-package inspector testing remains pending.

### Phase 6 – Decouple the REST API (1 day), fixes C6
1. Move `api/` to `packages/compliance-api` as a plain `FastAPI()` app built on the core contracts,
   standalone `LiteLlmEngine`, and DH adapter. The normal server install has no `google-adk`
   dependency.
2. Keep ADK web routes out of the REST service. Users who need `adk web` install the unified
   distribution's `adk` extra, which adds Google ADK without changing the server extra.
3. Optionally mount MCP streamable-http at `/mcp` on the server app, which makes it one deployable
   for the DH platform.

**Done when** the OpenAPI golden snapshot for `/v1/compliance/*` is unchanged and `test_api.py`
passes.

**Status: Complete.** The REST app and LiteLLM engine are in `compliance-api`, and an import-boundary
test verifies they do not import Google ADK.

### Phase 7 – Plugins, distribution, docs (2 days)
1. `scripts/sync_host_plugins.py` renders Copilot/VS Code, Claude Code, and OpenCode skill bundles.
   The generated-file freshness check is implemented; Gemini support is deferred.
2. Add marketplace and registry metadata if/when publication is approved.
3. CI:
   - unit tests per package;
   - native host plugin validation;
   - skill lint;
   - MCP smoke test;
   - publish the unified wheel to PyPI and a Docker image on tag.
4. Complete component usage guides and CI/release automation. Current component README files and
   host setup instructions are starter documentation; distribution publication and native host
   tests are not yet complete.

**Total estimate: about 12–17 developer-days.**

---

## 8. File-by-file migration map

| Current | Target |
|---|---|
| `adk/compliance_adk/contracts/*` | `compliance_core/contracts/*` |
| `adk/compliance_adk/knowledge/okf.py` | `compliance_core/knowledge/bundle.py` |
| `adk/compliance_adk/knowledge/tools.py` | `compliance_core/tools/knowledge.py` (+ `ToolSpec`s) |
| `adk/compliance_adk/runtime/validation.py` | `compliance_core/validation/semantic.py`, used by `tools/validation.py` |
| `adk/compliance_adk/runtime/runner.py` | Split: loop and envelope → `compliance_core/analysis/structured.py`; ADK invocation → `compliance_adk/engine.py` |
| `adk/compliance_adk/runtime/registry.py` | `compliance_core/analysis/registry.py` (engine-agnostic) |
| `adk/compliance_adk/agents/specs.py` | `compliance_core/analysis/specs.py` (without `ModelRole`) |
| `adk/compliance_adk/agents/coordinator_tools.py` | `compliance_core/tools/analysis.py` + `tools/session.py` |
| `adk/compliance_adk/agents/specification_tools.py` | `compliance_core/tools/specifications.py` (via `SpecRepository`) |
| `adk/compliance_adk/agents/entity_tools.py` | `compliance_core/tools/entities.py` (via `EntityCatalog`) |
| `adk/compliance_adk/agents/session_state.py` | `compliance_core/state/workspace.py` (typed model + stores) |
| `adk/compliance_adk/dh/tools.py` | `compliance_dh/{repository,catalog,client}.py` |
| `adk/compliance_adk/skill_loader.py` | `compliance_core/skills.py` (neutral parser) + `compliance_adk/skills.py` (ADK `Skill` bridge) |
| `adk/compliance_adk/agents/{coordinator,structured,llm}.py` | `compliance_adk/agents/*`; prompts → `agents/personas/*.md` |
| `adk/compliance_adk/api/*` | `packages/compliance-api/*` |
| `adk/compliance_adk/config.py` | `compliance_core/config.py` + per-adapter settings |
| `adk/compliance_adk/skills/*` | `/skills/*` |
| `adk/{compliance,project_context,dataset,model}_agent/` | `packages/compliance-adk/entrypoints/*` (unchanged `root_agent` API) |
| `okf/`, `okb/` | `knowledge/okf`, `knowledge/okb` |

---

## 9. Testing strategy

- **Core unit tests** run without ADK, MCP or the network. They use fakes for `SpecRepository`,
  `EntityCatalog` and `AnalysisEngine`. Most of today's `test_*_tools.py` logic moves here, with
  `ToolContext` replaced by `InMemoryStateStore`.
- **Adapter conformance tests:** one parametrized suite asserts that each `ToolSpec` exposes the
  same name, parameters and descriptions through ADK, MCP and the LiteLLM tool schema.
- **Engine tests:** the existing scripted scenarios run against every engine.
- **Skill and plugin lint:** Agent Skills rules, tool existence, generated-file freshness, and
  `claude plugin validate`.
- **Manual and host tests:** extend `manual_tests/` with a scripted VS Code/Claude Code checklist
  covering install, run the project → dataset → model flow in host-driven mode, and save to DH.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Host-driven output quality varies by host model | The validation tools give hard error feedback, and the skills require validate-until-valid. The delegated mode stays available for guaranteed results. |
| Too many tools degrade host tool selection | Use tool profiles, MCP resources for the OKF instead of navigation calls, and concise tool descriptions. |
| State lost between host chat sessions | Use `FileStateStore` in the workspace (`.compliance/`) by default for plugins. It is git-friendly and auditable. |
| Divergent behaviour between adapters | Single `ToolSpec` catalog, conformance tests and golden snapshots. |
| Secrets in plugin manifests | Use only host secret mechanisms (`userConfig.sensitive`, VS Code `inputs`), plus a lint rule against literal credentials. |
| Breaking existing `compliance_adk` importers | Re-export shims for one minor release and a migration guide. |
| MCP sampling not supported by every host | Keep it optional. Fall back to `litellm`, or to no engine (host-driven only). |
| Knowledge licensing when redistributed in plugins | The OKF/OKB bundle is CC BY 4.0 (`okb/manifest.json`). Include attribution in the plugin and wheel metadata. |

---

## 11. Decisions confirmed

1. **Default execution mode:** host-driven. Delegated analysis remains an explicit opt-in for REST,
   CI or hosts that configure an internal LLM engine.
2. **State location:** the current workspace, under `.compliance/`; do not store primary analysis
   data under plugin-managed data directories or only in process memory. Add `.compliance/` to the
   default ignore guidance and document that it can contain sensitive project information.
3. **DH integration:** enabled by default, with credentials supplied by the user or deployment
   environment. Missing credentials produce actionable errors; they do not silently hide tools.
4. **Repository strategy:** keep a monorepo for core, adapters, skills, knowledge, and generated
   host plugin bundles.
5. **Server deployment:** use the standalone REST/MCP server and LiteLLM engine without
   `google-adk`. Keep the ADK adapter and `adk web` available as a separate optional package.

These are implementation constraints, not outstanding questions. If workspace state or DH
credentials are unavailable in a host, report that limitation explicitly while preserving
read-only knowledge and validation features.
