# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for scraping websites
# Built using Pyppeteer

import os
from urllib.parse import urlparse
import re
import requests
import tqdm
from google.cloud import storage

import warnings

warnings.filterwarnings("ignore")


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
        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcs_bucket_name = "ccc-crawl_data"
        self.gcs_directory = ""
        self.storage_client = storage.Client(project=self.gcp_project_id)
        self.bucket = self.storage_client.bucket(self.gcs_bucket_name)

        # Acceptable file extensions
        self.good_file_extentions = [".zip", ".pdf", ".csv"]

        # File download chunk size
        self.chunk_size = 8192

        # Show warnings - note requests verify parameter
        self.show_warnings = False
        if not self.show_warnings:
            warnings.filterwarnings("ignore")

        # Update any key word args
        self.__dict__.update(kwargs)


    def validate_filename(self):
        '''
        Method to validate that this is a filetype that can be handled. This method names the class
        attribute for file base name and checks if it has a valid extension.

        return:
            boolean

        '''

        # Get the file basename
        self.filebasename = os.path.basename(urlparse(self.url).path)

        acceptable_file = False

        for file_ext in self.good_file_extentions:
            if self.filebasename.find(file_ext) >= 0:
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


            blob = self.bucket.blob(os.path.join(self.gcs_directory, self.filebasename))
            # with open(os.path.join(self.file_storage_path,
            #                        self.filebasename), 'wb') as file:
            with blob.open("wb") as file:
                for data in response.iter_content(chunk_size=self.chunk_size):
                    file.write(data)

            return 1

        except:
            return -1
            pass
