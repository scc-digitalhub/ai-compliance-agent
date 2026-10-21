# AI Compliance Framework

AI compliance analysis agents built with Google ADK and FastAPI. The agents use the [Open Knowledge
Framework (OKF)](okf/) catalog to produce typed compliance context for projects and compliance
objectives for datasets and models. An interactive coordinator uses the same structured agents to
answer questions and explain their results. This repository no longer contains the earlier
`src/compliance_agent` LangChain implementation.

## Architecture

- `adk/compliance_adk/contracts/` contains the shared Pydantic request, response, and output models.
- `adk/compliance_adk/knowledge/` provides cached, read-only tools for the OKF catalog.
- `adk/compliance_adk/agents/` defines the project-context, dataset, model, and interactive coordinator agents.
- `adk/compliance_adk/runtime/` runs structured agents, validates their output, and returns grounding metadata.
- `adk/compliance_adk/api/` exposes the structured agents through FastAPI.
- `adk/compliance_adk/skills/` contains the procedures and output examples used by the agents.
- `adk/{compliance_agent,project_context_agent,dataset_agent,model_agent}/` provides entry points for `adk web`.
- `okb/` defines the compliance object schemas; `okf/` contains the associated knowledge catalog.

The structured API accepts project, dataset, and model definitions directly. Dataset and model requests
can include project context from an earlier analysis. Responses have a `data` object and `meta` with
assumptions, warnings, OKF paths consulted, token usage, and the bundle version. Results are decision
support, not legal advice.

## Requirements

- Python 3.11 or newer
- Access to an LLM supported by LiteLLM (for example, OpenAI-compatible providers or the included
	[LiteLLM gateway](litellm/docker-compose.yml))

## Setup

```bash
cd adk
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
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
| `API_KEYS` | Optional comma-separated API keys; unset disables authentication for local development |
| `CORS_ORIGINS` | Optional comma-separated allowed browser origins |
| `MAX_CONCURRENCY`, `REQUEST_TIMEOUT_S`, `MAX_VALIDATION_RETRIES` | Request execution and retry limits |
| `OKF_PATH` | Optional OKF bundle path; defaults to this repository's `okf/` directory |

`STRUCTURED_THINKING_BUDGET` and `COORDINATOR_THINKING_BUDGET` are optional Gemini-specific settings.
See [`adk/.env.example`](adk/.env.example) for the complete configuration list.

## Run the API

From the `adk/` directory with the virtual environment activated:

```bash
python -m uvicorn compliance_adk.api.app:app --host 127.0.0.1 --port 8100
```

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

If `API_KEYS` is configured, include `-H 'X-API-Key: your-key'` in the request. Invalid request
payloads return 422; upstream, timeout, and repeatedly invalid model output errors return structured
error responses with request IDs.

## Interactive Development UI

From `adk/`, run:

```bash
adk web --port 8000
```

The ADK UI discovers the coordinator and the three structured agent entry points. It is for development;
the FastAPI service above is the HTTP API. A React console is not included in this checkout; client
applications can integrate with the versioned endpoints.

## Tests

Tests use a scripted model, so they do not require provider credentials or make real LLM calls:

```bash
cd adk
source .venv/bin/activate
python -m pytest
```
