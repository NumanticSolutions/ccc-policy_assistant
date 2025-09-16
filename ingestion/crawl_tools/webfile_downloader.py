# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for scraping websites
# Built using Pyppeteer

import os, sys
from io import BytesIO

from urllib.parse import urlparse

import requests
from google.cloud import storage

from pypdf import PdfReader

import warnings
warnings.filterwarnings("ignore")

utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.osa_tools.authentication import ApiAuthentication
import utilities.google_tools.gcp_tools as gct
from utilities.logging.logging_utils import LoggingUtils
from utilities.pdf_parsing.pdf_parser import NumAIPdfParser


class webFileDownloader:
    '''
    Class for downloading files from URL links.

    usage:
        turl = "https://nces.ed.gov/ipeds/datacenter/data/F2223_F2_Stata.zip"
        test = await wc.webScraper.visit_page(url=turl)

        test.crawl_results.keys()
        dict_keys(['url', 'html_code_string', 'soup', 'soup_text', 'h2t_text', 'page_urls'])

    params:

    '''

    def __init__(self, url, **kwargs):
        '''
        Initialize class
        '''

        # Set URL
        self.url = url

        # Path to crawl results data local storage
        self.file_storage_path = ""
        self.gcp_project_id = ""
        self.gcs_bucket_name = ""
        self.gcs_directory = ""

        # Acceptable file extensions
        self.good_file_extentions = [".zip", ".pdf", ".csv"]

        # File download chunk size
        self.chunk_size = 8192

        # Parameters for PDF reading
        self.pdf_text_parser = "pymupdf"
        self.extract_images = False
        self.save_text_data_bq = False
        self.save_images_gcs = True
        self.gcs_location_pdfread = ""
        self.gcs_bucket_name_pdfread = ""
        self.gcs_directory_pdfread = ""
        self.bq_dataset_id_pdfread = ""
        self.bq_table_name_pdfread = ""
        self.bq_if_exists_pdfread = ""
        self.show_progress_bar_pdfread = False

        # Show warnings - note requests verify parameter
        self.show_warnings = False
        if not self.show_warnings:
            warnings.filterwarnings("ignore")

        # Update any key word args
        self.__dict__.update(kwargs)

        # Establish storage names if passed as kwargs
        self.storage_client = storage.Client(project=self.gcp_project_id)
        self.bucket = self.storage_client.bucket(self.gcs_bucket_name)

        # Check if saving to a local path
        if len(self.file_storage_path) > 0 and os.path.exists(self.file_storage_path):
            self.save_location = "local"

        # check if saving to a GCS bucket
        elif len(self.gcp_project_id) > 0:
            self.save_location = "gcs"

        # Otherwise assume src_location is a local path
        else:
            msg = ("The saving location can not be found. It must be a valid local or GCS bucket."
                   "Please investigate.")
            raise ValueError(msg)

        # Get the file basename
        self.filebasename = os.path.basename(urlparse(self.url).path)
        self.file_type = ""

    def validate_filename(self):
        '''
        Method to validate that this is a filetype that can be handled. This method names the class
        attribute for file base name and checks if it has a valid extension.

        return:
            boolean

        '''

        acceptable_file = False

        for file_ext in self.good_file_extentions:
            if self.filebasename.find(file_ext) >= 0:
                self.file_type = file_ext
                acceptable_file = True

        return acceptable_file

    def download_document(self):
        '''
        Method to download the file from a URL.
        '''

        # Check if valid file type
        if self.validate_filename() == False:
            return -1

        try:
            response = requests.get(self.url, stream=True, verify=False)
            response.raise_for_status()

            # Get file size
            self.total_file_size = int(response.headers.get('content-length', 0))
            self.content_type = response.headers.get('content-type', 0)

                # Save to GCS
            if self.save_location == "gcs":

                # Set up the content and content type depending on flags
                if self.file_type == ".zip":
                    buffer = BytesIO()
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:  # Filter out keep-alive chunks
                            buffer.write(chunk)
                    content = buffer.getvalue()
                    content_type = "text/plain"

                elif self.file_type == ".pdf":
                    content = response.content
                    content_type = "application/pdf"

                elif self.file_type == ".csv":
                    content = response.content
                    content_type = "text/csv"

                # Save file to GCS
                gct.save_file_to_bucket(gcs_project_id=self.gcp_project_id,
                                        gcs_bucket_name=self.gcs_bucket_name,
                                        gcs_directory=self.gcs_directory,
                                        file_name=self.filebasename,
                                        content=content,
                                        content_type=content_type)

            # Save to a local location
            elif self.save_location == "local":
                with open(os.path.join(self.file_storage_path,
                                       self.filebasename), 'wb') as file:
                    for data in response.iter_content(chunk_size=self.chunk_size):
                        file.write(data)

            return 1

        except:
            return -1

    def read_document(self):
        '''
        Method to read the file from a URL and return the text.
        '''

        if self.filebasename.find(".csv") >= 0:
            # Todo - complete later
            pass

        elif self.filebasename.find(".zip") >= 0:
            # Todo - complete later
            pass

        elif self.filebasename.find(".pdf") >= 0:

            try:
                doc_metadata = {}
                pdf_parts = NumAIPdfParser(src_location=self.url,
                                           pdf_text_parser=self.pdf_text_parser,
                                           doc_metadata=doc_metadata,
                                           extract_images=self.extract_images,
                                           save_text_data_bq=self.save_text_data_bq,
                                           save_images_gcs=self.save_images_gcs,
                                           gcs_project_id=self.gcp_project_id,
                                           gcs_location=self.gcs_location_pdfread,
                                           gcs_bucket_name=self.gcs_bucket_name_pdfread,
                                           gcs_directory=self.gcs_directory_pdfread,
                                           bq_dataset_id=self.bq_dataset_id_pdfread,
                                           bq_table_name=self.bq_table_name_pdfread,
                                           bq_if_exists=self.bq_if_exists_pdfread,
                                           show_progress_bar=self.show_progress_bar_pdfread
                                           )

                return pdf_parts.df

            except:
                return -1

