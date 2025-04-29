# CCC Policy Assistants
# Agent with multiple tools
# Steve Godfrey
# April 2025

# See https://github.com/google/adk-samples/tree/main/agents



# Import libraries
import os, sys
import json

from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag
import vertexai

# Need 2 paths here to handle the case of running the agent from the root directory using adk run rag
utils_path = "../../../../../ccc-policy_assistant/interface/utils"
sys.path.insert(0, utils_path)

utils_path = "../../../../ccc-policy_assistant/interface/utils"
sys.path.insert(0, utils_path)

from authentication import ApiAuthentication

# Set environment variables
try:
    dotenv_path = "../../../../../ccc-policy_assistant/data/environment"
    api_configs = ApiAuthentication(dotenv_path=dotenv_path)
except:
    dotenv_path = "../../../../ccc-policy_assistant/data/environment"
    api_configs = ApiAuthentication(dotenv_path=dotenv_path)

api_configs.set_environ_variables()

# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"])

###################################
# Create instructions
instruction_prompt_v1 = """
        You are an AI assistant with access to specialized corpus of documents.
        Your role is to provide accurate and concise answers to questions based
        on documents that are retrievable using ask_vertex_retrieval. If you believe
        the user is just chatting and having casual conversation, don't use the retrieval tool.

        But if the user is asking a specific question about a knowledge they expect you to have,
        you can use the retrieval tool to fetch the most relevant information.

        If you are not certain about the user intent, make sure to ask clarifying questions
        before answering. Once you have the information you need, you can use the retrieval tool
        If you cannot provide an answer, clearly explain why.
        """

#########################

ask_vertex_retrieval = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description=(
        'Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,'
    ),
    rag_resources=[
        rag.RagResource(
            rag_corpus=os.environ.get("RAG_CORPUS")
        )
    ],
    similarity_top_k=3,
    vector_distance_threshold=0.6,
)


root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="ask_rag_agent",
    instruction=instruction_prompt_v1,
    tools=[
        ask_vertex_retrieval,
    ]
)



