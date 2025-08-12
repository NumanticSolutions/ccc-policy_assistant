# CCC Policy Assistants
# Agent to search IPEDS metadata
# Steve Godfrey
# July 2025


# Import libraries
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

from . import prompt

# Vertex AI Search
vertex_search_tool = VertexAiSearchTool(data_store_id=prompt.rag_ipeds_datastore_id)

# Agent Definition
root_agent = LlmAgent(
    name=prompt.rag_ipeds_agent_name,
    model=prompt.rag_ipeds_model_name,
    tools=[
        vertex_search_tool
    ],
    instruction=prompt.rag_iepds_agent_instruction,
    description=prompt.rag_ipeds_agent_description,
)

