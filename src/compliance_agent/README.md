# AI Compliance Agent

A LangChain-based agent that navigates an [Open Knowledge Format (OKF)](../okf/) bundle of
compliance concepts to assist with EU AI Act, GDPR, and related regulatory compliance for
AI projects, datasets, and models.

## Features

| Task | Endpoint | Description |
|------|----------|-----------|
| **Compliance Context** | `POST /compliance/context/{project_id}` | Loads a stored project and identifies applicable regulations, requirements, affected groups, protected attributes, misuse scenarios, and EU AI Act risk level |
| **Dataset Compliance** | `POST /compliance/dataset/{dataset_id}` | Loads a stored dataset and identifies protected attributes, proposes `ComplianceObjective` instances with metric thresholds |
| **Model Compliance** | `POST /compliance/model/{model_id}` | Loads a stored model and proposes compliance objectives covering fairness, robustness, transparency, calibration, and privacy |
| **Entity CRUD** | `GET\|POST\|PUT\|DELETE /entities/{projects\|datasets\|models}` | Manage projects, datasets, and models stored as JSON files |

All compliance endpoints return both a **narrative analysis** and **schema-compliant structured data** (matching the OKB JSON Schema definitions).

Entity data is stored as JSON files under `data/` (configurable via `DATA_PATH`). Seed data for the loan approval scenario is included in `data/projects/`, `data/datasets/`, and `data/models/`.

---

## Project Structure

```
src/compliance_agent/
├── config.py            # Settings (env / .env file via Pydantic Settings)
├── store.py             # Generic JSON file EntityStore
├── stores.py            # Shared EntityStore singletons (projects, datasets, models)
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
├── data/
│   ├── projects/        # Stored project JSON files
│   ├── datasets/        # Stored dataset JSON files
│   └── models/          # Stored model JSON files
├── agent/
│   ├── tools.py         # 9 LangChain @tool functions for OKF bundle navigation
│   ├── schemas.py       # Pydantic output schemas matching OKB definitions
│   └── agent.py         # ComplianceAgent class with 3 analysis tasks
├── api/
│   ├── models.py        # FastAPI request/entity models
│   ├── crud.py          # CRUD router for entity management
│   └── main.py          # FastAPI application
└── ui/
    └── app.py           # Streamlit 3-tab demonstration UI
```

---

## Quick Start

### 1. Install dependencies

```bash
cd src/compliance_agent
pip install -r requirements.txt
```

### 2. Configure the LLM provider

```bash
cp .env.example .env
# Edit .env — set your API key and preferred provider
```

See the [Configuration](#configuration) section for all available settings.

### 3. Start the API server

```bash
cd src/compliance_agent
python -m api.main
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 4. Start the Streamlit UI (separate terminal)

```bash
cd src/compliance_agent
streamlit run ui/app.py
# UI available at http://localhost:8501
```

---

## Configuration

All settings are loaded from `.env` (or environment variables).

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | API key for the LLM endpoint |
| `OPENAI_MODEL` | `gpt-4o` | Model identifier |
| `OPENAI_BASE_URL` | *(empty — OpenAI)* | Override base URL for non-OpenAI endpoints |
| `OKF_BUNDLE_PATH` | `../../../okf` | Absolute path to the OKF bundle |
| `AGENT_MAX_ITERATIONS` | `20` | Maximum reasoning steps before the agent gives up |
| `AGENT_VERBOSE` | `true` | Pass-through to LangChain's verbose flag |
| `LOG_LEVEL` | `INFO` | Log level for the tools module (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Only `agent.tools` emits at this level; all other loggers are silenced at `WARNING`. |
| `API_HOST` | `0.0.0.0` | Host the FastAPI server binds to |
| `API_PORT` | `8000` | Port the FastAPI server listens on |
| `API_BASE_URL` | `http://localhost:8000` | Backend URL used by the Streamlit UI |

---

## LLM Providers

The agent uses an OpenAI-compatible HTTP interface. Set `OPENAI_BASE_URL` to point at any compatible endpoint:

### OpenAI (default)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### LiteLLM proxy (local — see `litellm/docker-compose.yml`)

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=http://localhost:4000
OPENAI_MODEL=github_copilot/gpt-4o   # any model the proxy exposes
```

### Ollama

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3
```

### LM Studio

```env
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=local-model
```

### GitHub Copilot / GitHub Models

Both endpoints are OpenAI-compatible; use a GitHub PAT (`models:read` scope) as the key.

**GitHub Models Marketplace** (no Copilot subscription required):

```env
OPENAI_API_KEY=ghp_...   # GitHub PAT with models:read scope
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_MODEL=gpt-4o     # also: claude-sonnet-4-5, gemini-2.0-flash, o1-mini, …
```

**GitHub Copilot chat API** (requires active Copilot subscription):

```env
OPENAI_API_KEY=ghp_...
OPENAI_BASE_URL=https://api.githubcopilot.com
OPENAI_MODEL=gpt-4o
```

To create a PAT: `GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens`


```env
OPENAI_API_KEY=ghp_...                                  # PAT with models:read scope
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_MODEL=gpt-4o     # also: claude-sonnet-4-5, gemini-2.0-flash, o1-mini, …
```

**GitHub Copilot chat API** (requires active Copilot subscription):

```env
OPENAI_API_KEY=ghp_...
OPENAI_BASE_URL=https://api.githubcopilot.com
OPENAI_MODEL=gpt-4o
```

To create a PAT: `GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens`

---

## API Reference

Compliance analysis endpoints read entity data from storage by ID. Create entities first via the CRUD endpoints or by placing JSON files in `data/{projects,datasets,models}/`.

### `POST /compliance/context/{project_id}`

Build a `ComplianceContext` for a stored project.

**Response** (`ComplianceContextResponse`):

```json
{
  "narrative_summary": "...",
  "regulatory_analysis": "...",
  "risk_analysis": "...",
  "oversight_analysis": "...",
  "compliance_context": {
    "environment": "PRODUCTION",
    "regulations": [{ "framework": "EU_AI_ACT", "article": "Art. 10", ... }],
    "requirements": [...],
    "affected_groups": [...],
    "vulnerable_groups": [...],
    "protected_attributes": [...],
    "foreseeable_misuse": [...],
    "risk_classification": { "risk_level": "HIGH", ... },
    "human_oversight": { "oversight_mode": "HUMAN_IN_THE_LOOP", ... }
  }
}
```

---

### `POST /compliance/dataset/{dataset_id}`

Analyse dataset compliance and suggest `ComplianceObjective` instances.

**Response** (`DataComplianceResponse`):

```json
{
  "narrative_summary": "...",
  "data_quality_analysis": "...",
  "privacy_analysis": "...",
  "fairness_analysis": "...",
  "scope": "TRAINING",
  "protected_attributes": [...],
  "objectives": [
    {
      "name": "Demographic Parity Difference ≤ 0.05",
      "metric": { "id": "metric-demographic-parity-difference", ... },
      "condition": { "threshold": { "operator": "LEQ", "value": 0.05 } },
      "priority": "MANDATORY",
      "severity": "HIGH",
      "requirements": ["req-euai-art-10"]
    }
  ]
}
```

---

### `POST /compliance/model/{model_id}?project_id={project_id}`

Analyse model compliance and suggest `ComplianceObjective` instances.

The optional `project_id` query parameter loads the corresponding project from storage and passes it as additional context to the agent.

**Response** (`ModelComplianceResponse`):

```json
{
  "narrative_summary": "...",
  "fairness_analysis": "...",
  "robustness_analysis": "...",
  "transparency_analysis": "...",
  "objectives": [...]
}
```

---

### CRUD endpoints — `GET|POST|PUT|DELETE /entities/{projects|datasets|models}`

Full CRUD for entity management. See the interactive docs at <http://localhost:8000/docs>.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/entities/projects` | List all projects |
| `POST` | `/entities/projects` | Create a project (returns `id`) |
| `GET` | `/entities/projects/{id}` | Get a project |
| `PUT` | `/entities/projects/{id}` | Replace a project |
| `DELETE` | `/entities/projects/{id}` | Delete a project |

Same pattern for `/entities/datasets` and `/entities/models`.

---

## OKF Navigation Tools

The agent uses these tools to navigate the compliance knowledge bundle without loading it all
into context at once:

| Tool | Bundle path navigated | Purpose |
|------|-----------------------|---------|
| `list_okf_directory(path)` | `{path}/index.md` | Discover concepts in a directory |
| `read_okf_concept(path)` | `{path}` | Read one concept file |
| `search_catalog(query, category)` | `catalog/**` | Keyword search across catalog |
| `get_regulatory_refs(frameworks)` | `catalog/regulatory-refs/` | List regulatory references |
| `get_requirements(framework, article)` | `catalog/requirements/{framework}/` | List requirements |
| `get_groups(keyword)` | `catalog/groups/` | List population groups |
| `get_attributes(concern)` | `catalog/attributes/` | List protected attributes |
| `get_metrics(concern_area, applies_to)` | `catalog/metrics/{area}/` | List metrics |
| `get_misuse_scenarios(keyword)` | `catalog/misuse-scenarios/` | List misuse scenarios |

The agent follows a **lazy navigation strategy**: it browses index files first, then reads
individual concept files only when needed.

---

## OKF Bundle

The agent reads from the OKF bundle rooted at `../okf/` (configurable via `OKF_BUNDLE_PATH`).
The bundle contains:

- **14 regulatory references** — EU AI Act, GDPR, DSA, NIS2, EU Data Act, EU Charter, CoE AI Convention, UNESCO, ISO 42001/23894/TR 24027, NIST AI RMF/100-2, EBA/ECB ML, AgID LLGG, Garante Privacy
- **46+ requirements** — from EU AI Act, GDPR, DSA, NIS2, EU Charter, UNESCO, ISO 42001 Annex A, EBA/ECB ML
- **19 population groups** — vulnerable, protected, occupational, and system-interaction groups
- **22 protected attributes** — GDPR special categories, EU AI Act/Charter characteristics, AI-derived scores
- **18 misuse scenarios** — societal, operational, adversarial, privacy, and platform misuse
- **40 metrics** — fairness (8), data quality (6), performance (6), robustness (4), explainability (5), calibration (3), privacy (5), environmental (3)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `langchain` · `langchain-core` | Agent framework |
| `langchain-openai` | OpenAI-compatible LLM (OpenAI, GitHub Models, Ollama, LiteLLM, …) |
| `langgraph` | Agent graph execution |
| `fastapi` · `uvicorn` | HTTP API server |
| `pydantic` · `pydantic-settings` | Data validation and config |
| `python-frontmatter` | OKF `.md` frontmatter parsing |
| `streamlit` | Demonstration UI |
| `httpx` | HTTP client (used by UI → API calls) |
