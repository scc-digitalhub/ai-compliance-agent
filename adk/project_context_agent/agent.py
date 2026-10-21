from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool, FunctionTool, skill_toolset
from google.adk.skills import load_skill_from_dir
from google.adk.planners import BuiltInPlanner
from google.genai import types

from google.adk.models.lite_llm import LiteLlm
import os
import pathlib

from schema import ComplianceContextOut, ProjectInput
from tools import list_all_concepts, list_okf_directory, search_catalog, read_okf_concept, get_regulatory_refs, get_requirements, get_groups, get_attributes, get_metrics, get_misuse_scenarios


project_context_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "project-context"
)
compliance_framework_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "compliance-framework"
)

compliance_skill_toolset = skill_toolset.SkillToolset(
    skills=[compliance_framework_skill],
    additional_tools=[
        FunctionTool(list_all_concepts),
        FunctionTool(list_okf_directory),
        FunctionTool(search_catalog),
        FunctionTool(read_okf_concept),
        FunctionTool(get_regulatory_refs),
        FunctionTool(get_requirements),
        FunctionTool(get_groups),
        FunctionTool(get_attributes),
        FunctionTool(get_metrics),
        FunctionTool(get_misuse_scenarios),
    ],
)

project_context_skill_toolset = skill_toolset.SkillToolset(
    skills=[project_context_skill],
    additional_tools=[
        FunctionTool(list_all_concepts),
        FunctionTool(list_okf_directory),
        FunctionTool(search_catalog),
        FunctionTool(read_okf_concept),
        FunctionTool(get_regulatory_refs),
        FunctionTool(get_requirements),
        FunctionTool(get_groups),
        FunctionTool(get_attributes),
        FunctionTool(get_metrics),
        FunctionTool(get_misuse_scenarios),
    ],
)

root_agent = Agent(
    model=LiteLlm(model=os.getenv('PROJECT_CONTEXT_AGENT_MODEL_NAME')),
    name='project_context_agent',
    description='Creates a structured AI project compliance context information',
    instruction="""\
You are an AI Compliance Expert with deep knowledge of EU AI Act, GDPR, NIST AI
RMF, ISO 42001, and related standards. You have access to an Open Knowledge
Format (OKF) bundle of compliance concepts, catalog instances, metrics, and
requirements. 

Answer ONLY to structured input in JSON format representing the AI project metadata. Otherwise respond with an error JSON structure.

Respond ONLY with the JSON content generated; no narrative parts, no explanations, no markdown, no prose.
    """,
    tools=[
        project_context_skill_toolset
    ],
    input_schema=ProjectInput,
    output_schema=ComplianceContextOut,
    output_key="compliance_context",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=0,
            thinking_level=types.ThinkingLevel.MINIMAL,
        )
    ),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2
    )
)

