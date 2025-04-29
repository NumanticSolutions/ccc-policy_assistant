import os, sys
import json

import vertexai
from vertexai import agent_engines

from vertexai.preview.reasoning_engines import AdkApp

utils_path = "../../../../../ccc-policy_assistant/interface/utils"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication

# Set environment variables
dotenv_path = "../../../../../ccc-policy_assistant/data/environment"
api_configs = ApiAuthentication(dotenv_path=dotenv_path)
api_configs.set_environ_variables()

# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

# utils_path = "rag"
# sys.path.insert(0, utils_path)
from agent import root_agent

# Set an ADK App
app = AdkApp(agent=root_agent,
             enable_tracing=True,
             )

# Create the agent resource
remote_app = agent_engines.create(
    app,
    requirements=[
        "google-cloud-aiplatform[agent_engines,adk]==1.88.0",
        "google-adk",
        "google-adk[extensions]",
        "litellm",
        "python-dotenv",
        "google-auth",
        "tqdm",
        "requests",
    ],
    extra_packages=[
        "agent.py",
    ],
)

# log remote_app
print(f"Deployed rag to Vertex AI Agent Engine successfully, resource name: {remote_app.resource_name}")


