# CCC Policy Assistants
# Tools to deploy and manage agents on Vertex AI
# Steve Godfrey
# August 2025


import os, sys
import shutil
import json
import argparse

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

#### Step 1. Add utils by copying required utility files
utils_to_copy = ["../../../Utilities/osa_tools/authentication.py",
                 "../../../Utilities/osa_tools/os_tools.py",
                 # "../../../../../Utilities/google_tools/gcp_tools.py",
                 # "../../../../../Utilities/logging/response_logger.py",
                 # "../../../../../Utilities/text_cleaning/text_cleaning_tools.py"
                 ]

utils_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.insert(0, utils_path)
# Create if directory if it doesn't exist
if not os.path.exists(utils_path):
    os.makedirs(utils_path)

for util_file in utils_to_copy:
    shutil.copy2(util_file, "{}/{}".format(utils_path,
                                           os.path.basename(util_file)))
from authentication import ApiAuthentication
import os_tools as ot

#### Step 2. Authenticate
api_configs = ApiAuthentication(client="CCC")

#### Step 3. Copy required files into the deployment directory
support_directories = [("../ccc_chatbot", "./ccc_chatbot"),
                       # ("../data_science", "./data_science"),
                       # (api_configs.dotenv_path, "./data")
                       ]
for sd in support_directories:
    ot.copy_and_replace_recursive(sd[0], sd[1])

# Import the chatbot
from ccc_chatbot.agent import rag_agent
from ccc_chatbot.agent import rag_ipeds_agent
from ccc_chatbot.agent import search_agent
from ccc_chatbot.agent import synthesis_agent
from ccc_chatbot.agent import synthesis_ipeds_agent

### Step 4. Read deployment parameters
deploy_configs_file = "deployment_configs.json"
with open(deploy_configs_file, 'r') as infile:
    deploy_configs = json.load(infile)

# Add agents to deploy configs
deploy_configs["rag"]["agent"] = rag_agent
deploy_configs["rag_ipeds"]["agent"] = rag_ipeds_agent
deploy_configs["search"]["agent"] = search_agent
deploy_configs["synthesis"]["agent"] = synthesis_agent
deploy_configs["synthesis_ipeds"]["agent"] = synthesis_ipeds_agent

# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

def deploy(agent_index: str,
           deploy_configs: dict) -> None:
    '''
    Function to deploy a new agent to Vertex AI

    agent_name: String indicating which agent is to be deployed

    '''

    # Set environment variables
    env_vars = dict(GOOGLE_API_KEY=os.environ["GOOGLE_API_KEY"],
                    GOOGLE_GENAI_USE_VERTEXAI=os.environ["GOOGLE_GENAI_USE_VERTEXAI"],
                    GOOGLE_CLOUD_PROJECT_ID=os.environ["GOOGLE_CLOUD_PROJECT_ID"],
                    BQ_IPEDS_DATASET_ID=os.environ["BQ_IPEDS_DATASET_ID"],
                    STAGING_BUCKET=os.environ["STAGING_BUCKET"]
                    )

    # Set parameters
    root_agent = deploy_configs[agent_index]["agent"]
    display_name = deploy_configs[agent_index]["display_name"]
    description = deploy_configs[agent_index]["description"]

    # Set an ADK App
    app = AdkApp(agent=root_agent,
                 enable_tracing=True,
                 )

    # Create the agent resource
    remote_app = agent_engines.create(
        app,
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk,langchain,ag2,llama_index,evaluation]==1.106.0",
            "google-adk==1.9.0",
            "google-cloud-discoveryengine==0.13.11",
            "cloudpickle==3.1.1",
            "pydantic==2.11.7",
            "python-dotenv==1.1.1",
            "google-auth==2.40.3"
        ],

        extra_packages=[
            "ccc_chatbot",
            # "data",
            "utils",
        ],
        gcs_dir_name=os.environ["STAGING_BUCKET"],
        display_name=display_name,
        description=description,
        env_vars=env_vars
    )

    # log remote_app
    print(f"Deployed {agent_index} agent to Vertex AI Agent Engine successfully, resource name: {remote_app.resource_name}")

def delete(resource_id: str) -> None:
    '''
    Function to delete an existing agent resource
    '''
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_id}")


def list(resource_id: str) -> None:
    '''
    Function to list all existing agent resources
    '''


def main():
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument("-a", "--action", help="Action to perform", dest="action", required=True,
                        choices=["deploy", "delete", "list"], type=str, default="deploy")
    parser.add_argument("-id", help="Resource ID", dest="resource_id", required=False, type=str)
    args = parser.parse_args()

    # Take action depending on command line inputs
    if args.action == "deploy":
        if args.resource_id not in ["rag", "rag_ipeds", "search", "synthesis", "synthesis_ipeds"]:
            msg = ("Agent ID is required for deploying an agent; currently 'rag', "
                   "'search', 'data_science', 'synthesis'.")
            raise Exception(msg)
        else:
            print("Starting agent deployment ...")
            deploy(agent_index=args.resource_id,
                   deploy_configs=deploy_configs)

    elif args.action == "delete":
        if not args.resource_id:
            msg = "Resource ID is required for deleting an agent."
            raise Exception(msg)
        else:
            print("Starting agent deletion ...")
            delete(resource_id=args.resource_id)

    elif args.action == "list":
        for agent in agent_engines.list():
            print(agent)
    else:
        print("Invalid action. Please use 'deploy' or 'delete'.")

if __name__ == "__main__":
    main()




