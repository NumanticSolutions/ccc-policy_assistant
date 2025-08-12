# CCC Policy Assistants
# Agent to synthesize search results from other agents
# Steve Godfrey
# August 2025


from google.adk.agents import Agent

from . import prompt

root_agent = Agent(
    name=prompt.synthesis_agent_name,
    model=prompt.synthesis_model_name,
    description=prompt.synthesis_agent_description,
    instruction=prompt.synthesis_agent_instruction
)
