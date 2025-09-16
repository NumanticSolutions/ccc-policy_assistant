# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for crawling and scraping multiple websites

import sys, os
import json
from datetime import datetime
import time

import pandas as pd
from urllib.parse import urlparse

import random
from tqdm import tqdm

from google.cloud import storage

import asyncio
import web_scraper as ws
import webfile_downloader as wfd

utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.osa_tools.authentication import ApiAuthentication
import utilities.google_tools.gcp_tools as gct
import utilities.text_cleaning.text_cleaning_tools as tct
from utilities.logging.logging_utils import LoggingUtils

api_configs = ApiAuthentication(client="CCC")

class webCrawler:
    '''
    Class to crawl multiple websites starting with a seed URL. The main method for crawling is
    crawl_sites, and its basic logic is to start with a seed URL and then crawl pages found on that
    website limited by the depth and width parameter. Width is the maximum number of webpages to crawl
    from each page crawled and depth is how many pages should provide source URLs before the process is
    stopped.

    This function uses the webCrawler class to scrape data from each website. Results are periodically
    inserted into a Pandas Dataframe and saved to CSV files.

    Args:
        seed_url: str
            The first URL to crawl for at a target website. From this seed URL, the crawler will look for
            additional URLS to crawl limited by the depth and width paramters (passed to the crawl_sites
            method)
        save_location: str
            A flag indicating where crawl results should be saved to a GCS bucket in a file ('gcs') or into
            BigQuery table ('bq') or local path ('local').
        log_crawls: bool
            A boolean indicating if log files of the crawls should be created.
    '''
    
    def __init__(self,
                 seed_url: str,
                 source_index: str,
                 save_location: str,
                 log_crawls: bool=True,
                 **kwargs):

        # Date format
        self.dtformat = "%Y-%m-%d %H:%M:%S"

        # Sleep time between crawls (secs)
        self.wait_time = 5

        # Save threshold - crawler will save results in batches of this size
        self.save_threshold = 100
        self.save_location = save_location

        # Maximum webpages
        self.max_crawls = 1000

        # Counts
        self.crawl_cnt = 0  # Number of sites crawled
        self.files_cnt = 0  # Number of files downloaded
        self.crawl_results_cnt = 0 # Number of sites producing crawl results
        self.saved_batch_cnt = 0  # Number of saved batches

        # Path to crawl results data local storage
        self.results_path = ""
        self.gcp_project_id = ""
        self.gcs_bucket_name = ""
        self.gcs_directory = ""
        self.bq_dataset_id = ""
        self.bq_table_name = ""
        self.bq_if_exists = ""

        # Output filename base - if this is blank, the crawler will assign a name
        self.output_filename_base = ""

        # Acceptable file extensions
        self.file_extentions = [".zip", ".pdf", ".csv"]

        # Seed url
        self.seed_url = seed_url
        self.source_index = source_index

        # Good domains - if blank only the seed url
        # If not blank it will be overwritten when keywords are updated
        self.good_domains = [urlparse(self.seed_url).netloc]

        # Other parameters
        self.log_crawls = log_crawls
        self.log_modes = ["screen", "file", "gcp"]
        self.logs_file_path = "data/logs"
        self.date_format = "%Y%m%d"
        self.logfile_name = None
        self.organization = ""

        # Update any key word args
        self.__dict__.update(kwargs)

        # Check that save locations are set
        if self.save_location == "bq":
            if self.bq_dataset_id == "" or self.bq_table_name == "" or self.bq_if_exists == "":
                msg = ("When saving to Bigquery (save_location = 'bq') both the bq_table_name and "
                       "bq_if_exists variables need values passed through kwargs; Please investigate.")
                raise ValueError(msg)

        elif self.save_location == "gcs":
            if self.gcp_project_id == "" or self.gcs_bucket_name == "":
                msg = ("When saving to Google Cloud (save_location = 'gcs') both the gcp_project_id and "
                       "gcs_bucket_name variables need values passed through kwargs; Please investigate.")
                raise ValueError(msg)

            # Set GCS class variables
            self.storage_client = storage.Client(project=self.gcp_project_id)
            self.gcs_bucket = self.storage_client.bucket(self.gcs_bucket_name)

        # Set up logger
        if self.log_crawls:
            self.logging_utils = LoggingUtils(log_modes=self.log_modes,
                                              logs_file_path=self.logs_file_path)

            # Start logger
            self.logger = self.logging_utils.create_logger(logfile_name=self.logfile_name)
    
    async def crawl_sites(self,
                          dont_crawl_urls,
                          crawl_urls,
                          depth,
                          width):
        '''
        Functions for crawling and scraping multiple websites. Its basic logic is to start with a
        seed URL and then crawl pages found on that website limited by the depth and width parameter.
        Width is the maximum number of webpages to crawl from each page crawled and depth is how many
        pages should provide source URLs before the process is stopped.
    
        This function uses the webCrawler class to scrape data from each website. Results are periodically
        inserted into a Pandas Dataframe and saved to CSV files.
    
        params:
            seed_url:str: url to first crawl
            dont_crawl_urls: list: urls that should not be crawled (most likely because we crawled before)
            depth: int: depth of crawl
            width: int: width of crawl
    
        '''

        ## Step 0.25: Set up logging
        if self.log_crawls:
            evt_msg = "Configuring crawl for seed url: {}".format(self.seed_url)
            self.logging_utils.log_event(logger=self.logger,
                                         log_entry=dict(file=os.path.basename(__file__),
                                                        event=evt_msg
                                                        )
                                         )

        ## Step 0.5: Set up crawling records
        # A list of dictionaries to hold crawl results
        all_sites_results = []
        # A list of sites to crawl - usually these come from URLs found on crawled pages
        to_crawl_urls = []
    
        # Clean up seed_url by removing last slash
        if self.seed_url[-1] == "/" or self.seed_url[-1] == "\\":
            self.seed_url = self.seed_url[:-1]

        ## Step 1: Validate
        if self.seed_url in dont_crawl_urls:
            msg = ("The seed URL is in the don't crawl list (dont_crawl_urls); "
                   "Please remove it if you want to continue.")
            raise Exception(msg)
    
        # Step 2: Start crawling additional sites
        # Use the for loop to count depth
        for depth_cnt in tqdm(range(1, depth + 1)):
    
            # Step 2.1: Set first crawl list equal to only the seed URL
            if depth_cnt == 1:
                # Add seed as first URL to crawl
                to_crawl_urls = [self.seed_url] + crawl_urls

                if self.log_crawls:
                    evt_msg = "Depth: {}: 1; Len to_crawl_urls: {}".format(depth_cnt, len(to_crawl_urls))
                    self.logging_utils.log_event(logger=self.logger,
                                                 log_entry=dict(file=os.path.basename(__file__),
                                                                event=evt_msg
                                                                )
                                                 )
    
            ## Step 2.2: Get a random set of URLs to crawl (equal width)
            if width < len(to_crawl_urls):
                r_urls = random.sample(to_crawl_urls, width)
            else:
                r_urls = to_crawl_urls
    
            ##  Step 2.3: Create a new list of URLs found at this depth level
            found_urls = []

            ## Step 2.4: Crawl all randomly selected URLs
            # print("Depth level: {}: {} URLs".format(depth_cnt, len(r_urls)))
            for r_url in r_urls:

                ## Step 2.5: Check if this URL is on the dont_craw_list
                if r_url not in dont_crawl_urls and self.is_good_domain(r_url) == True:

                    ## Step 2.6. Check if this is a pdf that we want to read
                    if self.is_file_url(r_url) == ".pdf":

                        # Read file content
                        fd_obj = wfd.webFileDownloader(url=r_url)
                        rf_res = fd_obj.read_document()

                        ## Step 2.7: Crawl and pause
                        if rf_res != -1 and len(rf_res) > 0:

                            # Add this to the dataframe of crawl results
                            idx0 = 0
                            doc_metadata = json.loads(rf_res.loc[idx0, "src_doc_metadata"])

                            if "title" in doc_metadata and doc_metadata["title"] != "nan":
                                page_title = doc_metadata["title"]
                            else:
                                page_title = ""

                            if "subject" in doc_metadata and doc_metadata["subject"] != "nan":
                                page_descr = doc_metadata["subject"]
                            else:
                                page_descr = ""

                            # Add this content to the dataframe
                            all_sites_results.append(dict(page_url=r_url,
                                                          seed_url=self.seed_url,
                                                          source_index=self.source_index,
                                                          page_title=page_title,
                                                          page_name="",
                                                          page_descr=page_descr,
                                                          page_text=tct.clean_web_texts(web_texts=t["md_text"].tolist()),
                                                          media_type="pdf file",
                                                          language_code="en-US",
                                                          organization=self.organization,
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          )
                                                     )
                            self.files_cnt += 1

                    ## Step 2.8: Check if this is a zip or csv file that we want to download
                    elif self.is_file_url(r_url) in [".zip", ".csv"]:

                        # Download file content
                        fd_obj = wfd.webFileDownloader(url=r_url,
                                                       gcp_project_id=self.gcp_project_id,
                                                       gcs_directory=os.path.join("{}/zipcsv_files".format(self.gcs_directory)))
                        dd_res = fd_obj.download_document()

                        # Add this to the dataframe of crawl results
                        if dd_res != -1:

                            # Add details of the file download to the data dictionary
                            all_sites_results.append(dict(page_url=r_url,
                                                          seed_url=self.seed_url,
                                                          source_index=self.source_index,
                                                          page_title="",
                                                          page_name="",
                                                          page_descr="",
                                                          page_text="file download",
                                                          media_type="{} file".format(self.is_file_url(r_url)),
                                                          language_code="en-US",
                                                          organization=self.organization,
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          )
                                                     )

                            self.files_cnt += 1

                    ## Step 2.9: Crawl and pause
                    else:
                        self.crawl_cnt += 1
                        crawl = ws.webScraper()
                        crawl.visit_page(url=r_url)

                        # Pause
                        time.sleep(self.wait_time)

                        ## Step 2.10: Add these crawl results to the list of dictionaries; if data return
                        if len(crawl.result) > 0:

                            # Add to count of found crawl results
                            self.crawl_results_cnt += 1

                            ## Add these crawl results
                            all_sites_results.append(dict(page_url=r_url,
                                                          seed_url=self.seed_url,
                                                          source_index=self.source_index,
                                                          page_title="" if crawl.result["page_title"] == "nan" \
                                                                else crawl.result["page_title"],
                                                          page_name="" if crawl.result["site_name"] == "nan" \
                                                                else crawl.result["site_name"],
                                                          page_descr="" if crawl.result["description"] == "nan" \
                                                                else crawl.result["description"],
                                                          page_text="{} {}".format(crawl.result["ptag_text"],
                                                                                   crawl.result["divtag_text"]).strip(),
                                                          media_type="web page text",
                                                          language_code="en-US",
                                                          organization=self.organization,
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          )
                                                     )

                            ## Step 2.11: Add found URLs to the found URLs list
                            found_urls.extend(crawl.result["atag_urls"])

                    ## Step 2.12: Check if results should be saved
                    if self.crawl_results_cnt % self.save_threshold == 0:
                        self.save_results_batch(all_sites_results=all_sites_results)

                        # reset results to an empty list
                        all_sites_results = []

                    ## Step 2.13: Check if this job is hitting a crawl maximum and should stop
                    if self.crawl_cnt >= self.max_crawls:
                        break

                else:

                    dont_crawl_urls.append(r_url)
    
            ## Step 2.14: Eliminate dups in found_urls
            found_urls = list(set(found_urls))
    
            ## Step 2.15: Add crawled URL to the dont-crawl list; two versions with and without final slash
            dont_crawl_urls.extend(r_urls)
            dont_crawl_urls.extend(["{}/".format(u) for u in r_urls])
    
            ## Step 2.16: Remove dont-crawl URLs from to_crawl list
            to_crawl_urls = [u for u in found_urls if u not in dont_crawl_urls]
    
            ## Step 2.17: Update User
            evt_msg = ("Depth level finished: {}: {} URLs crawled; {} files downloaded; "
                       "{} URLs in to_crawl_urls; {} URLs in dont_crawl_urls").format(depth_cnt,
                                                                                      self.crawl_cnt,
                                                                                      self.files_cnt,
                                                                                      len(to_crawl_urls),
                                                                                      len(dont_crawl_urls)
                                                                                      )
            self.logging_utils.log_event(logger=self.logger,
                                         log_entry=dict(file=os.path.basename(__file__),
                                                        event=evt_msg
                                                        )
                                         )
    
        ### Step 2.18:. Save results not already yet saved
        self.save_results_batch(all_sites_results=all_sites_results)

    def save_results_batch(self, all_sites_results):
        '''
        Function to save a batch of crawl results
        :return:
        '''

        # Create a results file name
        # seed URL host
        purl = urlparse(self.seed_url)
        seedhost = purl.hostname.replace(".", "")

        # Crawl date
        cd_dtformat = "%Y%b%d"
        crwl_dt = datetime.now().strftime(cd_dtformat)

        # batch number
        self.saved_batch_cnt += 1

        # results filename
        if self.output_filename_base == "":
            res_filename = "{}_{}_{}.csv".format(seedhost, crwl_dt,
                                                 self.saved_batch_cnt)
        else:
            res_filename = "{}_{}_{}.csv".format(self.output_filename_base,
                                                 crwl_dt, self.saved_batch_cnt)

        # Check if any results to be saved
        if len(all_sites_results) > 0:

            # Create a dataframe
            df = pd.DataFrame(data=all_sites_results)

            # Save crawl data on GCS or BigQuery or locally
            if self.save_location == "gcs":
                gct.write_pandas_as_csv_file_on_gcs(gcs_project_id=self.gcp_project_id,
                                                    df=df,
                                                    gcs_bucket_name=self.gcs_bucket_name,
                                                    gcs_directory="{}/webpages_pdfs".format(self.gcs_directory),
                                                    file_name=res_filename)

            # Save data in a CSV file
            elif self.save_location == "local":
                df.to_csv(path_or_buf=os.path.join(self.results_path, res_filename))

            elif self.save_location == "bq":

                gct.load_pandas_to_bigquery(df=df,
                                            dataset_id=self.bq_dataset_id,
                                            table_name=self.bq_table_name,
                                            project_id=self.gcp_project_id,
                                            if_exists=self.bq_if_exists,
                                            progress_bar_type=None)


            ## Update User
            evt_msg = ("Batch {} saved to disk in {}/webpages_pdfs.").format(self.saved_batch_cnt,
                                                                                self.gcs_directory)
            self.logging_utils.log_event(logger=self.logger,
                                         log_entry=dict(file=os.path.basename(__file__),
                                                        event=evt_msg
                                                        )
                                         )

        # Close logger
        if self.log_crawls:
            self.logging_utils.close_logger()

    def is_file_url(self, url):
        '''
        Method to determine if the URL points to a file to be downloaded; If a valid
        file extension can be found, return the value of the file extension. Otherwise,
        return None.
        '''

        # Get the file basename
        filebasename = os.path.basename(urlparse(url).path)

        for file_ext in self.file_extentions:
            if filebasename.find(file_ext) >= 0:
                return file_ext

        return None

    def is_good_domain(self, url):
        '''
        Method to determine if the URL points to a bad domain
        '''

        is_good = False

        purl = urlparse(url)
        for bd in self.good_domains:
            if purl.netloc.find(bd) >= 0:
                is_good = True

        return is_good

