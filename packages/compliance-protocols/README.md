<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# Compliance protocol adapters

These optional adapters expose the existing ADK coordinator and its packaged persona/skills:

- **ACP** means **Agent Client Protocol**, over stdio, for editors such as Zed.
- **A2A** implements the SDK's **1.0 JSON-RPC binding**, with HTTP/SSE, discovery and durable tasks.
  Requests must include `A2A-Version: 1.0`; older A2A bindings are not advertised or enabled.

The legacy BeeAI Agent Communication Protocol is not implemented.

## Installation and model configuration

From the repository:

```bash
uv sync --extra acp --extra a2a
```

Or install the unified distribution with `[acp]`, `[a2a]`, or `[acp,a2a]`.
Unlike host-driven MCP, these adapters run their own coordinator model. Configure
`COORDINATOR_MODEL`, `STRUCTURED_MODEL` for delegated analyses, and the provider's credentials
as described in the root README. No model or credential is embedded in the portable persona.

The implementation targets `agent-client-protocol` 0.12.x, `a2a-sdk` 1.3.x/1.x and Google ADK
2.13 or later within major version 2. Resolve and test SDK upgrades before deployment.

## Common transport policy

| Environment variable | Default / purpose |
|---|---|
| `COMPLIANCE_PROTOCOL_STATE_DIR` | `.compliance/protocols`; durable SQLite sessions, history and A2A tasks |
| `COMPLIANCE_PROTOCOL_ALLOW_WRITES` | `false`; explicitly enable approval-gated specification writes |
| `COMPLIANCE_PROTOCOL_TIMEOUT_S` | `180`; per-turn deadline, including queueing and approval waiting |
| `COMPLIANCE_PROTOCOL_MAX_CONCURRENCY` | `4`; concurrent turns across conversations |
| `COMPLIANCE_PROTOCOL_APPROVAL_TTL_S` | `300`; expiry for deferred A2A write approvals |

The user must name the project in the conversation or provide a full `store://` key.
DigitalHub enforces project access using the credentials configured for the agent process;
there is no protocol-specific project allowlist or environment-selected default project.
DigitalHub authorization failures are reported as tool errors.

`COMPLIANCE_PROTOCOL_ALLOWED_PROJECTS` has been removed. Remove it from deployment configuration;
it no longer restricts access. Use DigitalHub permissions to limit accessible projects.

Analyses are kept per project inside a conversation, so one conversation may work with several
DigitalHub projects without mixing same-named dataset/model assessments. Each conversation has
independent ADK state; no global workspace state is shared between conversations.

Writes are also checked for conflicts: a save returns `conflict` when the stored specification
changed since it was retrieved, or exists but was never retrieved in the conversation. The approved
operation states whether `overwrite` is requested. Saved specifications carry a `provenance` block.

Only validated/recorded analysis results and normalized retrieved specifications become result
artifacts. Recorded results include OKF version and consulted paths. Assumptions and validation
warnings remain attached. Ordinary explanations are text, not invented structured assessments.
Clarification uses the `request_user_input` tool, with A2A tasks marked input-required.

## ACP editor connection

Launch with `compliance-acp`, or from a source checkout:

```bash
uv run --extra acp compliance-acp
```

Merge the [Zed configuration example](../../integrations/acp/zed-settings.json) into the editor's
settings. The editor must inherit the model, credential and transport policy environment.
For a source checkout, replace the command with `uv` and use:

```json
["run", "--project", "/absolute/path/to/ai-compliance-agent", "--extra", "acp", "compliance-acp"]
```

Supported: initialization, new sessions, text prompts, output/tool updates, cancellation, loading
sessions with history replay, and one-shot permission requests. The session's `cwd` must be an
existing absolute directory. Reloading requires the same resolved directory, but `cwd` never
selects a DigitalHub project.

Not supported: client-supplied MCP servers, additional directories, images/audio, editor filesystem
operations, terminals or remote ACP transport. Unsupported session configuration is explicitly
rejected. The agent uses its built-in compliance tools, not arbitrary client executables.

Stdout is reserved for SDK protocol framing. Runtime diagnostics go to stderr.
Structured results are delivered as JSON Markdown blocks and in the prompt response's
`_meta.compliance.artifacts`; `_meta.compliance.status` distinguishes failure from completion.
If writes are enabled, each exact normalized write is presented via `session/request_permission`;
only `allow_once` is offered, never persistent blanket approval.

## A2A service

Additional settings:

| Environment variable | Default / purpose |
|---|---|
| `COMPLIANCE_PROTOCOL_BEARER_TOKEN` | Required secret, at least 32 characters |
| `COMPLIANCE_PROTOCOL_HOST` | `127.0.0.1`; bind address |
| `COMPLIANCE_PROTOCOL_PORT` | `8101`; listening port |
| `COMPLIANCE_PROTOCOL_PUBLIC_URL` | `http://127.0.0.1:8101`; advertised HTTP(S) origin |

Set the bearer token through a secret manager or the process environment; do not put it in a
checked-in configuration. Set public URL and port consistently, then run:

```bash
uv run --extra a2a compliance-a2a
```

- `GET /.well-known/agent-card.json`: public discovery, generated from the packaged agent/skills.
- `GET /health`: public process/lifespan readiness, not a provider or DigitalHub health probe.
- `POST /a2a`: authenticated JSON-RPC; supports SDK task retrieval, listing, cancellation,
  send-message and streaming operations. Push notifications are not configured/advertised.

Example request (shell variable contains the configured bearer token):

```bash
curl http://127.0.0.1:8101/a2a \
  -H "Authorization: Bearer $COMPLIANCE_PROTOCOL_BEARER_TOKEN" \
  -H 'A2A-Version: 1.0' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "request-1",
    "method": "SendMessage",
    "params": {
      "message": {
        "messageId": "message-1",
        "role": "ROLE_USER",
        "parts": [{"text": "Explain EU AI Act risk classification."}]
      }
    }
  }'
```

Use the returned `contextId` for follow-up messages, and `taskId` to continue an input-required task.
Use `SendStreamingMessage` for SSE. Text and JSON data parts are accepted; file/URL/raw parts are
rejected. JSON analysis inputs are supplied to the coordinator as structured context, not bypasses
around input validation.

### Deferred write approval

When writes are enabled, a proposed save returns an input-required task with a JSON part containing
`approval_required`: a random id, exact project/entity/kind/specification and expiry. No write has
occurred. A client must obtain the user's decision and send a separate message in the same context:

```json
{
  "message": {
    "messageId": "approval-message",
    "contextId": "<returned contextId>",
    "taskId": "<input-required task id>",
    "role": "ROLE_USER",
    "parts": [{
      "data": {"approval_id": "<returned approval id>", "approve": true}
    }]
  }
}
```

Use `false` to reject. An approval cannot be supplied through model-generated text or tool arguments.
It is bound to its conversation and exact normalized payload, expires, and is consumed before
execution. Replaying a decision cannot save twice. A2A callers are responsible for obtaining actual
human consent; possession of the service token alone does not establish that a human approved.

## Deployment boundaries and recovery

This is a **single-tenant, single-worker baseline**, not multi-tenant identity delegation.
All authenticated A2A callers share the configured service identity and its DigitalHub permissions;
caller-specific DigitalHub credentials are not delegated.
Token holders can access this tenant's stored tasks/contexts; do not share the token across tenants.
Run a separate process, state directory, token and DigitalHub credentials per tenant or trust boundary.
Do not point two workers or ACP/A2A processes at the same state directory.

For remote access, terminate TLS at a trusted reverse proxy and apply connection/request limits
there. The application enforces bearer authentication; Agent Card security metadata alone is not
used as enforcement. No push callback URLs or remote files are fetched.

SQLite preserves conversation history, pending approvals and task results across restarts.
Model execution is not checkpoint-resumed: submitted/working A2A tasks from a previous process
are marked failed on startup; input-required and completed tasks remain available.
One turn per conversation runs at a time. Cancellation/deadlines stop model execution cooperatively,
but cannot undo a DigitalHub SDK write that has already started or committed. After interruption,
reconcile the stored specification before requesting another save. There is deliberately no
automatic retry of a consumed write approval.

Protect and back up the state directory: it contains prompts, entity details, approval payloads and
specifications. New state directories are created with owner-only permissions; use appropriate
permissions on existing directories. `.compliance/` is ignored by git.

## Validation

```bash
uv run --extra dev pytest packages/compliance-protocols/tests
```

Tests use scripted models and fake DigitalHub repositories, including real ACP subprocess/stdin
framing and A2A JSON-RPC/SSE exchanges. They do not send prompts to an external model or mutate a
real DigitalHub deployment.
