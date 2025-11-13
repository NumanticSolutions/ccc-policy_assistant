# © 2025 Numantic Solutions LLC
# MIT License
#
# CCC chatbot agent synthesizing responses of sub agents


import os, sys
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
    utils_path = "../utilities/"
sys.path.insert(0, utils_path)

try:
    from utilities.osa_tools.authentication import ApiAuthentication
    from utilities.text_cleaning import json_tools as jt
except:
    from authentication import ApiAuthentication
    import json_tools as jt

from ccc_search_agent_parser import SearchAgentResults
from ccc_rag_agent_parser import RagAgentResults

import data_models as dms

class ReportWriterResults:
    '''
    Class to synthesize input of searches and respond to a user's query
    '''

    def __init__(self,
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
        self.user_id = user_id
        self.session_id = session_id
        self.agent = "synthesis"

        # Use the Vertex RAG agent or Vertex AI Search App directly
        # Values:
        #   rag: Use the RAG agent to search
        #   rag_search_engine: Search the Vertex AI Engine directly
        # self.va_search_tool = "rag_search_engine"
        self.va_search_tool = "rag"

        # Google search agent name
        self.gs_agent_name = "search"

        # Parameters - Maximum number of search URIs to return
        self.max_va_uris = 5
        self.max_gs_uris = 5

        # Update any key word args
        self.__dict__.update(kwargs)

        # Users's query
        self.user_id = user_id

        # Expected output - JSON
        self.report_dict = dict(report_title="",
                                report_executive_summary="",
                                report_body="",
                                report_references="")

        # Synthesis agent resource
        # Vertex AI deployed agent
        self.synthesis_resource_name = "projects/1037997398259/locations/us-central1/reasoningEngines/4851234417747689472"

        # Local FastAPI development server
        self.session_url = f"http://localhost:8000/apps/{self.agent}/users/{self.user_id}/sessions/{self.session_id}"
        self.run_url = "http://localhost:8000/run"

        # Authenticate
        if "GOOGLE_API_KEY" not in os.environ.keys():
            self.authenticate()

    def call_synthesis_agent(self):
        '''
        Call the synthesis agent
        '''

        if self.agent_server == "vertexai_client":
            # Retrieve agent
            self.agent_engine = agent_engines.get(self.synthesis_resource_name)

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

            try:
                self.events = json.loads(self.response.text)
            except:
                self.events = []

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

    def create_policy_report(self,
                             query: str):
        '''
        Method to respond to a user's query
        '''

        ### Step 1. Set parameters
        references = []

        ### Step 2. Get RAG Vertex AI search results of web text
        try:
            va_text = ""
            self.va_agent = RagAgentResults(agent=self.va_search_tool,
                                            query=query,
                                            user_id=self.user_id,
                                            session_id=self.session_id,
                                            agent_server=self.agent_server)

            ### Step 2.1: get text - expected to be output of RAG agent
            if len(self.va_agent.contents) > 0 or len(self.va_agent.transcripts) > 0:

                va_text = "Summary: {}. Transcripts: {}".format(self.va_agent.contents,
                                                            self.va_agent.transcripts)

            ### Step 2.3: get references - expected to be output of RAG agent
            if len(self.va_agent.uris) > 0:
                for va in self.va_agent.uris:
                    references.append(dms.Reference(organization=va["uri_text"],
                                                    uri=va["uri"]))

            ### Step 2.3: add references
            if len(self.va_agent.search_engine_results_df) > 0:
                df_va = self.va_agent.search_engine_results_df
                try:
                    for idx in df_va.index:
                        org = json.loads(df_va.loc[idx, "organization"])
                        references.append(dms.Reference(organization=org["name"],
                                                        uri=df_va.loc[idx, "page_url"]))
                except:
                    pass

                va_text = "{}. {}.".format(va_text,
                                           df_va["clean_headings"])
        except:
            pass

        ### Step 3. Get Google search results
        gs_text = ""
        try:
            self.gs_agent = SearchAgentResults(agent=self.gs_agent_name,
                                               query=query,
                                               user_id=self.user_id,
                                               session_id=self.session_id,
                                               agent_server=self.agent_server)

            ### Step 3.1: Get GS references
            try:
                for gc in self.gs_agent.uris:
                    references.append(dms.Reference(organization=gc["uri_text"],
                                                    uri=gc["uri"]))
            except:
                pass

            ### Step 3.2. Get GS text
            gs_text = self.gs_agent.contents

        except:
            pass

        ### Step 4. Combine VA and GS text
        va_gs_text = "{}. {}. ".format(va_text,
                                       gs_text)

        ### Step 4. Create input data model - only continue if some text returned by agents
        if len(va_gs_text) > 0:
            input_material = dms.InputContent(report_material=va_gs_text,
                                              report_references=references)
            self.query = input_material.model_dump_json()

            ### Step 5. Call the synthesis agent
            self.call_synthesis_agent()

            ### Step 6. Parse agent's reponse
            self.parse_synthesis_response()

    def parse_synthesis_response(self):
        '''
        Method to synthesize the search results into a predefined summary output format
        (as specified in the JSON output schema format)

        '''

        # Create an output dictionary
        contents = []

        # Get text results
        try:
            for event in self.events:
                if type(event) == dict:
                    for key in event.keys():
                        if type(event[key]) == dict and key == "content":
                            for txt_dict in event[key]["parts"]:
                                contents.append(txt_dict["text"])

                self.report_dict = jt.extract_json(text=contents[0])

        except:
            pass




