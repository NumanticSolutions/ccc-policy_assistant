# © 2025 Numantic Solutions LLC
# MIT License
#
# Create a VertexAI Search datastore

# https://docs.cloud.google.com/generative-ai-app-builder/docs/create-data-store-es#create-datastore-import-data-python
# https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store

# Note: to use this approach, the BigQuery table or view needs a column named view
# Here's how to create a view:
#   CREATE VIEW `your_project_id.ccc_polasst.crawl_text_for_vais` AS
#           SELECT page_id AS _id, page_url, ... , crawl_time FROM `your_project_id.ccc_polasst.crawl_text`;


import os, sys
import time

# Numantic utilities
utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.logging.logging_utils import LoggingUtils
from utilities.osa_tools.authentication import ApiAuthentication

# Configure environmental variables
api_configs = ApiAuthentication(client="CCC")


from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

def create_vais_data_store(project_id: str,
                           location: str,
                           data_store_id: str,
                           display_name: str) -> str:

    # Configure client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # The full resource name - projects/{project}/locations/{location}/collections/default_collection
    parent = client.collection_path(
        project=project_id,
        location=location,
        collection="default_collection",
    )

    data_store = discoveryengine.DataStore(display_name=display_name,
                                           industry_vertical=discoveryengine.IndustryVertical.GENERIC,
                                           solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
                                           content_config=discoveryengine.DataStore.ContentConfig.NO_CONTENT
                                           )

    request = discoveryengine.CreateDataStoreRequest(parent=parent,
                                                     data_store_id=data_store_id,
                                                     data_store=data_store
                                                     )

    # Make the request
    operation = client.create_data_store(request=request)

    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    # After the operation is complete - get information from operation metadata
    metadata = discoveryengine.CreateDataStoreMetadata(operation.metadata)

    # Handle the response
    print(response)
    print(metadata)

    return operation.operation.name

def import_documents_from_bigquery(project_id: str,
                                   location: str,
                                   data_store_id: str,
                                   bigquery_dataset: str,
                                   bigquery_table: str
                                   ) -> None:
    """
    Imports documents from a BigQuery table into the Data Store.
    """

    #  Configure client
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # The full resource name of the search engine branch.
    # e.g. projects/{project}/locations/{location}/dataStores/{data_store_id}/branches/{branch}
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        bigquery_source=discoveryengine.BigQuerySource(
            project_id=project_id,
            dataset_id=bigquery_dataset,
            table_id=bigquery_table,
            data_schema="custom"
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    # Make the request
    operation = client.import_documents(request=request)

    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    # After the operation is complete,
    # get information from operation metadata
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)

    # Handle the response
    print(response)
    print(metadata)

# --- Main Execution Block ---
def main():

    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = "global"
    data_store_id = "web-text-datastore-v4"
    display_name = "web-text-datastore-v4"

    bigquery_dataset = "ccc_polasst"
    # bigquery_table = "crawl_text"
    bigquery_table = "crawl_text_for_vais"
    id_field = "page_id"

    # 1. Create the Data Store
    data_store_name = create_vais_data_store(project_id=project_id,
                                             location=location,
                                             data_store_id=data_store_id,
                                             display_name=display_name)

    # 2. Ingest data from BigQuery
    import_documents_from_bigquery(project_id=project_id,
                                   location=location,
                                   data_store_id=data_store_id,
                                   bigquery_dataset=bigquery_dataset,
                                   bigquery_table=bigquery_table)


if __name__ == "__main__":
    main()




