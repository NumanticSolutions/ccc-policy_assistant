import os, sys
import json

import vertexai
from vertexai import agent_engines

from search_tools import readVaiSearchResults
from search_tools import readGoogleSearchResults

class cccChatBot:
    '''
    Class to synthesize input of searchs and respond to a user's query
    '''

    def __init__(self,
                 user_id: str):
        '''
        Initialize class
        '''

        # Users's query
        self.user_id = user_id

        # Synthesis agent resouce
        self.synthesis_resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/3177122411342462976"

        # Authenticate
        ########### Adjust for production deployments
        # self.authenticate()

        # Retrieve agent
        self.agent_engine = agent_engines.get(self.synthesis_resource_name)

        # Establish session
        self.session = self.agent_engine.create_session(user_id=self.user_id)


    def authenticate(self):
        '''
        Authenticate with Google AI servvices
        '''

        # Import authentication object
        utils_path = "utils/"
        sys.path.insert(0, utils_path)
        from authentication import ApiAuthentication
        api_configs = ApiAuthentication(client="CCC")

        # Initialize Vertex AI API once per session
        vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
                      location=os.environ["GOOGLE_CLOUD_LOCATION"],
                      staging_bucket=os.environ["STAGING_BUCKET"])

    def stream_and_parse_query(self,
                               query: str):
        '''
        Method to respond to a user's query
        '''

        # # Authenticate
        # self.authenticate()
        #
        # # Retrieve agent
        # self.agent_engine = agent_engines.get(self.synthesis_resource_name)
        #
        # # Establish session
        # self.session = self.agent_engine.create_session(user_id=self.user_id)

        ### Step 1. Get Vertex AI search results
        self.va_results = readVaiSearchResults(query=query)

        ### Step 2. Get Google search results
        self.gs_results = readGoogleSearchResults(query=query,
                                                  user_id=self.user_id)

        # Step 3. Create full-context query using search results
        self.context = " ".join(self.va_results.contents + self.gs_results.contents)
        q_wrp = ("Use the following search results to synthesize an answer "
                 "in the context of California community colleges "
                 "to this user query: {}?  "
                 "Search results: {}.")
        self.full_context_query = q_wrp.format(query,
                                               self.context)

        # Step 4. Call the synthesis agent
        self.result = self.agent_engine.stream_query(message=self.full_context_query,
                                                     session_id=self.session["id"],
                                                     user_id=self.user_id)

        # Step 5. Parse response
        self.parse_response()

    # def get_search_results(self,
    #                        query: str):
    #     '''
    #     Method to conduct Vertex AI search of CCC documents and to
    #     Google search
    #     '''
    #
    #     # Get Vertex AI search results
    #     self.va_results = readVaiSearchResults(query=query)
    #
    #     # Get Google search results
    #     self.gs_results = readGoogleSearchResults(query=query,
    #                                               user_id=self.user_id)




    # def full_context_create_query(self):
    #     '''
    #     Create a query to send to the synthesis agent. This full context query will be
    #     composed of search content plus the user's query.
    #     '''
    #
    #     # create query context
    #     self.context = " ".join(self.va_results.contents + self.gs_results.contents)
    #
    #
    #     q_wrp = ("Use the following search results to synthesize an answer "
    #              "to this user query: {}?  "
    #              "Search results: {}.")
    #     self.full_context_query = q_wrp.format(self.query,
    #                                            self.context)

    def parse_response(self):
        '''
        Method to synthesize the search results into a predefined summary output format
        (as specified in the JSON output schema format)

        '''

        # # Retrieve agent
        # self.agent_engine = agent_engines.get(self.synthesis_resource_name)
        #
        # # Establish session
        # self.session = self.agent_engine.create_session(user_id=self.user_id)

        # Get agent response


        # Put results into a dictionary for later access
        self.events = []
        for event in self.result:
            self.events.append(event)

        # Create an output dictionary
        contents = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            contents.append(txt_dict["text"])

        # Convert the output JSON to a dictionary
        contstr = contents[0].replace("```json\n", "")
        contstr = contstr.replace("\n```", "")

        self.report_dict = json.loads(contstr)

        # Add reference URIs from search results
        ref_uris = []
        for uri_dict in self.gs_results.uris + self.va_results.uris:
            md_formatted = "[{}]({})".format(uri_dict["uri_text"],
                                             uri_dict["uri"])
            ref_uris.append(md_formatted)

        # Add these to report dictionary
        self.report_dict["reference_uris"] = ref_uris


