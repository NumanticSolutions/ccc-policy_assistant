# © 2025 Numantic Solutions LLC
# MIT License
#
# Create a Vertex AI Search app that can be used in an ADK agent


import os, sys
import time

# Numantic utilities
if os.environ['USER'] == 'numantic':
    utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
else:
    utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.osa_tools.authentication import ApiAuthentication
import utilities.google_tools.bigquery_tools as bqt
import utilities.ai_tools.vertexai.vais_datastore as vais_ds
import utilities.ai_tools.vertexai.vais_searchapp as vais_sa

# Authenticate
api_configs = ApiAuthentication(client="CCC")

if __name__ == "__main__":

    ### Step 1. Set parameters
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    # gcp_location = os.environ["GOOGLE_CLOUD_LOCATION"]
    gcp_location = "global"
    dataset_id = "ccc_polasst"
    src_table_name = "crawl_text"
    view_name = "crawl_text_vais_view"
    view_descr = "Web text view for a Vertex AI search app"

    view_cols = ["page_id", "page_url", "seed_url", "page_name", "clean_headings_text",
                 "media_type", "language_code", "organization"]
    id_col = "page_id"
    where_params = {"media_type": ["pdf file", "web page text"]}
    rename_id_col = True

    data_store_id = "dstore_{}".format(view_name)
    data_store_ids = [data_store_id]
    data_store_display_name = "CCC web text data store: Source: {}".format(view_name)

    engine_id = "webtext_search_app"
    search_app_display_name = "CCC web text search app"

    ### Step 2. Create a view of the BigQuery table with webtext
    bqt.create_bq_table_view(project_id=project_id,
                             dataset_id=dataset_id,
                             src_table_name=src_table_name,
                             view_name=view_name,
                             view_cols=view_cols,
                             id_col=id_col,
                             where_params=where_params,
                             view_descr=view_descr,
                             rename_id_col=rename_id_col)

    time.sleep(10)

    ### Step 3. Create a Vertex AI Search Data Store
    data_store_name = vais_ds.create_vais_data_store(project_id=project_id,
                                                     location=gcp_location,
                                                     data_store_id=data_store_id,
                                                     display_name=data_store_display_name
                                                     )

    time.sleep(10)

    ### Step 4. Import BigQuery data
    vais_ds.import_documents_from_bigquery(project_id=project_id,
                                           location=gcp_location,
                                           data_store_id=data_store_id,
                                           bigquery_dataset=dataset_id,
                                           bigquery_table=view_name
                                       )
    time.sleep(10)

    ### Step 3. Create a Vertex AI Search App
    engine_name = vais_sa.create_search_engine_from_datastore(project_id=project_id,
                                                              location=gcp_location,
                                                              engine_id=engine_id,
                                                              display_name=search_app_display_name,
                                                              data_store_ids=data_store_ids
                                                              )