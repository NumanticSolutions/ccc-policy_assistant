# CCC Policy Assistants
# Tools to deploy and manage agents on Vertex AI
# Steve Godfrey
# August 2025


import os, sys
import json
import argparse

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

### Step 1. Authenticate if needed
if "GOOGLE_API_KEY" not in os.environ.keys():
    utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
    sys.path.insert(0, utils_path)
    from utilities.osa_tools.authentication import ApiAuthentication
    api_configs = ApiAuthentication(client="CCC")

#### Step 2. Import sub-agents
from ccc_policybot.sub_agents.rag.agent import root_agent as rag_agent
from ccc_policybot.sub_agents.search.agent import root_agent as search_agent
from ccc_policybot.sub_agents.synthesis.agent import root_agent as synthesis_agent

### Step 3. Read deployment parameters
deploy_configs_file = "deployment_configs.json"
with open(deploy_configs_file, 'r') as infile:
    deploy_configs = json.load(infile)

### Step 4. Add agents to deploy configs
deploy_configs["rag"]["agent"] = rag_agent
deploy_configs["search"]["agent"] = search_agent
deploy_configs["synthesis"]["agent"] = synthesis_agent

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
                    STAGING_BUCKET=os.environ["STAGING_BUCKET"],
                    GOOGLE_CLOUD_PROJECT_ID=os.environ["GOOGLE_CLOUD_PROJECT_ID"]
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
            "google-cloud-aiplatform[agent_engines,adk,langchain,ag2,llama_index,evaluation]==1.120.0",
            "google-adk==1.16.0",
            "google-cloud-discoveryengine==0.13.12",
            "cloudpickle==3.1.1",
            "pydantic==2.12.3",
            "python-dotenv==1.1.1",
            "google-auth==2.41.1"
        ],
        extra_packages=[
            "ccc_policybot",
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
        if args.resource_id not in ["rag", "search", "synthesis"]:
            msg = ("Agent ID is required for deploying an agent; currently 'rag', "
                   "'search', 'synthesis'.")
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




