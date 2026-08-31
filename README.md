# ai-compliance-agent

LangChain-based agent that navigates an [Open Knowledge Framework (OKF)](okf/) compliance bundle to suggest `ComplianceContext`, data compliance objectives, and model compliance objectives for AI systems.

## Requirements

- Python 3.11+
- Access to an OpenAI-compatible LLM endpoint (OpenAI, Azure OpenAI, GitHub Models, Ollama, LM Studio, vLLM, or a [LiteLLM](litellm/) proxy)

## Setup

```bash
cd src/compliance_agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env with your values
```

## Configuration

All settings are loaded from `src/compliance_agent/.env` (or environment variables). Copy `.env.example` as a starting point.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | API key for the LLM endpoint |
| `OPENAI_MODEL` | `gpt-4o` | Model identifier |
| `OPENAI_BASE_URL` | *(empty — OpenAI)* | Override base URL for non-OpenAI endpoints (see examples below) |
| `OKF_BUNDLE_PATH` | `../../../okf` | Absolute path to the OKF bundle; defaults to the `okf/` folder at the repo root |
| `AGENT_MAX_ITERATIONS` | `20` | Maximum reasoning steps before the agent gives up |
| `AGENT_VERBOSE` | `true` | Pass-through to LangChain's verbose flag |
| `LOG_LEVEL` | `INFO` | Log level for the tools module (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Only `agent.tools` logs at this level; all other loggers are silenced at `WARNING`. |
| `API_HOST` | `0.0.0.0` | Host the FastAPI server binds to |
| `API_PORT` | `8000` | Port the FastAPI server listens on |
| `API_BASE_URL` | `http://localhost:8000` | Backend URL used by the Streamlit UI |

### Common `OPENAI_BASE_URL` values

```
http://localhost:4000          # LiteLLM proxy (see litellm/docker-compose.yml)
http://localhost:11434/v1      # Ollama
http://localhost:1234/v1       # LM Studio
https://models.inference.ai.azure.com  # GitHub Models (use a GitHub PAT as the key)
```

## Running

**API server** (from `src/compliance_agent/`):

```bash
python -m api.main
```

Swagger UI available at <http://localhost:8000/docs>.

**Streamlit UI** (from `src/compliance_agent/`):

```bash
streamlit run ui/app.py
```

## Tests

```bash
pytest
```
