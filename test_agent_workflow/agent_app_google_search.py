
import os, sys
import requests
import json
import google.auth
from google.auth.transport.requests import Request

# import vertexai
from vertexai import agent_engines

# Set environment variables
utils_path = "utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
api_configs = ApiAuthentication(client="CCC")


class readGoogleSearchResults:
    '''
    Class to read and parse Google AI Search agent App results

    '''

    def __init__(self,
                 query: str,
                 user_id: str):
        '''
        Initialize class
        '''

        # Get the agent name
        self.resource_name = "projects/eternal-bongo-435614-b9/locations/us-central1/reasoningEngines/8448585775179628544"

        # Users's query
        self.query = query
        self.user_id = user_id

        # Call the API
        self.call_agent()

        # Parse the response
        self.parse_response()

    def call_agent(self):
        '''
        Call the API to get search results for user's query
        '''

        # Retrieve agent
        self.agent_engine = agent_engines.get(self.resource_name)

        # Establish session
        self.session = self.agent_engine.create_session(user_id=self.user_id)

        # Get agent response
        self.result = self.agent_engine.stream_query(message=self.query,
                                                     session_id=self.session["id"],
                                                     user_id=self.user_id)

        # Put results into a dictionary for later access
        self.events = []
        for event in self.result:
            self.events.append(event)


    def parse_response(self):
        '''
        Method to parse response into the elements of interest
        '''

        self.domains = []
        self.uris = []
        self.contents = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            self.contents.append(txt_dict["text"])

            # Find domains and URIs from grounding_metadata
            uri_index = 0
            for gc in event["grounding_metadata"]["grounding_chunks"]:
                for key in gc.keys():
                    if key == "web":
                        self.domains.append(gc["web"]["domain"])
                        self.uris.append(dict(uri_index=uri_index,
                                              uri=gc["web"]["uri"],
                                              uri_text=gc["web"]["domain"])
                                         )
                        uri_index += 1

        self.domains = list(set(self.domains))
