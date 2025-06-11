# CCC Policy Assistants
# Agent with multiple tools
# Steve Godfrey
# April 2025

# See https://github.com/google/adk-samples/tree/main/agents



# Import libraries
import os

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import load_memory

from . import prompt

root_agent = LlmAgent(
    model=os.environ["GEMINI_MODEL"],
    description=prompt.memory_agent_description,
    name=prompt.memory_agent_name,
    instruction=prompt.memory_agent_instruction,
    tools=[load_memory]
)



