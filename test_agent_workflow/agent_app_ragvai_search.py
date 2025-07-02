
import os, sys
import re
# import requests
# import json
# import google.auth
# from google.auth.transport.requests import Request

# import vertexai
from vertexai import agent_engines

# Set environment variables
utils_path = "utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
api_configs = ApiAuthentication(client="CCC")


class readVaiSearchResults:
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
        # self.resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/3990725831524614144"
        self.resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/8025388147695157248"

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
                            self.contents.append(txt_dict["text"])

            # Find domains and URIs from grounding_metadata
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
                                    org_dets = fl_txt[os:ss].split("\n")
                                    org_dets = [d.replace("-", "").strip() for d in org_dets if len(d) > 0]
                                else:
                                    org_dets = []

                                # Get transcript
                                if ttsres:
                                    transcript = fl_txt[ttsres.start() + len(pat_trs):]
                                else:
                                    transcript = ""

                                # Add to organization to list but firsts convert to dictionary
                                dorgs.append({k[:k.find(":")]: k[k.find(":") + 1:].strip() for k in org_dets})

                                # get a list of organizations without duplicates
                                for org_name in set([org["name"] for org in dorgs]):
                                    for dorg in dorgs:
                                        if dorg["name"] == org_name and dorg not in self.organizations:
                                            self.organizations.append(dorg)

                                # Add transcripts
                                self.transcripts.append(transcript)

                                # Get the uri
                                try:
                                    self.uris.append(dict(uri_index=i,
                                                          uri=gc["retrieved_context"]["uri"],
                                                          uri_text=gc["retrieved_context"]["title"]
                                                          )
                                                     )
                                except:
                                    self.uris.append(dict(uri_index=i,
                                                          uri=gc["retrieved_context"]["uri"],
                                                          uri_text=""
                                                          )
                                                     )

            except:
                pass




# class readVaiSearchResults:
#     '''
#     Class to read and parse Vertex AI Search App results
#
#     '''
#
#     def __init__(self, query: str):
#         '''
#         Initialize class
#         '''
#
#         # Define the endpoint - For use if accessing VertexAI Search App via REST
#         self.url = ("https://discoveryengine.googleapis.com/v1alpha/"
#                     "projects/1062597788108/locations/global/collections/default_collection/"
#                     "engines/web-text-data-store-search_1750123185671/servingConfigs/default_search:search"
#                     )
#
#         # Users's query
#         self.query = query
#         self.pagesize = 10
#
#         # Get credentials
#         self.get_gcp_credentials()
#
#         # Call the API
#         self.call_api()
#
#         # Parse the response
#         self.parse_response()
#
#     def get_gcp_credentials(self):
#         '''
#         Get GCP credentials need to call the API
#         '''
#
#         # Get application default credentials
#         credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
#         credentials.refresh(Request())
#
#         # Prepare headers
#         self.headers = {
#             "Authorization": f"Bearer {credentials.token}",
#             "Content-Type": "application/json",
#             "X-Goog-User-Project": os.environ["GOOGLE_CLOUD_PROJECT"]
#         }
#
#     def call_api(self):
#         '''
#         Call the API to get search results for user's query
#         '''
#
#         # Define the request payload
#         payload = {
#             "query": self.query,
#             "pageSize": self.pagesize,
#             "queryExpansionSpec": {
#                 "condition": "AUTO"
#             },
#             "spellCorrectionSpec": {
#                 "mode": "AUTO"
#             },
#             "languageCode": "en-US",
#             "userInfo": {
#                 "timeZone": "America/Los_Angeles"
#             }
#         }
#
#         # Make the POST request
#         self.response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
#
#         self.response.status_code = self.response.status_code
#         self.response_content = self.response.json()
#
#     def parse_response(self):
#         '''
#         Method to parse response into the elements of interest
#         '''
#
#         max_char_uri_text = 45
#
#         self.organizations = []
#         self.uris = []
#         self.contents = []
#         dorgs = []
#
#         for i, result in enumerate(self.response_content["results"]):
#             transcript = result["document"]["structData"]["transcript"]
#             self.contents.append(transcript)
#             self.uris.append(dict(uri_index=i,
#                                   uri=result["document"]["structData"]["uri"],
#                                   uri_text="{} ...".format(transcript[:max_char_uri_text].strip())
#                                   )
#                              )
#             dorgs.append(json.dumps(result["document"]["structData"]["organizations"][0]))
#
#         # All organizations
#         dorgs = [json.loads(o) for o in dorgs]
#
#         # get org names
#         org_names = set([org["name"] for org in dorgs])
#
#         # get a list of organizations without duplicates
#         for org_name in org_names:
#             for dorg in dorgs:
#                 if dorg["name"] == org_name and dorg not in self.organizations:
#                     self.organizations.append(dorg)
#
#         # remove duplicates from these lists
#         self.contents = list(set(self.contents))
