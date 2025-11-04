from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Pydantic object for a search result
    """
    clean_headings_text: str = Field(description="The text content of the search result")
    media_type: str = Field(description="A description of the source content's media, e.g. web page or file")
    page_name: str = Field(description="The source content's page name")
    page_url: str = Field(description="The source content's page URL")
    seed_url: str = Field(description="The source content's seed URL")
