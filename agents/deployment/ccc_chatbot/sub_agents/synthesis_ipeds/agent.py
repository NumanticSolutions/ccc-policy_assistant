# CCC Policy Assistants
# Agent to synthesize search results from other agents
# Steve Godfrey
# August 2025

import os, sys

from google.adk.agents import Agent

from . import prompt

root_agent = Agent(
    name=prompt.synthesis_ipeds_agent_name,
    model=prompt.synthesis_ipeds_model_name,
    description=prompt.synthesis_ipeds_agent_description,
    instruction=prompt.synthesis_ipeds_agent_instruction
)
