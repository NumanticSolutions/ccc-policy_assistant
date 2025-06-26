from google.adk.agents import Agent, LlmAgent
from pydantic import BaseModel, Field
from google.genai import types

from . import prompt

# Convenient declaration for controlled generation.
# json_response_config = types.GenerateContentConfig(
#     response_mime_type="application/json"
# )
#
# class PolicyReport(BaseModel):
#     report_title: str = Field(description="Title of the output report.")
#     report_executive_summary: str = Field(description="An executive summary of the report's findings.")
#     report_body: str = Field(description="Body of the output report.")
#     report_references: str = Field(description="References used in the output report.")

# root_agent = Agent(
#     name=prompt.synthesis_agent_name,
#     model=prompt.synthesis_model_name,
#     description=prompt.synthesis_agent_description,
#     instruction=prompt.synthesis_agent_instruction,
#     disallow_transfer_to_parent=True,
#     disallow_transfer_to_peers=True,
#     output_schema=PolicyReport,
#     output_key="synthesis",
#     generate_content_config=json_response_config
# )

root_agent = Agent(
    name=prompt.synthesis_agent_name,
    model=prompt.synthesis_model_name,
    description=prompt.synthesis_agent_description,
    instruction=prompt.synthesis_agent_instruction
)
