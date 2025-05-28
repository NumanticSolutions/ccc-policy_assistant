import os, sys
import argparse

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Import an authentication object
utils_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), '../../test_agent_workflow/utils'))
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import os_tools as ot

# Set environment variables
dotenv_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/environment'))
sys.path.insert(0, dotenv_path)
api_configs = ApiAuthentication(dotenv_path=dotenv_path)

# Copy agent files into the deployment directory
chatbot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ccc_chatbot'))
source_directory = chatbot_path
destination_directory = "./ccc_chatbot"
ot.copy_and_replace_recursive(source_directory, destination_directory)

# Import the chatbot
from ccc_chatbot.agent import root_agent


# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])


def deploy() -> None:
    '''
    Deploy a new agent to Vertex AI
    '''
    # Set an ADK App
    app = AdkApp(agent=root_agent,
                 enable_tracing=True,
                 )

    # Create the agent resource
    remote_app = agent_engines.create(
        app,
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk]==1.88.0",
            "google-adk==0.5.0",
            "google-adk[extensions]",
            "litellm",
            "python-dotenv",
            "google-auth",
            "tqdm",
            "requests",
        ],
        extra_packages=[
            "ccc_chatbot",
        ],
    )



    # log remote_app
    print(f"Deployed rag to Vertex AI Agent Engine successfully, resource name: {remote_app.resource_name}")

def delete(resource_id: str) -> None:
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_id}")


def main():
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument("-a", "--action", help="Action to perform", dest="action", required=True,
                        choices=["deploy", "delete"], type=str, default="deploy")
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
    else:
        print("Invalid action. Please use 'deploy' or 'delete'.")

if __name__ == "__main__":
    main()




