# Logical steps
# 1. Create a Data Store (inside a Collection).
# 2. Import Documents into that Data Store.
# 3. Create an Engine/App that points to the Data Store you just created.

import os, sys
import json
import time

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf import field_mask_pb2, struct_pb2

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
DATA_STORE_DISPLAY_NAME = "Web Text Data"  # A user-friendly name for your data store
DATA_STORE_ID = "{}-id".format(DATA_STORE_DISPLAY_NAME.lower().replace(" ", "-"))
ENGINE_NAME = "{}-search".format(DATA_STORE_DISPLAY_NAME.lower().replace(" ", "-"))
ENGINE_ID = "{}-id".format(ENGINE_NAME)
GCS_JSONL_URI = "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/*"
INDUSTRY_VERTICAL = "GENERIC"
INPUT_FILES = [ "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/calmattersdigitaldemocracyorg_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/cccaoeorg_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/ccrctccolumbiaedu_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/enwikipediaorg_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/icangotocollegecom_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/laocagov_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/nscresearchcenterorg_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/wwwaaccncheedu_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/wwwccccoedu_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/wwwccleagueorg_2025May01_text.jsonl",
                "gs://ccc-crawl_data_xb/crawl_data/jsonl_files/wwwecsorg_2025May01_text.jsonl"]


def create_data_store(project_id: str,
                      data_store_id: str,
                      location: str,
                      data_store_display_name: str):
    '''
    Function to create a GCS data store within the default collection
    '''

    # Establish Discovery Engine client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # Initialize request argument(s)
    data_store = discoveryengine.DataStore(
        display_name=data_store_display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    operation = client.create_data_store(
        request=discoveryengine.CreateDataStoreRequest(
            parent=client.collection_path(project_id, location, "default_collection"),
            data_store=data_store,
            data_store_id=data_store_id,
        )
    )

    # Make the request
    response = operation.result(timeout=90)
    print("Data store created: {}".format(response.name))
    return response.name


def update_datastore(project_id: str,
                     data_store_id: str,
                     location: str):
    '''
    Function to update a datastore usually to pass JSON structured data schema
    '''

    # Get data store path name
    data_store_path_name = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}"

    # Set a Discovery Engine client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # Update data store for JSON schema
    filename = "gcs_json_schema.json"
    with open(filename, 'r') as infile:
        schema_body = json.load(infile)

    # Send PATCH request with updated structured data JSON
    struct_schema = {"structSchema": json.dumps(schema_body)}

    # Create the DataStore object with the updated schema
    data_store = discoveryengine.DataStore(
        name=data_store_path_name,
        struct_schema=struct_schema,
    )
#
    # Create the FieldMask to indicate that only struct_schema is being updated
    update_mask = field_mask_pb2.FieldMask(paths=["struct_schema"])

    # Call the API
    updated_store = client.update_data_store(
        data_store=data_store,
        update_mask=update_mask,
    )

    print(f"Updated data store: {updated_store.name}")


def import_documents(project_id: str,
                     location: str,
                     data_store_id: str,
                     gcs_uri: str,
                     input_files: list):
    '''
    Function to import documents to a GCS data store
    '''

    # Create a client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # The full resource name of the search engine branch.
    # e.g. projects/{project}/locations/{location}/dataStores/{data_store_id}/branches/{branch}
    parent = client.branch_path(project=project_id,
                                location=location,
                                data_store=data_store_id,
                                branch="default_branch",
                                )

    # Create a path to the source documents
    if len(input_files) > 0:
        source_documents = INPUT_FILES
    else:
        source_documents = [f"{gcs_uri}"]

    # Send an import documents request
    request = discoveryengine.ImportDocumentsRequest(parent=parent,
                                                     gcs_source=discoveryengine.GcsSource(
                                                         input_uris=source_documents,
                                                         data_schema="content"
                                                     ),
                                # Options: `FULL`, `INCREMENTAL`
                                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
                                                     )

    # Make the request
    operation = client.import_documents(request=request)

    response = operation.result()

    # Once the operation is complete, get information from operation metadata
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)

    # Handle the response
    print("Operation status: {}".format(operation.operation.name))
    return operation.operation.name


def create_engine(project_id: str,
                  location: str,
                  engine_name: str,
                  engine_id: str,
                  data_store_id: str):
    '''
    Function to create a search engine
    '''

    # Create a client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.EngineServiceClient(client_options=client_options)

    # Initialize request argument(s)
    engine = discoveryengine.Engine(display_name=engine_name,
                                    solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
                                    industry_vertical=discoveryengine.IndustryVertical.GENERIC,
                                    data_store_ids=[data_store_id],
                                    search_engine_config=discoveryengine.Engine.SearchEngineConfig(
                                        search_tier=discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE),
                                    )

    request = discoveryengine.CreateEngineRequest(parent=client.collection_path(project_id,
                                                                                location,
                                                                                "default_collection"),
                                                  engine=engine,
                                                  engine_id=engine.display_name
                                                  )

    # Make the request
    operation = client.create_engine(request=request)
    response = operation.result(timeout=90)
    print("Engine create: {}".format(response.name))
    return response.name

def list_all_data_stores(project_id: str, location: str) -> list[discoveryengine.DataStore]:
    """
    Lists all data stores in a given project and location.
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

def delete_data_store(data_store_path_name: str,
                      location: str):
    '''
    Function to delete data stores
    '''

    print("Deleting {}".format(data_store_path_name))

    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    client.delete_data_store(name=data_store_path_name)


#----------------- Main ----------------
def main():
    """Main function to orchestrate the creation process."""

    # List all data stores
    datastores = list_all_data_stores(project_id=PROJECT_ID,
                                      location=LOCATION)
    print("Existing data stores")
    for ds in datastores:
        print(ds.name)

    # Delete data stores if needed
    delete_all_stores = False
    if delete_all_stores:
        for ds in datastores:
            delete_data_store(data_store_path_name=ds.name,
                              location=LOCATION)

    # Create a data store
    print("starting data store creation")
    create_data_store(project_id=PROJECT_ID,
                      data_store_id=DATA_STORE_ID,
                      location=LOCATION,
                      data_store_display_name=DATA_STORE_DISPLAY_NAME)

    # Update the data store if needed
    update_data_store = False
    if update_data_store:
        update_datastore(project_id=PROJECT_ID,
                         data_store_id=DATA_STORE_ID,
                         location=LOCATION)

    # Sleep before loading documents
    print("sleeping")
    # time.sleep(15)

    # Import documents
    print("starting document importation")
    # import_documents(project_id=PROJECT_ID,
    #                  location=LOCATION,
    #                  data_store_id=DATA_STORE_ID,
    #                  gcs_uri=GCS_JSONL_URI.format,
    #                  input_files=INPUT_FILES)

    # Create Engine
    print("starting engine creation")
    # create_engine(project_id=PROJECT_ID,
    #               location=LOCATION,
    #               engine_name=ENGINE_NAME,
    #               engine_id=ENGINE_ID,
    #               data_store_id=DATA_STORE_ID)


if __name__ == "__main__":
    main()