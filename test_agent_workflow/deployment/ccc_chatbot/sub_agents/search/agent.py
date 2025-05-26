import os, sys

from google.adk.agents import Agent
from google.adk.tools import google_search

from . import prompt


root_agent = Agent(
    name=prompt.search_agent_name,
    model=os.environ["GEMINI_MODEL"],
    description=prompt.search_agent_description,
    instruction=prompt.search_agent_instruction,
    tools=[google_search]
)
