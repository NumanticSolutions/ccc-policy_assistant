import os, sys
import json
from datetime import datetime

import asyncio
import vertexai
from vertexai import agent_engines
from google import adk
from google.adk.sessions import VertexAiSessionService
from google.genai import types
from vertexai.preview import reasoning_engines

#### Step 1. Add utils
utils_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import os_tools as ot

# Set environment variables
dotenv_path = "data/"
api_configs = ApiAuthentication(dotenv_path=dotenv_path)

# Create an agent engine instance
# agent_engine = agent_engines.create()

### Step 2: Create a tool and an agent that uses that tool
def greetings(query: str):
  """Tool to greet user."""
  if 'hello' in query.lower():
    return {"greeting": "Hello, world"}
  else:
    return {"greeting": "Goodbye, world"}

# Define an ADK agent
# root_agent = adk.Agent(
#     model=os.environ["GEMINI_MODEL"],
#     name='my_agent',
#     instruction="You are an Agent that greet users, always use greetings tool to respond.",
#     tools=[greetings]
# )

# Import the chatbot
from ccc_chatbot.agent import root_agent
from ccc_chatbot.agent import rag_agent
from ccc_chatbot.agent import search_agent
from ccc_chatbot.agent import synthesis_agent

### Step 4. Read deployment parameters
deploy_configs_file = "deployment_configs.json"
with open(deploy_configs_file, 'r') as infile:
    deploy_configs = json.load(infile)

# Add agents to deploy configs
deploy_configs["rag"]["agent"] = rag_agent
deploy_configs["search"]["agent"] = search_agent
deploy_configs["synthesis"]["agent"] = synthesis_agent
deploy_configs["ccc_bot"]["agent"] = root_agent

# app_name="projects/1062597788108/locations/us-central1/reasoningEngines/4961181182478778368"
app_name = "projects/1062597788108/locations/us-central1/reasoningEngines/9020261452878970880"
user_id="User_123"

# Create the ADK runner with VertexAiSessionService
session_service = VertexAiSessionService(project=os.environ["GOOGLE_CLOUD_PROJECT"],
                                         location=os.environ["GOOGLE_CLOUD_LOCATION"])

async def create_service_session(app_name, user_id, session_service):
    return await session_service.create_session(app_name=app_name, user_id=user_id)

runner = adk.Runner(
    agent=root_agent,
    app_name=app_name,
    session_service=session_service)

# Helper method to send query to the runner
def call_agent(query, session_id, user_id):
  content = types.Content(role='user', parts=[types.Part(text=query)])
  events = runner.run(
      user_id=user_id, session_id=session_id, new_message=content)

  for event in events:
      if event.is_final_response():
          final_response = event.content.parts[0].text
          print("Agent Response: ", final_response)



async def main(agent_index: str,
               deploy_configs):

    # Set agent parameter
    root_agent = deploy_configs[agent_index]["agent"]

    print("Testing a local deployment of agent: {}".format(deploy_configs[agent_index]["display_name"]))
    start_time = datetime.now()
    print("Time: {}".format(start_time.strftime("%b %-d, %Y, %-H:%M:%S %p")))

    user_msg = "What are the responsibilities of the board members of a California community college?"
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    session = app.create_session(user_id="u_123")
    print("Session details: {}".format(session))

    for event in app.stream_query(
            user_id="u_123",
            session_id=session.id,
            message=user_msg,
    ):
        print("Event Author: {}".format(event["author"]))
        print("Text: {} ...".format(event['content']["parts"][0]["text"][:750]))
        print()

    # Create a session
    # session = await create_service_session(app_name=app_name,
    #                                  user_id=user_id,
    #                                  session_service=session_service)
    #
    # print(session)

    # print(user_msg)
    # call_agent(user_msg, session.id, user_id)
    # # Agent response: "Hello, world"
    #
    # call_agent("Thanks!", session.id, user_id)
    # # Agent response: "Goodbye, world"


if __name__ == "__main__":
    agent_index = "rag"
    asyncio.run(main(agent_index=agent_index,
                     deploy_configs=deploy_configs))
