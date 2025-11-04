from pydantic import BaseModel, Field
from typing import List


class Reference(BaseModel):
    """
    Pydantic object for a reference in the policy report
    """
    organization: str = Field(description="The name of the organization providing the reference material")
    uri: str = Field(description="The URI or the referenced material")

class InputContent(BaseModel):
    """
    Pydantic object for input content needed to generate  synthesized policy report
    """
    report_material: str = Field(description="Material relevant to the report's topic")
    report_references: List[Reference] = Field(description="A list of reference sources for the policy report")

class PolicyReport(BaseModel):
    """
    Pydantic object for a synthesized policy report
    """
    report_title: str = Field(description="The policy report's title")
    report_executive_summary: str = Field(description="An executive summary of the report's content")
    report_body: str = Field(description="The policy report's main body of content")
    report_references: List[Reference] = Field(description="A list of reference sources for the policy report")


