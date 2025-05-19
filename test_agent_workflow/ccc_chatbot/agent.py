import os

from google.adk.agents.llm_agent import Agent


from . import prompt

from .sub_agents import rag_agent
from .sub_agents import search_agent


root_agent = Agent(
    model=os.environ["GEMINI_MODEL"],
    name=prompt.chatbot_agent_name,
    description=prompt.chatbot_agent_description,
    instruction=prompt.chatbot_agent_instruction,
    sub_agents=[
        rag_agent,
        search_agent
    ],
)
