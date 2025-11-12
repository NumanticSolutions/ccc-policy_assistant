# CCC Policy Assistants
# Agent to synthesize search results from other agents
# Steve Godfrey
# August 2025

import os, sys
from google.adk.agents import Agent

from . import prompt
from . import data_models as dms

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
    name=prompt.synthesis_agent_name,
    model=prompt.synthesis_model_name,
    description=prompt.synthesis_agent_description,
    instruction=prompt.synthesis_agent_instruction,
    output_schema=dms.PolicyReport,
)
