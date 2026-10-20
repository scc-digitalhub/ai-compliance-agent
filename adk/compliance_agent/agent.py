from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool, FunctionTool, skill_toolset
from google.adk.skills import load_skill_from_dir
from google.adk.planners import BuiltInPlanner
from google.genai import types

from google.adk.models.lite_llm import LiteLlm
import os
import pathlib

from tools import list_all_concepts, list_okf_directory, search_catalog, read_okf_concept, get_regulatory_refs, get_requirements, get_groups, get_attributes, get_metrics, get_misuse_scenarios


project_context_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "project-context"
)
compliance_framework_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "compliance-framework"
)
data_analysis_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "dataset-analysis"
)
model_analysis_skill = load_skill_from_dir(
    pathlib.Path(os.getcwd()) / "skills" / "model-analysis"
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


data_analysis_skill_toolset = skill_toolset.SkillToolset(
    skills=[data_analysis_skill],
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

model_analysis_skill_toolset = skill_toolset.SkillToolset(
    skills=[model_analysis_skill],
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

project_context_agent = Agent(
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
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=0,
            thinking_level=types.ThinkingLevel.MINIMAL,
        )
    )
)
project_context_tool = AgentTool(project_context_agent)

data_analysis_agent = Agent(
    model=LiteLlm(model=os.getenv('DATA_ANALYSIS_AGENT_MODEL_NAME')),
    name='data_analysis_agent',
    description='Analyzes AI dataset compliance aspects',
    instruction="""\
You are an AI Compliance Expert specialized in dataset analysis. You have access to an Open Knowledge
Format (OKF) bundle of compliance concepts, catalog instances, metrics, and requirements.

Answer ONLY to structured input in JSON format representing the dataset metadata. Otherwise respond with an error JSON structure.

Respond ONLY with the JSON content generated; no narrative parts, no explanations, no markdown, no prose.
    """,
    tools=[
        data_analysis_skill_toolset
    ],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=0,
            thinking_level=types.ThinkingLevel.MINIMAL,
        )
    )
)
data_analysis_tool = AgentTool(data_analysis_agent)

model_analysis_agent = Agent(
    model=LiteLlm(model=os.getenv('MODEL_ANALYSIS_AGENT_MODEL_NAME')),
    name='model_analysis_agent',
    description='Analyzes AI model compliance aspects',
    instruction="""\
You are an AI Compliance Expert specialized in AI/ML model analysis. You have access to an Open Knowledge
Format (OKF) bundle of compliance concepts, catalog instances, metrics, and requirements.

Answer ONLY to structured input in JSON format representing the AI model metadata. Otherwise respond with an error JSON structure.

Respond ONLY with the JSON content generated; no narrative parts, no explanations, no markdown, no prose.
    """,
    tools=[
        model_analysis_skill_toolset
    ],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=0,
            thinking_level=types.ThinkingLevel.MINIMAL,
        )
    )
)
model_analysis_tool = AgentTool(model_analysis_agent)

root_agent = Agent(
    model=LiteLlm(model=os.getenv('ROOT_AGENT_MODEL_NAME')),
    name='root_agent',
    description='Creates a structured AI compliance information',
    instruction="""\
You are an AI Compliance Expert with deep knowledge of EU AI Act, GDPR, NIST AI
RMF, ISO 42001, and related standards. You have access to an Open Knowledge
Format (OKF) bundle of compliance concepts, catalog instances, metrics, and
requirements.  

PREFERRED APPROACH FOR PLANNING - always prefer skills and specialized tools that fits the requested task over general knowledge.
- for defining the AI project compliance context in a structured manner use the project_context_tool tool.
- for analyzing AI compliance-related aspects of datasets always use the data_analysis_tool.
- for explaining the concepts of the compliance framework and their meaning always use the compliance-framework skill.

PREFERRED APPROACH TO INFORMATION RETRIEVAL — always try the OKF tools first:
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
    """,
    tools=[
        compliance_skill_toolset,
        project_context_tool,
        data_analysis_tool,
        model_analysis_tool
    ],
    # planner=BuiltInPlanner(
    #     thinking_config=types.ThinkingConfig(
    #         include_thoughts=False,
    #         thinking_budget=0,
    #         thinking_level=types.ThinkingLevel.MINIMAL,
    #     )
    # )
)
