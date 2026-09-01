"""
LangChain compliance agent.

Architecture:
  1. A LangGraph ReAct agent navigates the OKF bundle using tools to gather facts.
  2. A second structured-output LLM call extracts the validated Pydantic result.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from config import settings
from agent.tools import ALL_TOOLS
from agent.schemas import (
    ComplianceContextResponse,
    DataComplianceResponse,
    ModelComplianceResponse,
)

logger = logging.getLogger(__name__)


# ── LLM factory ───────────────────────────────────────────────────────────────

def _make_llm(temperature: float = 0.0):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
    )


# ── Shared agent system prompt ────────────────────────────────────────────────

_AGENT_SYSTEM = """\
You are an AI Compliance Expert with deep knowledge of EU AI Act, GDPR, NIST AI
RMF, ISO 42001, and related standards. You have access to an Open Knowledge
Format (OKF) bundle of compliance concepts, catalog instances, metrics, and
requirements.

PREFERRED APPROACH — always try the OKF tools first:
- Use the specialised tools (get_regulatory_refs, get_requirements, get_groups,
  get_attributes, get_metrics, get_misuse_scenarios) to retrieve grounded facts.
- Supplement with your general knowledge only when the OKF bundle does not
  contain the concept you need.

NAVIGATION STRATEGY — always navigate lazily:
1. Call list_okf_directory to browse a category before reading individual files.
2. Call search_catalog to narrow down to relevant concepts.
3. Call read_okf_concept only for files you definitely need.
4. Use specialised tools before falling back to search_catalog.

When you have gathered enough information, provide a comprehensive analysis that
covers both narrative explanations and structured data.
"""


def _build_graph():
    # create_react_agent handles the tool-calling loop and scratchpad internally
    return create_react_agent(_make_llm(), ALL_TOOLS, prompt=_AGENT_SYSTEM)


# ── Structured extraction ──────────────────────────────────────────────────────

def _extract_structured(narrative: str, schema_cls, task_hint: str) -> Any:
    """Run a second LLM call to extract validated Pydantic output from narrative.

    Tries with_structured_output first (works for OpenAI); falls back to
    explicit JSON prompting + manual parse for models that ignore tool schemas
    (e.g. Claude via LiteLLM proxy).
    """
    llm = _make_llm(temperature=0.0)
    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
    prompt = (
        f"Based on the following compliance analysis, extract all relevant information "
        f"and return it as a valid JSON object that exactly matches the "
        f"{schema_cls.__name__} schema below.\n\n"
        f"Task context: {task_hint}\n\n"
        f"Required JSON Schema:\n{schema_json}\n\n"
        f"Analysis:\n{narrative}\n\n"
        f"Return ONLY the JSON object — no markdown, no prose, no code fences."
    )
    try:
        return llm.with_structured_output(schema_cls).invoke(prompt)
    except Exception as exc:
        # Fallback for models that return plain text instead of a tool call
        logger.warning("with_structured_output failed (%s); retrying with raw JSON parse", exc)
        raw = llm.invoke(prompt).content
        # Strip markdown code fences if the model wrapped the JSON anyway
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        text = m.group(1).strip() if m else raw.strip()
        return schema_cls.model_validate_json(text)


# ── Public agent class ─────────────────────────────────────────────────────────

class ComplianceAgent:
    """Singleton compliance agent. Call `get()` instead of constructing directly."""

    _instance: ComplianceAgent | None = None

    def __init__(self) -> None:
        self._graph = _build_graph()

    @classmethod
    def get(cls) -> ComplianceAgent:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _run(self, input_text: str) -> str:
        """Invoke the LangGraph agent and return the final assistant message."""
        result = self._graph.invoke(
            {"messages": [HumanMessage(content=input_text)]},
            config={"recursion_limit": settings.agent_max_iterations * 2},
        )
        return result["messages"][-1].content

    def build_compliance_context(self, project: dict) -> ComplianceContextResponse:
        """Given project metadata, suggest a ComplianceContext."""
        input_text = f"""\
TASK: Build a ComplianceContext for the following AI project.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Project information:
{json.dumps(project, indent=2)}

Steps to follow:
1. Identify the deployment geography and applicable regulatory frameworks.
   - Call get_regulatory_refs() to retrieve EU AI Act, GDPR, DSA/NIS2 if relevant.
   - Determine the EU AI Act risk classification based on the AI task and domain.

2. Retrieve relevant normative requirements.
   - Call get_requirements('eu-ai-act') and get_requirements('gdpr').
   - Select the requirements applicable to the project's risk level and domain.
   - Also check iso-42001-annex-a, dsa, nis2, eba-ml as needed.

3. Identify affected and vulnerable groups.
   - Call get_groups() to find groups impacted by the AI task and domain.

4. Identify protected attributes.
   - Call get_attributes() based on the domain and task.

5. Identify foreseeable misuse scenarios.
   - Call get_misuse_scenarios() relevant to the domain and deployment.

6. Suggest a human oversight profile appropriate for the risk level.

7. Synthesise a full compliance analysis covering: applicable regulations,
   key requirements, groups, attributes, misuse risks, oversight, and risk level.
   Include both a narrative explanation and the structured data.
"""
        narrative = self._run(input_text)
        return _extract_structured(
            narrative,
            ComplianceContextResponse,
            f"Project: {project.get('domain', '')} / {project.get('ai_task', '')}",
        )

    def analyze_dataset(self, dataset: dict) -> DataComplianceResponse:
        """Given dataset metadata, schema, and samples, suggest compliance objectives."""
        input_text = f"""\
TASK: Analyse the compliance requirements for the following AI dataset.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Dataset information:
{json.dumps(dataset, indent=2)}

Steps to follow:
1. Identify the dataset's role (training / validation / test) and sensitivity.
   - Call read_okf_concept('data/DataGovernance.md') and read_okf_concept('data/ConsentSpec.md') if needed.

2. Identify protected and sensitive attributes present in the dataset schema.
   - Call get_attributes() to match schema field names to known AttributeRef instances.
   - Flag GDPR Art. 9 special categories if present.

3. Select relevant data quality and fairness objectives.
   - Call get_metrics('data-quality') to identify applicable data quality metrics.
   - Call get_metrics('fairness') to identify fairness metrics given the protected attributes.
   - Call get_metrics('privacy') if sensitive data is present.

4. Retrieve the applicable requirements.
   - Call get_requirements('eu-ai-act', 'art10') for data governance.
   - Call get_requirements('gdpr') for personal data (Art. 5, 6, 9, 25, 35 as applicable).

5. For each relevant metric, propose a concrete ComplianceObjective with:
   - The metric id and name.
   - An acceptance condition (threshold or range).
   - Priority (MANDATORY for safety/legal requirements, RECOMMENDED otherwise).
   - Linked requirement ids.

6. Provide narrative analysis covering: data quality, privacy, fairness, and
   retention/consent concerns.
"""
        narrative = self._run(input_text)
        return _extract_structured(
            narrative,
            DataComplianceResponse,
            f"Dataset: {dataset.get('name', '')} / scope={dataset.get('scope', '')}",
        )

    def analyze_model(self, model: dict, requirements: list[dict] | None = None) -> ModelComplianceResponse:
        """Given model metadata and project requirements, suggest compliance objectives."""
        req_hint = (
            "\n\nProject requirements already identified:\n"
            + json.dumps(requirements, indent=2)
            if requirements
            else ""
        )
        input_text = f"""\
TASK: Analyse the compliance requirements for the following AI model.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Model information:
{json.dumps(model, indent=2)}
{req_hint}

Steps to follow:
1. Determine the applicable compliance concern areas based on the AI task:
   - For classification/regression: fairness, calibration, performance.
   - For generative models: privacy, robustness, explainability.
   - For all models: performance, robustness, explainability.

2. Retrieve relevant metrics for each concern area:
   - Call get_metrics('fairness') for models making decisions about individuals.
   - Call get_metrics('performance') for accuracy/recall requirements.
   - Call get_metrics('robustness') for adversarial and distribution-shift risks.
   - Call get_metrics('explainability') for transparency requirements.
   - Call get_metrics('calibration') for probabilistic output models.
   - Call get_metrics('privacy') if trained on sensitive data.

3. Read specific metric concept files to get acceptance thresholds and code.

4. For each metric, create a ComplianceObjective with:
   - Concrete acceptance condition (e.g. EOD ≤ 0.05, AUC ≥ 0.85).
   - Appropriate priority and severity.
   - Links to EU AI Act Art. 10, 13, 14, 15 as applicable.

5. Call get_misuse_scenarios() to identify foreseeable misuse and adversarial risks
   relevant to the model type.

6. Provide narrative analysis covering: fairness, robustness, transparency,
   and calibration concerns.
"""
        narrative = self._run(input_text)
        return _extract_structured(
            narrative,
            ModelComplianceResponse,
            f"Model: {model.get('name', '')} / task={model.get('ai_task', '')}",
        )
