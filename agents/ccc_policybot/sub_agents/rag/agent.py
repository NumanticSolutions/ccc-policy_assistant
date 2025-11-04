# CCC Policy Assistants
# Agent to search curated web text
# Steve Godfrey
# August 2025


# Import libraries
import os, sys
from google.adk.agents import LlmAgent, Agent
from google.adk.tools import VertexAiSearchTool

from . import prompt

# Authentication tools
if "GOOGLE_API_KEY" not in os.environ.keys():
    utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
    sys.path.insert(0, utils_path)
    from utilities.osa_tools.authentication import ApiAuthentication
    api_configs = ApiAuthentication(client="CCC")

# Vertex AI Search
vertex_search_tool = VertexAiSearchTool(search_engine_id=prompt.vais_engine_id,
                                        max_results=4)

# Agent Definition
root_agent = Agent(
    name=prompt.vais_agent_name,
    model=prompt.vais_model_name,
    instruction=prompt.vais_agent_instruction,
    description=prompt.vais_agent_description,
    tools=[
        vertex_search_tool
    ],
)

