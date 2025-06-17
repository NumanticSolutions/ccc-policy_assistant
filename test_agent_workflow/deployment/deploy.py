import os, sys
import argparse

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp


#### Step 1. Add utils
utils_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import os_tools as ot

#### Step 2. Copy required files into the deployment directory
support_directories = [("../ccc_chatbot", "./ccc_chatbot"),
                       ("../../data/environment", "./data")]
for sd in support_directories:
    ot.copy_and_replace_recursive(sd[0], sd[1])

#### Step 3. Authenticate
api_configs = ApiAuthentication(dotenv_path="./data")

# # Import an authentication object
# utils_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), '../../test_agent_workflow/utils'))
# sys.path.insert(0, utils_path)
# from authentication import ApiAuthentication
# import os_tools as ot
#
# # Set environment variables
# dotenv_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/environment'))
# sys.path.insert(0, dotenv_path)
# api_configs = ApiAuthentication(dotenv_path=dotenv_path)
#
# # Copy agent files into the deployment directory
# chatbot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ccc_chatbot'))
# source_directory = chatbot_path
# destination_directory = "./ccc_chatbot"
# ot.copy_and_replace_recursive(source_directory, destination_directory)

# Import the chatbot
from ccc_chatbot.agent import root_agent


# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])


def deploy() -> None:
    '''
    Function to deploy a new agent to Vertex AI
    '''

    # Set environment variables
    env_vars = None

    # Set an ADK App
    app = AdkApp(agent=root_agent,
                 enable_tracing=True,
                 )

    # Create the agent resource
    remote_app = agent_engines.create(
        app,
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk,langchain,ag2,llama_index,evaluation]>=1.88.0",
            "google-adk==1.2.1",
            "google-cloud-discoveryengine",
            "cloudpickle==3.1.1",
            "python-dotenv",
            "google-auth",
        ],
        extra_packages=[
            "ccc_chatbot",
            "data",
            "utils"
        ],
        gcs_dir_name=os.environ["STAGING_BUCKET"],
        display_name="CCC Chatbot",
        description="An agent providing indepth research on policies affecting California community colleges",
        env_vars=env_vars
    )

    # log remote_app
    print(f"Deployed rag to Vertex AI Agent Engine successfully, resource name: {remote_app.resource_name}")

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
    parser.add_argument("-id", help="Resource ID", dest="resource_id", required=False,
                        type=str)
    args = parser.parse_args()

    if args.action == "deploy":
        print("Starting agent deployment ...")
        deploy()

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




