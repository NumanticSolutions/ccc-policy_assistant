import os, sys

from google.adk.agents import Agent

from . import prompt

root_agent = Agent(
    name=prompt.synthesis_agent_name,
    model=os.environ["GEMINI_MODEL"],
    description=prompt.synthesis_agent_description,
    instruction=prompt.synthesis_agent_instruction
)
