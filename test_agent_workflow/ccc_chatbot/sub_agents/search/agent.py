import os, sys

from google.adk.agents import Agent
from google.adk.tools import google_search

from . import prompt


root_agent = Agent(
    name=prompt.search_agent_name,
    model=os.environ["GEMINI_MODEL"],
    instruction=prompt.search_agent_instruction,
    description=prompt.search_agent_description,
    tools=[google_search]
)

