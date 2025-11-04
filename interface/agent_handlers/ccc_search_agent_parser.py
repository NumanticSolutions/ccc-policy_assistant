# © 2025 Numantic Solutions LLC
# MIT License
#
# Process responses from the Google search agent

import os, sys
import re
import json
import requests


import vertexai
from vertexai import agent_engines

#### Numantic utilities
try:
    if 'USER' in os.environ.keys() and os.environ['USER'] == 'numantic':
        utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
    elif 'USER' in os.environ.keys() and os.environ['USER'] == 'stephengodfrey':
        utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
    else:
        utils_path = "../utilities/"
except:
    utils_path = "utilities/"
sys.path.insert(0, utils_path)

try:
    from utilities.text_cleaning import json_tools as jt
    from utilities.text_cleaning import text_cleaning_tools as tct
    from utilities.osa_tools.authentication import ApiAuthentication
except:
    import json_tools as jt
    import text_cleaning_tools as tct
    from authentication import ApiAuthentication



class SearchAgentResults:
    '''
    Class to read and parse responses from multiple Google ADK agents

    '''

    def __init__(self,
                 agent: str,
                 query: str,
                 user_id: str,
                 session_id: str,
                 **kwargs):
        '''
        Initialize class
        '''

        # Set the agent server
        # Values:
        #   adk_api_server: Local FastAPI server
        #   vertexai_client: Deployed agent called from a Vertex AI server
        self.agent_server = "vertexai_client"

        # Users's query
        self.query = query
        self.user_id = user_id
        self.session_id = session_id
        self.agent = agent

        # Update any key word args
        self.__dict__.update(kwargs)

        # Validate inputs
        agents = ["search"]
        if self.agent not in agents:
            msg = "The input parameter rag_agent must be in {}".format(agents)
            raise ValueError(msg)

        # Set up agent resources
        # Vertex AI deployed agent
        self.search_agent_resource_name = "projects/1037997398259/locations/us-central1/reasoningEngines/2453041227893833728"

        # Local FastAPI development server
        self.session_url = f"http://localhost:8000/apps/{self.agent}/users/{self.user_id}/sessions/{self.session_id}"
        self.run_url = "http://localhost:8000/run"

        # Authenticate
        if "GOOGLE_API_KEY" not in os.environ.keys():
            self.authenticate()

        # Call the API
        if self.agent == "search":

            # Call the search Agent
            self.call_agent()

            # Parse the response
            self.parse_search_response()


    def authenticate(self):
        '''
        Authenticate with Google AI services
        '''

        # Authenticate
        api_configs = ApiAuthentication(client="CCC")

        # Initialize Vertex AI API once per session
        vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
                      location=os.environ["GOOGLE_CLOUD_LOCATION"],
                      staging_bucket=os.environ["STAGING_BUCKET"])

    def call_agent(self):
        '''
        Call the API to get search results for user's query
        '''


        if self.agent_server == "vertexai_client":
            # Retrieve agent
            self.agent_engine = agent_engines.get(self.search_agent_resource_name)

            # Establish session
            self.session = self.agent_engine.create_session(user_id=self.user_id)
            self.session_id = self.session["id"]

            # Get agent response
            self.result = self.agent_engine.stream_query(message=self.query,
                                                         session_id=self.session_id,
                                                         user_id=self.user_id)

            # Put results into a dictionary for later access
            self.events = []
            for event in self.result:
                self.events.append(event)

        elif self.agent_server == "adk_api_server":

            response = requests.post(self.session_url)

            if response.status_code != 200:
                # If the session already exists continue
                if response.text != f'{{"detail":"Session already exists: {self.session_id}"}}':
                    msg = "Failed to create a session. Response text: {}".format(response.text)
                    raise Exception(msg)

            ### Step 3: Call the agent with the user's query
            headers = {"Content-Type": "application/json"}
            data = {"app_name": self.agent,
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "new_message": {"role": "user",
                                    "parts": [{"text": self.query}]
                                    }
                    }

            # Get response with quiz metadata and questions
            self.response = requests.post(self.run_url, headers=headers, data=json.dumps(data))

            self.events = json.loads(self.response.text)

    def parse_search_response(self):
        '''
        Method to parse response into the elements of interest
        '''

        # Set labels
        if self.agent_server == "vertexai_client":
            grnd_meta_label = "grounding_metadata"
            grnd_chunks_label = "grounding_chunks"

        elif self.agent_server == "adk_api_server":
            grnd_meta_label = "groundingMetadata"
            grnd_chunks_label = "groundingChunks"

        self.domains = []
        self.uris = []
        self.contents = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            self.contents.append(tct.clean_contents(intext=txt_dict["text"]))

            # Find domains and URIs from grounding_metadata
            uri_index = 0
            for gc in event[grnd_meta_label][grnd_chunks_label]:
                for key in gc.keys():
                    if key == "web":
                        if "domain" in gc["web"].keys() and "uri" in gc["web"].keys():
                            self.domains.append(gc["web"]["domain"])
                            self.uris.append(dict(uri_index=uri_index,
                                                  uri=gc["web"]["uri"],
                                                  uri_text=gc["web"]["domain"])
                                             )
                            uri_index += 1

        self.domains = list(set(self.domains))




