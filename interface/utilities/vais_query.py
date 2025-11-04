# © 2025 Numantic Solutions LLC
# MIT License
#
# Query a Vertex AI Search App

# https://cloud.google.com/enterprise-search?hl=en
# https://cloud.google.com/generative-ai-app-builder/docs/preview-search-results?hl=en&_gl=1*1hjqten*_ga*MTgxNDQ4NTkwLjE3NDk2NjEwMDg.*_ga_WH2QY8WWF5*czE3NjE1MTk4NDUkbzE2NCRnMCR0MTc2MTUxOTg0NSRqNjAkbDAkaDA


import os, sys
import time
import json

import pandas as pd
from google.cloud.discoveryengine_v1 import SearchServiceClient, SearchRequest
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine


class QueryVaiSearch:
    """
    Object to query using an existing Vertex AI Search App. Note, the Search App and its supporting
    Data Stores need to have been previously created.

    References:
        Vertex AI Search: https://cloud.google.com/enterprise-search?hl=en

    """

    def __init__(self,
                 search_app_id: str,
                 gcp_project:str="",
                 gcp_location:str="",
                 **kwargs
                 ):
        """
        Instantiate class.
        """

        # GCP parameters
        self.gcp_project = gcp_project
        self.gcp_location = gcp_location
        self.search_app_id = search_app_id

        # Search App parameters
        # self.gcp_project = "779629487479"
        self.serving_config = ("projects/{}/locations/{}/collections/default_collection/"
                               "engines/{}/servingConfigs/default_search").format(self.gcp_project,
                                                                                  self.gcp_location,
                                                                                  self.search_app_id)

        # Search parameters
        self.return_snippet = True
        self.summary_result_count = 5
        self.include_citations = True
        self.ignore_adversarial_query = True
        self.ignore_non_summary_seeking_query = True

        self.preamble = "Search the data store and return text that is similar to the query"
        self.model_version = "stable"

        self.page_size = 10

        # Update any key word args
        self.__dict__.update(kwargs)

        # Authenticate
        self.authenticate()

    def authenticate(self):
        """
        Authenticate with Google Cloud

        """
        ### Step 1: Set up client options
        client_options = (
            ClientOptions(api_endpoint=f"{self.gcp_location}-discoveryengine.googleapis.com")
            if self.gcp_location != "global"
            else None
        )

        ### Step 2. Initialize the Search Service Client
        self.client = SearchServiceClient(client_options=client_options)

    def search_vertex_ai_app(self,
                             query: str):
        """
        Performs a search request against a Vertex AI Search App.
        """

        ### Step 1. Construct the Search Request
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=self.return_snippet
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=self.summary_result_count,
                include_citations=self.include_citations,
                ignore_adversarial_query=self.ignore_adversarial_query,
                ignore_non_summary_seeking_query=self.ignore_non_summary_seeking_query,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                    preamble=self.preamble
                ),
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version=self.model_version,
                ),
            ),
        )

        ### Step 2. Construct the Search Request
        request = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=self.page_size,
            content_search_spec=content_search_spec,
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )

        ### Step 3. Execute the Search
        self.response = self.client.search(request=request)

        ### Step 4. Extract structured data into a dataframe
        self.extract_structured_data()

    def extract_structured_data(self):
        """
        Extract structured data after completing a query.
        :return:
            Pandas dataframe with structured data
        """

        # A list of structured data keys
        # These are the expected structured data keys which correspond to BigQuery columns
        self.struct_data_keys = []

        results_list = []
        for result in self.response.results:

            strut_data_result_dict = {}

            strut_data_result_dict["id"] = result.document.id
            strut_data_result_dict["name"] = result.document.name

            # Get the structured data content for this key
            for key in result.document.struct_data.keys():

                # Vlaues stored in proto.marshal.collections.maps.MapComposite object
                if isinstance(result.document.struct_data[key], type(result.document.struct_data)):
                    items_dict = {i[0]: i[1] for i in result.document.struct_data[key].items()}
                    strut_data_result_dict[key] = json.dumps(items_dict)

                else:
                    strut_data_result_dict[key] = result.document.struct_data[key]

            # Add it to a list
            results_list.append(strut_data_result_dict)

        self.struct_data_df = pd.DataFrame(data=results_list)

