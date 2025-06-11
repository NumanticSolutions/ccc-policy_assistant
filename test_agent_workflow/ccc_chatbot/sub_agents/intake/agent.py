

from google.adk.agents import Agent

from . import prompt

root_agent = Agent(
    name=prompt.intake_agent_name,
    model=prompt.intake_model_name,
    description=prompt.intake_agent_description,
    instruction=prompt.intake_agent_instruction
)