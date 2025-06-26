from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.agents import SequentialAgent

###### Comment out when deploying
# import os, sys
# utils_path = "utils/"
# sys.path.insert(0, utils_path)
# from authentication import ApiAuthentication
# api_configs = ApiAuthentication(client="CCC")

from . import prompt
# from .sub_agents import intake_agent
from .sub_agents import rag_agent
# from .sub_agents import memory_agent
from .sub_agents import search_agent
from .sub_agents import synthesis_agent

###################
# research_pipeline_agent = SequentialAgent(
#     name=prompt.pipeline_agent_name,
#     description=prompt.pipeline_agent_description,
#     sub_agents=[rag_agent,
#                 search_agent,
#                 synthesis_agent
#                 ],
# )
# root_agent = research_pipeline_agent


# research_pipeline_agent = SequentialAgent(
#     name=prompt.pipeline_agent_name,
#     description=prompt.pipeline_agent_description,
#     sub_agents=[rag_agent,
#                 synthesis_agent
#                 ],
# )
# root_agent = research_pipeline_agent

# root_agent = synthesis_agent


# policy_assistant_agent = Agent(
#     name=prompt.chatbot_agent_name,
#     model=prompt.chatbot_model_name,
#     description=prompt.chatbot_agent_description,
#     sub_agents=[intake_agent,
#                 research_pipeline_agent,
#                 synthesis_agent
#                 ],
# )
#
# root_agent = policy_assistant_agent



# research_pipeline_agent = LlmAgent(
#     name=prompt.pipeline_agent_name,
#     model = os.environ["GEMINI_MODEL"],
#     sub_agents=[memory_agent,
#                 rag_agent,
#                 search_agent
#                 ],
#     description=prompt.pipeline_agent_description,
# )
#
# policy_assistant_agent = LlmAgent(
#     name=prompt.chatbot_agent_name,
#     model = os.environ["GEMINI_MODEL"],
#     sub_agents=[research_pipeline_agent,
#                 synthesis_agent
#                 ],
#     description=prompt.chatbot_agent_description,
#
# )

# policy_assistant_agent = LlmAgent(
#     name=prompt.chatbot_agent_name,
#     model = os.environ["GEMINI_MODEL"],
#     sub_agents=[rag_agent,
#                 search_agent,
#                 synthesis_agent
#                 ],
#     description=prompt.chatbot_agent_description,
#
# )

