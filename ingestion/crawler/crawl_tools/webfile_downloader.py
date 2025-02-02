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

    def __init__(self, url):
        '''
        Initialize class
        '''

        # Set URL
        self.url = url

        # Path to crawl results data local storage
        self.file_storage_path = ("/Users/stephengodfrey/OneDrive - numanticsolutions.com/"
                                  "Engagements/Projects/ccc_policy_assistant/data/testfiles")
        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcs_bucket_name = "webfiles-test"
        self.gcs_directory = "ipeds"
        self.storage_client = storage.Client(project=self.gcp_project_id)
        self.bucket = self.storage_client.bucket(self.gcs_bucket_name)

        # Acceptable file extensions
        self.good_file_extentions = [".zip", ".pdf", ".csv"]

        # Show progress bar
        self.show_progress_bar = False

        # File download chunk size
        self.chunk_size = 8192

        # Check if acceptable
        if self.validate_filename():

            # Create output directory if it doesn't exist
            os.makedirs(self.file_storage_path, exist_ok=True)


            # Download the file
            self.download_document()


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


        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()

            # Get file size
            self.total_file_size = int(response.headers.get('content-length', 0))

            if self.show_progress_bar:
                # with open(os.path.join(self.file_storage_path,
                #                        self.filebasename), 'wb') as file, tqdm(desc= self.filebasename,
                #                                                                total=self.total_file_size,
                #                                                                unit='iB',
                #                                                                unit_scale=True) as progress_bar:
                #     for data in response.iter_content(chunk_size=self.chunk_size):
                #         size = file.write(data)
                #         progress_bar.update(size)
                pass

            else:
                blob = self.bucket.blob(os.path.join(self.gcs_directory, self.filebasename))
                # with open(os.path.join(self.file_storage_path,
                #                        self.filebasename), 'wb') as file:
                with blob.open("wb") as file:
                    for data in response.iter_content(chunk_size=self.chunk_size):
                        file.write(data)

        except:
            pass
