import os, sys

from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent


###### Comment out when deploying
# utils_path = "../interface/utils"
# sys.path.insert(0, utils_path)
# from authentication import ApiAuthentication
#
# # Set environment variables
# dotenv_path = "../data/environment"
# print(os.listdir(dotenv_path))
# api_configs = ApiAuthentication(dotenv_path=dotenv_path)


from . import prompt

from .sub_agents import rag_agent
from .sub_agents import search_agent
from .sub_agents import synthesis_agent


code_pipeline_agent = SequentialAgent(
    name=prompt.chatbot_agent_name,
    sub_agents=[rag_agent,
                search_agent,
                synthesis_agent],
    description=prompt.chatbot_agent_description,
)

root_agent = code_pipeline_agent