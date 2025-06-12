import os, sys

import time
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

utils_path = "../../test_agent_workflow/utils"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import gcp_tools as gct

# Set environment variables
dotenv_path = "../../data/environment"
api_configs = ApiAuthentication(dotenv_path=dotenv_path)
api_configs.set_environ_variables()


# --- Configuration: Update these values for your project ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = "global"  # Or a specific region like "us-central1"
APP_DISPLAY_NAME = "CCC Web Docs Search"  # A user-friendly name for your app
DATA_STORE_DISPLAY_NAME = "Web Docs GCS Data"  # A user-friendly name for your data store
GCS_JSONL_URI = "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/*"  # Use a wildcard (*) to import all files in the folder



# -----------------------------------------------------------------Create a Data Store (inside a Collection).
# Import Documents into that Data Store.
# Create an Engine/App that points to the Data Store you just created.
#
# 1. Create a Data Store (inside a Collection).
# 2. Import Documents into that Data Store.
# 3. Create an Engine/App that points to the Data Store you just created.

def create_search_app(project_id: str, location: str, app_display_name: str) -> str:
    """Creates a new Vertex AI Search App (Engine)."""

    # The parent path for creating an engine
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

    # The client options for the desired region
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    client = discoveryengine.EngineServiceClient(client_options=client_options)

    # Construct the Engine object
    engine = discoveryengine.Engine(
        display_name=app_display_name,
        # SOLUTION_TYPE_SEARCH is crucial for creating a search app
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
    )

    # Create the Engine (this is a Long-Running Operation - LRO)
    print(f"Creating search app '{app_display_name}'...")
    operation = client.create_engine(
        parent=parent,
        engine=engine,
        engine_id=app_display_name.lower().replace(" ", "-"),  # Create a stable ID
    )

    # Wait for the LRO to complete and get the result
    created_engine = operation.result()
    print(f"Successfully created app. Resource name: {created_engine.name}")

    return created_engine.name


# def create_gcs_data_store(project_id: str, data_store_name: str) -> str:
#     """Creates a Data Store within a Search App."""
#
#     location = engine_name.split('/')[3]  # Extract location from engine name
#     client_options = (
#         ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
#         if location != "global"
#         else None
#     )
#
#     client = discoveryengine.DataStoreServiceClient(client_options=client_options)
#
#     parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
#
#     data_store = discoveryengine.DataStore(
#         display_name=data_store_name,
#         industry_vertical="GENERIC",  # Use GENERIC for most use cases
#         # This is correct even for JSONL. It refers to the ingestion method.
#         content_config=discoveryengine.DataStore.ContentConfig.CONTENT_CONFIG_UNSTRUCTURED_DATA,
#     )
#
#     print(f"Creating data store '{data_store_name}'...")
#     operation = client.create_data_store(
#         parent=parent,
#         data_store=data_store,
#         data_store_id=data_store_name.lower().replace(" ", "-"),
#     )
#
#     created_data_store = operation.result()
#     print(f"Successfully created data store. Resource name: {created_data_store.name}")
#
#     return created_data_store.name

def create_gcs_data_store(
    project_id: str,
    location: str,
    data_store_name: str
) -> str:
    """
    Creates a GCS Data Store within the default collection.

    Args:
        project_id: Your Google Cloud project ID.
        location: The GCP location (e.g., "global", "us-central1").
        data_store_name: The display name for the new Data Store.

    Returns:
        The resource name of the created Data Store.
    """
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # The parent for a Data Store is a Collection, not an Engine.
    # We will use the 'default_collection'.
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

    data_store = discoveryengine.DataStore(
        display_name=data_store_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC
    )

    # Generate a unique ID for the data store
    data_store_id = data_store_name.lower().replace(" ", "-")

    print(f"Creating data store '{data_store_name}' in parent '{parent}'...")
    operation = client.create_data_store(
        parent=parent,
        data_store=data_store,
        data_store_id=data_store_id,
    )

    created_data_store = operation.result()
    print(f"Successfully created data store. Resource name: {created_data_store.name}")

    return created_data_store.name

def import_documents_from_gcs(data_store_name: str, gcs_uri: str):
    """Triggers a document import from GCS into the specified data store."""

    location = data_store_name.split('/')[3]  # Extract location
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # The parent path for the documents is the 'default_branch'
    parent = client.branch_path(
        project=PROJECT_ID,
        location=location,
        data_store=data_store_name.split('/')[-1],  # Extract data store ID
        branch="default_branch",
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            # The API uses "json" for the JSONL format
            data_schema="document",
        ),
        # INCREMENTAL will add new/update existing docs. FULL will wipe and replace.
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    print(f"Starting import from {gcs_uri}...")
    operation = client.import_documents(request=request)

    print(f"Waiting for import operation '{operation.operation.name}' to complete...")
    # This can take a long time for large datasets
    response = operation.result()

    print("Import completed!")
    if response.error_samples:
        print(f"Found {len(response.error_samples)} errors.")
        for error in response.error_samples:
            print(f" - Error: {error.message}")
    else:
        print("Import successful with 0 errors.")

def list_all_data_stores(project_id: str, location: str) -> list[discoveryengine.DataStore]:
    """
    Lists all data stores in a given project and location.

    Args:
        project_id: Your Google Cloud project ID.
        location: The GCP location (e.g., "global", "us", "eu").

    Returns:
        A list of DataStore objects.
    """
    # 1. Instantiate the Client
    # A specific endpoint is required for non-global locations.
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)
    # print(dir(client))

    # 2. Define the Parent Resource
    # The parent for listing data stores is the default_collection.
    # Its format is `projects/{project_id}/locations/{location}/collections/default_collection`
    parent = client.collection_path(
        project=project_id, location=location, collection="default_collection"
    )

    print(f"Listing data stores for parent: {parent}\n")

    # 3. Make the API Call
    # The list_data_stores method returns a Pager object that you can iterate over.
    response_pager = client.list_data_stores(parent=parent)

    # Convert the pager to a list to get all results at once
    data_stores = list(response_pager)

    return data_stores

def delete_data_store(name, location):
    '''
    Function to delete data stores
    '''

    print("Deleting {}".format(name))

    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    client.delete_data_store(name=name)



def main():
    """Main function to orchestrate the creation process."""
    try:

        datastores = list_all_data_stores(project_id=PROJECT_ID, location=LOCATION)

        for ds in datastores:
            print("Existing datastores")
            print(ds.name)

            # print(dir(ds))

        # Delete a data store if needed
        # delete_data_store(name=datastores[0].name, location=LOCATION)


        # Step 21 Create the Data Store
        # data_store_resource_name = create_gcs_data_store(project_id=PROJECT_ID,
        #                                                  location=LOCATION,
        #                                                  data_store_name=DATA_STORE_DISPLAY_NAME)

        # Give the system a moment before creating the data store
        time.sleep(10)


        # # Step 3: Import the Documents
        data_store_name=datastores[0].name
        print(data_store_name)
        import_documents_from_gcs(data_store_name=data_store_name,
                                  gcs_uri=GCS_JSONL_URI)


        #data_store_name: str, gcs_uri: str
        # # Step 1: Create the App (Engine)
        # engine_resource_name = create_search_app(PROJECT_ID, LOCATION, APP_DISPLAY_NAME)
        #
        # # Give the system a moment before creating the data store
        # time.sleep(10)
        #
        #
        # # Step 3: Import the Documents
        # import_documents_from_gcs(data_store_resource_name, GCS_JSONL_URI)
        #
        # print("\n--- All Done! ---")
        # print(f"Your new search app is ready in the Google Cloud Console.")
        # print(f"Project: {PROJECT_ID}, Location: {LOCATION}")
        # print("You can now go to the Vertex AI -> Search and Conversation section to test it.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()