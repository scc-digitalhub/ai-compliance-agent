# Framework-neutral core boundary

The framework-neutral core now contains contracts, domain errors, the OKF bundle reader, semantic
validators, analysis output-schema/validation helpers, analysis/entity/specification services,
tool metadata and dependency ports, and workspace state abstractions. The core modules import
neither Google ADK nor `compliance_adk`. Framework-neutral implementations are packaged under
`packages/`; ADK-only adapters and entry points remain under `adk/`.

The OKF reader accepts an explicit bundle root, `OKF_PATH`, or the packaged core data. The canonical
OKF/OKB assets live in `packages/compliance-core/src/compliance_core/data/` and are configured as
core package data. No repository-root data symlinks are needed.

`CoreSettings` supplies framework-neutral `OKF_PATH` and `COMPLIANCE_WORKSPACE` defaults. The
existing ADK `Settings` class inherits those shared fields and retains its LLM, runner-limit, and
ADK skill-loader settings. `compliance_dh.settings` owns the standalone DigitalHub project setting.

`FileStateStore` persists JSON-compatible data under `.compliance/`, which is ignored by git because
analysis state can contain sensitive project or dataset metadata. The MCP server selects it at the
active workspace root. The core tool catalog is registered with MCP; host-driven mode is the default
and omits the delegated LLM tools. `record_compliance_analysis` schema- and semantics-validates
host-generated output before storing the normalized project, dataset, or model result in the
workspace. DigitalHub tools are enabled by default and can be disabled explicitly. Knowledge
operations now live in `compliance_core.knowledge_tools` and are described by core `ToolSpec`s;
ADK-specific wrappers expose those tools to ADK. The ADK adapter maps `ToolContext` into `ToolEnv`
and supplies DH adapters and the existing structured analysis engine. `compliance_dh` implements
the DigitalHub repositories and SDK operations without importing ADK; no compatibility facade
remains under `compliance_adk`.

The six skills now live in the `compliance-skills` package, use portable string-valued metadata and
`allowed-tools` frontmatter, and default to host-driven schema → validate → record. Generated
Copilot/VS Code, Claude Code, and OpenCode bundles include the skills and local MCP launch
configuration; a check detects stale copies. The MCP server also exposes an OKF index, path-based
OKF resources, and a `compliance_analysis` prompt.

Core, DH, MCP, Skills, API, and ADK source modules are bundled into one `ai-compliance-platform`
distribution. Optional `api`, `mcp`, `adk`, and `server` extras select runtime dependencies; the
server extras do not include Google ADK. The unified distribution is not yet published to a package
index.

## REST dependency boundary

The REST API code lives in `compliance_api` and uses a LiteLLM engine over the core tool catalog.
The API and MCP modules ship in the same distribution as the ADK integration, but Google ADK is an
optional dependency installed only by the `adk` extra. API and MCP deployments do not require it.

## Next ordered work

1. Add component usage guides, CI build/install checks, and publish the unified distribution when
   release policy and credentials are available.
