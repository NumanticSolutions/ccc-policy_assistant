# © 2025 Numantic Solutions LLC
# MIT License
#
# CCC data science agent handling multiple sub agents


import os, sys
import json

import vertexai
from vertexai import agent_engines

# Text cleaning
utils_path = "../utils/"
sys.path.insert(0, utils_path)
import json_tools as jt

from ccc_subagent_parser import getSubAgentResults

class cccDataScienceBot:
    '''
    Class to provide data analysis of IPEDS data
    '''

    def __init__(self,
                 user_id: str,
                 **kwargs):
        '''
        Initialize class
        '''

        # Update any key word args
        self.__dict__.update(kwargs)

        self.rag_agent = "rag_ipeds"
        self.user_id = user_id

        self.synthesis_ipeds_resource_name="projects/1062597788108/locations/us-central1/reasoningEngines/3420052908429803520"

    def search_ipeds_metadata(self,
                              query: str):
        '''
        Method to search IPEDS metadata to see if any data tables contain information
        relevant to the query
        :return:
        '''


        chatbot = getSubAgentResults(rag_agent=self.rag_agent,
                                     query=query,
                                     user_id=self.user_id)

        try:
            self.report_dict = jt.extract_json(text=chatbot.contents[0])

            if self.report_dict["relevant_data_yes_or_no"] == True or \
                    self.report_dict["relevant_data_yes_or_no"].lower() == "yes":
                self.ipeds_helpful = True

            self.ipeds_result = self.report_dict["description_of_relevant_data"]

        except:
            msg = ("I did a search of the Integrated Postsecondary Education Data System (IPEDS) "
                   "but did not find data relevant to your query. ")

            self.report_dict = {}
            self.ipeds_result = msg

    def synthesize_ipeds_metadata_search(self,
                                         query: str,
                                         context: str):
        '''
        Method to synthesize IPEDS search results into a summary paragraph
        :param query:
        :param context:
        :return:
        '''

        # Retrieve agent
        agent_engine = agent_engines.get(self.synthesis_ipeds_resource_name)

        # Establish session
        session = agent_engine.create_session(user_id=self.user_id)

        # Create a query with context
        q_wrp = "query: {} \n\ncontext:{}"
        self.full_context_query = q_wrp.format(query,
                                                context)

        self.result = self.agent_engine.stream_query(message=self.full_context_query,
                                                     session_id=session["id"],
                                                     user_id=self.user_id)