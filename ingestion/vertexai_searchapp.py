
# © 2025 Numantic Solutions LLC
# MIT License
#
# Create a VertexAI Search App or Engine

import os, sys

# Numantic utilities
utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.logging.logging_utils import LoggingUtils
from utilities.osa_tools.authentication import ApiAuthentication


# Configure environmental variables
api_configs = ApiAuthentication(client="CCC")

import time
from typing import List
# from google.cloud import discoveryengine
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1 import EngineServiceClient
from google.api_core.client_options import ClientOptions

def create_search_engine_from_datastore(project_id: str,
                                        location: str,
                                        engine_id: str,
                                        display_name: str,
                                        data_store_ids: List[str]
                                        ) -> str:
    """Creates a Vertex AI Search Engine from an existing Data Store.

    Args:
        project_id: The ID of your Google Cloud project.
        location: The location of the data store (e.g., 'global', 'us').
        engine_id: A unique ID for the new search app (Engine).
        display_name: A human-readable name for the new search app.
        data_store_ids: A list of the IDs of the data stores to attach.

    Returns:
        The full resource name of the created engine.
    """

    # Configure the API endpoint for the client
    client_options = None
    if location != "global":
        client_options = ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")

    # Initialize the Engine Service Client
    client = discoveryengine.EngineServiceClient(client_options=client_options)

    # 1. Define the Engine resource
    engine = discoveryengine.Engine(
        display_name=display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
        data_store_ids=data_store_ids,
        # search_engine_config=discoveryengine.SearchEngineConfig(
        #     search_tier=discoveryengine.SearchTier.SEARCH_TIER_STANDARD,
        #     # search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_LLM],
        # ),
    )

    # 2. Create the request object
    # parent = discoveryengine.location_path(project=project_id, location=location)
    parent = f"projects/{project_id}/locations/{location}"

    request = discoveryengine.CreateEngineRequest(
        parent=parent,
        engine=engine,
        engine_id=engine_id,
    )

    # 3. Send the request and wait for the long-running operation to complete
    print(f"Creating engine '{display_name}'...")
    operation = client.create_engine(request=request)

    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    engine_name = response.name
    print(f"\nEngine created successfully! Name: {engine_name}")
    return engine_name


# Execute the function
if __name__ == "__main__":

    # --- Configuration ---
    YOUR_PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]  # Replace with your actual project ID
    YOUR_LOCATION = "global"  # Replace with the location of your data store (e.g., 'us', 'global')
    YOUR_DATA_STORE_ID = "web-text-datastore-v4"

    # New Search App details
    NEW_ENGINE_ID = "web-text-search-app"  # A unique ID for the API
    NEW_DISPLAY_NAME = "Web Text Search App V4"  # A human-readable name


    try:
        # Note: Your Data Store ID in the full resource name format is not needed here,
        # you only pass the short ID to data_store_ids.
        engine_resource_name = create_search_engine_from_datastore(
            project_id=YOUR_PROJECT_ID,
            location=YOUR_LOCATION,
            engine_id=NEW_ENGINE_ID,
            display_name=NEW_DISPLAY_NAME,
            data_store_ids=[YOUR_DATA_STORE_ID],
        )
    except Exception as e:
        print(f"An error occurred: {e}")