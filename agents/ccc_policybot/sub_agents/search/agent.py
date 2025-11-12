# CCC Policy Assistants
# Google search agent
# Steve Godfrey
# August 2025

import os, sys
from google.adk.agents import Agent
from google.adk.tools import google_search

from . import prompt

# Authentication tools - needed for local testing
if 'USER' in os.environ.keys():
    if os.environ['USER'] == 'numantic':
        utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
    elif os.environ['USER'] == 'stephengodfrey':
        utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."

    sys.path.insert(0, utils_path)
    from utilities.osa_tools.authentication import ApiAuthentication
    api_configs = ApiAuthentication(client="CCC")

root_agent = Agent(
    name=prompt.search_agent_name,
    model=prompt.search_model_name,
    description=prompt.search_agent_description,
    instruction=prompt.search_agent_instruction,
    tools=[google_search]
)
