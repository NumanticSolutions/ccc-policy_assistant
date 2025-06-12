# CCC Policy Assistants
# Agent with multiple tools
# Steve Godfrey
# April 2025

# See https://github.com/google/adk-samples/tree/main/agents



# Import libraries




from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag
# import vertexai

from . import prompt
#
# utils_path = "../interface/utils"
# sys.path.insert(0, utils_path)
#
# utils_path = "../../interface/utils"
# sys.path.insert(0, utils_path)
#
# from authentication import ApiAuthentication
#
# # Set environment variables
# try:
#     dotenv_path = "../data/environment"
#     api_configs = ApiAuthentication(dotenv_path=dotenv_path)
# except:
#     dotenv_path = "../../data/environment"
#     api_configs = ApiAuthentication(dotenv_path=dotenv_path)
#
# api_configs.set_environ_variables()

# Initialize Vertex AI API once per session
# vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
#               location=os.environ["GOOGLE_CLOUD_LOCATION"])

ask_vertex_retrieval = VertexAiRagRetrieval(
    name=prompt.rag_tool_name,
    description=prompt.rag_tool_description,
    rag_resources=[
        rag.RagResource(
            rag_corpus=prompt.rag_corpus_name
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.4,
)

root_agent = Agent(
    name=prompt.rag_agent_name,
    model=prompt.rag_model_name,
    description=prompt.rag_agent_description,
    instruction=prompt.rag_agent_instruction,
    tools=[
        ask_vertex_retrieval,
    ]
)



