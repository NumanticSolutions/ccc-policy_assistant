# CCC Policy Assistants
# Agent to synthesize search results from other agents
# Steve Godfrey
# August 2025

import os, sys

from google.adk.agents import Agent

from . import prompt

# import os, sys
# if "GOOGLE_API_KEY" not in os.environ.keys():
#     utils_path = "../../../interface/utils"
#     sys.path.insert(0, utils_path)
#     from authentication import ApiAuthentication
#     api_configs = ApiAuthentication(client="CCC")

root_agent = Agent(
    name=prompt.synthesis_ipeds_agent_name,
    model=prompt.synthesis_ipeds_model_name,
    description=prompt.synthesis_ipeds_agent_description,
    instruction=prompt.synthesis_ipeds_agent_instruction
)
