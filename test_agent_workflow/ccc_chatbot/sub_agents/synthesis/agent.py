

from google.adk.agents import Agent

from . import prompt

root_agent = Agent(
    name=prompt.synthesis_agent_name,
    model=prompt.synthesis_model_name,
    description=prompt.synthesis_agent_description,
    instruction=prompt.synthesis_agent_instruction
)
