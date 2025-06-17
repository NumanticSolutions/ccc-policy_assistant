import os, sys

import time
import json
import requests
import google.auth
from google.auth.transport.requests import Request


utils_path = "../../test_agent_workflow/utils"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import gcp_tools as gct

# Set environment variables
dotenv_path = "../../data/environment"
api_configs = ApiAuthentication(dotenv_path=dotenv_path)
api_configs.set_environ_variables()


# --- Configuration parameters ---
PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT_ID"]
LOCATION = "global"  # Or a specific region like "us-central1"
DATA_STORE_DISPLAY_NAME = "Web Text GCS Data"  # A user-friendly name for your data store
DATA_STORE_ID = "{}-id".format(DATA_STORE_DISPLAY_NAME.lower().replace(" ", "-"))
ENGINE_NAME = "{}-search".format(DATA_STORE_DISPLAY_NAME.lower().replace(" ", "-"))
ENGINE_ID = "{}-id".format(ENGINE_NAME)
GCS_JSONL_URI = "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/*"
INDUSTRY_VERTICAL = "GENERIC"


def create_data_store(project_id: str,
                      data_store_id: str,
                      location: str,
                      data_store_display_name: str,
                      industry_vertical: str):
    '''
    Function to create Vertex DataStore using REST API
    '''

    # Endpoint to create a DataStore
    url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{project_id}/locations/{location}"
        f"/collections/default_collection/dataStores?dataStoreId={data_store_id}"
    )

    # Request payload
    payload = {
        "displayName": data_store_display_name,
        "industryVertical": industry_vertical
    }

    # Get application default credentials
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    # Send POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Output result
    if response.ok:
        print("DataStore created successfully:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Failed to create DataStore:")
        print(response.status_code, response.text)


# def update_datastore(data_store_name: str,
#                      location):
def update_datastore(project_id: str,
                     data_store_id: str,
                     location: str):
    '''
    Function to update a datastore using REST API usually to pass JSON structured data schema
    '''

    # Set your GCP project details
    api_endpoint = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}?updateMask=structSchema"

    # Define the schema
    filename = "gcs_json_schema.json"
    with open(filename, 'r') as infile:
        schema_body = json.load(infile)

    # Authenticate using Application Default Credentials
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    # Set headers
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

    # Send PATCH request with updated structured data JSON
    struct_schema = {"structSchema": json.dumps(schema_body)}
    response = requests.patch(api_endpoint, headers=headers, data=struct_schema)

    # Print result
    if response.status_code == 200:
        print("Schema updated successfully.")
        print(response.json())
    else:
        print("Failed to update schema.")
        print(response.status_code, response.text)


def main():
    """Main function to orchestrate the creation process."""

    # Step 1: Create the Data Store
    # create_data_store(project_id=PROJECT_ID,
    #                   data_store_id=DATA_STORE_ID,
    #                   location=LOCATION,
    #                   data_store_display_name=DATA_STORE_DISPLAY_NAME,
    #                   industry_vertical=INDUSTRY_VERTICAL)
    #
    # # Give the system a moment before creating the data store
    # time.sleep(10)

    # Step 3 Update datastore
    update_datastore(project_id=PROJECT_ID,
                     data_store_id=DATA_STORE_ID,
                     location=LOCATION)


if __name__ == "__main__":
    main()