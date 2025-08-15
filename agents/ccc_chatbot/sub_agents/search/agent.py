# CCC Policy Assistants
# Google search agent
# Steve Godfrey
# August 2025


from google.adk.agents import Agent
from google.adk.tools import google_search

from . import prompt

# import os, sys
# if "GOOGLE_API_KEY" not in os.environ.keys():
#     api_configs = ApiAuthentication(client="CCC")

root_agent = Agent(
    name=prompt.search_agent_name,
    model=prompt.search_model_name,
    description=prompt.search_agent_description,
    instruction=prompt.search_agent_instruction,
    tools=[google_search]
)
