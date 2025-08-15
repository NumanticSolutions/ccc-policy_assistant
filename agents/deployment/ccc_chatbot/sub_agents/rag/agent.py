# CCC Policy Assistants
# Agent to search curated web text
# Steve Godfrey
# August 2025


# Import libraries
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

from . import prompt

import os, sys
if "GOOGLE_API_KEY" not in os.environ.keys():
    utils_path = "../../../interface/utils"
    sys.path.insert(0, utils_path)
    from authentication import ApiAuthentication
    api_configs = ApiAuthentication(client="CCC")

# Vertex AI Search
vertex_search_tool = VertexAiSearchTool(data_store_id=prompt.vais_datastore_id)

# Agent Definition
root_agent = LlmAgent(
    name=prompt.vais_agent_name,
    model=prompt.vais_model_name,
    tools=[
        vertex_search_tool
    ],
    instruction=prompt.vais_agent_instruction,
    description=prompt.vais_agent_description,
)

