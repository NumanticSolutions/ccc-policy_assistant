import os, sys

import asyncio
import vertexai
from vertexai import agent_engines
from google import adk
from google.adk.sessions import VertexAiSessionService
from google.genai import types

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
root_agent = adk.Agent(
    model=os.environ["GEMINI_MODEL"],
    name='my_agent',
    instruction="You are an Agent that greet users, always use greetings tool to respond.",
    tools=[greetings]
)

app_name="projects/1062597788108/locations/us-central1/reasoningEngines/4961181182478778368"
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



async def main():

    # Create a session
    session = await create_service_session(app_name=app_name,
                                     user_id=user_id,
                                     session_service=session_service)

    call_agent("Hello!", session.id, user_id)
    # Agent response: "Hello, world"

    call_agent("Thanks!", session.id, user_id)
    # Agent response: "Goodbye, world"


if __name__ == "__main__":
    asyncio.run(main())
