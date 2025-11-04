# © 2025 Numantic Solutions LLC
# MIT License
#
# Process responses from the CCC RAG agent and its underlying Vertex AI Search Engine

import os, sys
import re
import json
import requests

import pandas as pd
import vertexai
from vertexai import agent_engines

#### Numantic utilities
if os.environ['USER'] == 'numantic':
    utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
elif os.environ['USER'] == 'stephengodfrey':
    utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
else:
    utils_path = "../utilities/"
sys.path.insert(0, utils_path)

from utilities.osa_tools.authentication import ApiAuthentication
from utilities.text_cleaning import json_tools as jt
from utilities.text_cleaning import text_cleaning_tools as tct
from utilities.ai_tools.vertexai.vais_query import QueryVaiSearch


class RagAgentResults:
    '''
    Class to read and parse responses from the CCC's Google RAG ADK agent and handle
    direct searches of its underlying Vertex AI Search Engine

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

        # Validate inputs
        agents = ["rag", "rag_search_engine"]
        if self.agent not in agents:
            msg = "The input parameter rag_agent must be in {}".format(agents)
            raise ValueError(msg)

        # Set up agent resources
        # Vertex AI deployed agent
        self.rag_agent_resource_name = "projects/1037997398259/locations/us-central1/reasoningEngines/5087647009905573888"

        # Local FastAPI development server
        self.session_url = f"http://localhost:8000/apps/{self.agent}/users/{self.user_id}/sessions/{self.session_id}"
        self.run_url = "http://localhost:8000/run"

        # Underlying Search App
        self.search_engine = "webtext_search_app"

        # Authenticate
        if "GOOGLE_API_KEY" not in os.environ.keys():
            self.authenticate()

        self.gcp_project = os.environ["GOOGLE_CLOUD_PROJECT_ID"],
        self.gcp_location = "global"

        # Update any key word args
        self.__dict__.update(kwargs)

        # Assume RAG results are unstructured - if we find they are set to True
        self.results_structured = False

        # Structured output - if available this will be a dataframe
        self.search_engine_results_df = None

        # Call the API
        if self.agent == "rag":

            # Call the RAG Agent
            self.call_agent()

            # Parse the response
            self.parse_rag_response()

        elif self.agent == "rag_search_engine":

            # Call the search app directly
            self.call_search_app()

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
            self.agent_engine = agent_engines.get(self.rag_agent_resource_name)

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

            # Put results into a dictionary for later access
            self.events = json.loads(self.response.text)

    def parse_rag_response(self):
        '''
        Method to parse response into the elements of interest
        '''

        self.organizations = []
        self.uris = []
        self.contents = []
        self.transcripts = []
        dorgs = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:

                            # Try to create structured output
                            try:
                                # Try to create a list of dictionaries from the structured output
                                rag_findings = jt.extract_json(text=txt_dict["text"])
                                self.search_engine_results_df = pd.DataFrame(data=rag_findings)

                                # Set the structured data flag to True
                                self.results_structured = True

                            except:
                                pass

                            # If results are structured
                            if self.results_structured:
                                if "clean_headings_text" in self.search_engine_results_df.columns:
                                    all_text_findings = ". ".join(
                                        self.search_engine_results_df["clean_headings_text"].tolist()
                                    )
                                    self.contents.append(all_text_findings)
                            else:
                                self.contents.append(tct.clean_contents(intext=txt_dict["text"]))


            # Find domains and URIs from grounding_metadata
            if not self.results_structured:
                try:
                    for i, gc in enumerate(event["grounding_metadata"]["grounding_chunks"]):
                        if type(gc) == dict:
                            for key in gc.keys():
                                if type(gc[key]) == dict and key == "retrieved_context":

                                    # Get organizations and transcripts
                                    pat_org = r"organizations:"
                                    pat_src = r"source_index:"
                                    pat_trs = r"transcript:"

                                    fl_txt = gc["retrieved_context"]["text"]

                                    # Find organization
                                    tores = re.search(pat_org, fl_txt)
                                    # Find source_index
                                    tsires = re.search(pat_src, fl_txt)
                                    # Find transcript
                                    ttsres = re.search(pat_trs, fl_txt)

                                    # Get organization
                                    if tores and tsires:
                                        os = tores.start() + len(pat_org)
                                        ss = tsires.start()
                                        dorg = json.loads(json.loads(fl_txt[os:ss]))
                                        dorgs.append(dorg)

                                    # Get transcript
                                    if ttsres:
                                        transcript = fl_txt[ttsres.start() + len(pat_trs):]
                                    else:
                                        transcript = ""

                                    # get a list of organizations without duplicates
                                    for org_name in set([org["name"] for org in dorgs]):
                                        for dorg in dorgs:
                                            if dorg["name"] == org_name and dorg not in self.organizations:
                                                self.organizations.append(dorg)

                                    # Add transcripts
                                    self.transcripts.append(transcript)

                                    # Get the title
                                    if "title" in gc["retrieved_context"].keys() and len(
                                            gc["retrieved_context"]["title"]) > 0:
                                        title = gc["retrieved_context"]["title"]
                                    else:
                                        title = dorg["name"]

                                    # Add a URI
                                    self.uris.append(dict(uri_index=i,
                                                          uri=gc["retrieved_context"]["uri"],
                                                          uri_text=title
                                                          )
                                                     )

                except:
                    pass

    def call_search_app(self):
        """
        Method to call the underlying Search App directly
        :return:
        """

        search = QueryVaiSearch(search_app_id=self.search_engine,
                              gcp_project=os.environ["GOOGLE_CLOUD_PROJECT_ID"],
                              gcp_location="global")

        search.search_vertex_ai_app(query=self.query)

        # Get the structured output into a dataframe
        self.search_engine_results_df = search.struct_data_df

        # Set the structured data flag to True
        self.results_structured = True


