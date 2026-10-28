# compliance_skills

Portable agent definition and Agent Skills for AI compliance workflows, included together in the
unified `ai-compliance-platform` distribution.

- [`agents/compliance-assistant.md`](src/compliance_skills/agents/compliance-assistant.md) is the
  canonical, framework-neutral coordinator persona derived from the ADK compliance agent.
  Its frontmatter declares `name`, `description`, the six required `skills`, and additional logical
  coordinator `tools`. Its body contains the shared workflow and safety rules.
- [`skills/`](src/compliance_skills/skills/) contains the canonical skill procedures and their tool
  allowlists. Agent and skill tool names remain logical, without host-specific MCP prefixes.
- `from compliance_skills import load_agent, load_skill` loads the packaged definitions without ADK.
  `load_agent()` returns the persona, instructions, skill names and additional tool names.

The optional ADK coordinator loads this same definition. Generate native Copilot, Claude Code and
OpenCode agents alongside skill copies and MCP configurations with
`python scripts/sync_host_plugins.py`; verify them with the same command plus `--check`.
Run these commands in the project's Python environment (for example, `uv run python ...`).
Do not edit generated integration files directly.

The host's selected model is used; no model or credentials are embedded in the definition.
Host-driven analysis is the default. Delegated analysis additionally requires server-side delegated
mode and LLM configuration. DigitalHub errors are reported rather than silently bypassed, and writing
specifications to DigitalHub requires an explicit user request.
DigitalHub project selection also comes from the user's request or previously established context,
not the process environment. Dataset/model entity and specification tools accept an explicit
`project` argument or a full `store://` key; the agent asks when the project is missing or ambiguous.
