# © 2025 Numantic Solutions LLC
# MIT License
#

# GCP
# from google.cloud import secretmanager
import os
import io
import json

import pandas as pd
import pandas_gbq as pbq

from google.cloud import storage
from google.cloud import bigquery
import google
import google.oauth2.credentials
from google.auth import compute_engine
import google.auth.transport.requests

# import pandas_gbq as gbq

# def get_gcpsecrets(project_id,
#                    secret_id,
#                    version_id="latest"):
#     """
#     Access a secret version in Google Cloud Secret Manager.
#
#     Args:
#         project_id: GCP project ID.
#         secret_id: ID of the secret you want to access.
#         version_id: Version of the secret (defaults to "latest").
#
#     Returns:
#         The secret value as a string.
#     """
#     # Create the Secret Manager client
#     client = secretmanager.SecretManagerServiceClient()
#
#     # Build the resource name of the secret version
#     name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
#
#     # Access the secret version
#     response = client.access_secret_version(request={"name": name})
#
#     # Return the payload as a string
#     # Note: response.payload.data is a bytes object, decode it to a string
#     return response.payload.data.decode("UTF-8")

def table_exists(project_id, dataset_id, table_id):
    '''
    Function to determine if a BigQuery dataset table exists
    :param dataset_id:
    :param table_id:
    :return:
    '''
    try:
        sql = ("SELECT 1 FROM `{}.{}` LIMIT 0").format(dataset_id, table_id)
        gbq.read_gbq(sql,  project_id=project_id)
        return True
    except gbq.gbq.GenericGBQException as e:
        if "Not found" in str(e):
            return False
        else:
            raise e

def gcp_list_bucket(gcp_project_id, gcs_bucket_name, path=""):
    '''
    Function to list all files in a GCP Cloud Storage directory
    '''

    # Create a storage client
    storage_client = storage.Client(project=gcp_project_id)

    # Get the bucket
    bucket = storage_client.bucket(gcs_bucket_name)

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket)

    # Note: The call returns a response only when the iterator is consumed.
    blob_names = [blob.name for blob in blobs]

    if path != "":
        blob_names = [bn for bn in blob_names if bn.find(path) >= 0]

    return blob_names

def read_gcs_file(gcp_project_id, gcs_bucket_name, path, filename):
    '''
    Function to read a GCP Cloud Storage file
    '''

    # Create a storage client
    storage_client = storage.Client(project=gcp_project_id)

    # Get the bucket
    bucket = storage_client.bucket(gcs_bucket_name)

    # Create a path to the file
    file_blob_path = os.path.join(path, filename)
    blob = bucket.blob(file_blob_path)

    return io.BytesIO(blob.download_as_string())

def upload_directory_to_gcs(local_directory, gcs_project_id,
                            gcs_bucket_name, gcs_directory):
    '''
    Function to upload a directory to Google Cloud Storage

    :param local_directory:
    :param bucket_name:
    :param gcs_directory:

    :return:
    '''

    # Initialize GCS client
    storage_client = storage.Client(project=gcs_project_id)
    bucket = storage_client.bucket(bucket_name=gcs_bucket_name)

    for root, _, files in os.walk(local_directory):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(local_file_path, local_directory)

            # Check if files should be stored in subdirectory of directly in bucket
            if gcs_directory == "":
                blob = bucket.blob(os.path.join(relative_path))
            else:
                blob = bucket.blob(os.path.join(gcs_directory, relative_path))

            # Upload
            blob.upload_from_filename(local_file_path)
            print(f"Uploaded {local_file_path} to gs://{gcs_bucket_name}/{gcs_directory}{relative_path}")

def download_directory_from_gcs(gcs_project_id, gcs_bucket_name,
                                gcs_directory, local_directory):
    '''
    Function to download a folder in Google Cloud Storage bucket to a local directory

    :param local_directory:
    :param bucket_name:
    :param gcs_directory:

    :return:
    '''

    # Initialize GCS client
    storage_client = storage.Client(project=gcs_project_id)
    bucket = storage_client.bucket(bucket_name=gcs_bucket_name)

    blobs = bucket.list_blobs(prefix=gcs_directory)

    for blob in blobs:
        if not blob.name.endswith("/"):  # Avoid directory blobs
            relative_path = os.path.relpath(blob.name, gcs_directory)
            local_file_path = os.path.join(local_directory, relative_path)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            blob.download_to_filename(local_file_path)
            print(f"Downloaded {blob.name} to {local_file_path}")

def idtoken_from_metadata_server(url: str, service_account_email: str):
    """
    Use the Google Cloud metadata server in the Cloud Run (or AppEngine or Kubernetes etc.,)
    environment to create an identity token and add it to the HTTP request as part of an
    Authorization header. This is an OIDC token (I think).

    Args:
        url: The url or target audience to obtain the ID token for.
            Examples: http://www.example.com
    """

    request = google.auth.transport.requests.Request()
    # Set the target audience.
    # Setting "use_metadata_identity_endpoint" to "True" will make the request use the default application
    # credentials. Optionally, you can also specify a specific service account to use by mentioning
    # the service_account_email.

    # credentials = compute_engine.IDTokenCredentials(
    #     request=request, target_audience=url,
    #     use_metadata_identity_endpoint=True
    # )

    credentials = compute_engine.IDTokenCredentials(
        request=request, target_audience=url, service_account_email=service_account_email
    )

    # Get the ID token.
    # Once you've obtained the ID token, use it to make an authenticated call
    # to the target audience.
    credentials.refresh(request)
    # print(credentials.token)
    print("Generated ID token.")

def read_json_file(gcs_project_id, gcs_bucket_name,
                   gcs_directory, file_name,
                   exact=False):
    '''
    Method to read a csv file from GCS into a pandas dataframe

    Inputs
        exact: a boolean indicating whether the filename needs to be an exact match
        or just a search string
    '''

    # Initialize GCS client
    storage_client = storage.Client(project=gcs_project_id)
    bucket = storage_client.bucket(bucket_name=gcs_bucket_name)

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket, prefix=gcs_directory)

    # Note: The call returns a response only when the iterator is consumed.
    for blob in blobs:
        if blob.name.find(file_name) >= 0:

            # If exact, the file_name must be an exact match
            if exact == True and blob.name != file_name:
                pass

            else:
                # Get the blob
                blob_file = bucket.blob(blob.name)

                # Works
                data = blob_file.download_as_bytes()
                return json.loads(blob_file.download_as_string(client=None))

    return None

def read_csv_file_into_pandas(gcs_project_id, gcs_bucket_name,
                              gcs_directory, file_name,
                              exact=False):
    '''
    Method to read a csv file from GCS into a pandas dataframe

    Inputs
        exact: a boolean indicating whether the filename needs to be an exact match
        or just a search string
    '''

    # Initialize GCS client
    storage_client = storage.Client(project=gcs_project_id)
    bucket = storage_client.bucket(bucket_name=gcs_bucket_name)

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket, prefix=gcs_directory)

    # Note: The call returns a response only when the iterator is consumed.
    for blob in blobs:
        if blob.name.find(file_name) >= 0:

            # If exact, the file_name must be an exact match
            if exact == True and blob.name != file_name:
                pass

            else:
                # Get the blob
                blob_file = bucket.blob(blob.name)

                # Works
                data = blob_file.download_as_bytes()
                return pd.read_csv(io.BytesIO(data))

    return None

def save_file_to_bucket(gcs_project_id, gcs_bucket_name,
                        gcs_directory, file_name, content):
    '''
    Save to file to a GCP bucket
    '''

    # Set GCS class variables
    storage_client = storage.Client(project=gcs_project_id)
    gcs_bucket = storage_client.bucket(gcs_bucket_name)

    # Save data in a CSV file
    blob = gcs_bucket.blob(os.path.join(gcs_directory, file_name))
    # blob.upload_from_string(file_name)
    blob.upload_from_string(content)

def load_csv_to_bigquery(project_id, dataset_name, table_name, csv_filepath):
    """Loads a CSV file into a BigQuery table.

    Args:
        project_id: The ID of the Google Cloud project.
        dataset_name: The name of the BigQuery dataset.
        table_name: The name of the BigQuery table.
        csv_filepath: The path to the CSV file.
    """

    client = bigquery.Client(project=project_id)

    dataset_ref = client.dataset(dataset_name)
    table_ref = dataset_ref.table(table_name)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # Skip the header row
        autodetect=True,  # Automatically detect the schema
    )

    with open(csv_filepath, "rb") as source_file:
        job = client.load_table_from_file(
            source_file, table_ref, job_config=job_config
        )

    job.result()  # Wait for the job to complete

    print(f"Loaded {job.output_rows} rows into {dataset_name}.{table_name}")


def create_dataset_if_not_exists(project_id, dataset_name):
    """Creates a BigQuery dataset if it does not already exist.

    Args:
        project_id: The ID of the Google Cloud project.
        dataset_name: The name of the BigQuery dataset.
    """
    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.{dataset_name}"

    try:
        client.get_dataset(dataset_id)  # Make an API request.
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"  # Set the location (e.g., "US", "EU")
        dataset = client.create_dataset(dataset, timeout=30)  # Make an API request.
        print(f"Created dataset {dataset_id}")

def load_pandas_to_bigquery(project_id, df,
                            dataset_id, table_name):
    """Loads a Pandas Dataframe into a BigQuery table.

    Args:
        project_id: The ID of the Google Cloud project.
        df: Pandas dataframe

        dataset_id: The name of the BigQuery dataset.
        table_id: The name of the BigQuery table.
    """

    table_id ="{}.{}".format(dataset_id, table_name)

    pbq.to_gbq(dataframe=df,
               destination_table=table_id,
               project_id=project_id)


    # client = bigquery.Client(project=project_id)
    #
    # # Define how the data should be written
    # job_config = bigquery.LoadJobConfig(
    #     # WRITE_TRUNCATE: If the table already exists, BigQuery overwrites the table data.
    #     # WRITE_APPEND: If the table already exists, BigQuery appends the data to the table. (Default)
    #     # WRITE_EMPTY: If the table already exists and contains data, a 'duplicate' error is returned.
    #     write_disposition="WRITE_TRUNCATE",
    # )

    # # Create the table reference
    # # table_ref_full = f"{project_id}.{dataset_id}.{table_id}"
    # # table_ref = client.dataset(dataset_id).table(table_id)
    # #
    # # # Start the load job
    # # # The library handles serializing the DataFrame and uploading it
    # # load_job = client.load_table_from_dataframe(dataframe=df,
    # #                                             destination=table_ref,
    # #                                             job_config=job_config
    # #                                             )
    #
    # # Wait for the job to complete
    # load_job.result()  # Waits for the job to finish
    # # print("Table created.")
