# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for crawling and scraping multiple websites

import sys, os
from datetime import datetime
import time

import pandas as pd
import numpy as np
from urllib.parse import urlparse

import random
from tqdm import tqdm

from google.cloud import storage

import asyncio
import web_scraper as ws
import webfile_downloader as wfd

utils_path = "../../interface/utils"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import gcp_tools as gct

class webCrawler():
    '''
    Class to crawl multiple websites starting with a seed URL. The main method for crawling is
    crawl_sites, and its basic logic is to start with a seed URL and then crawl pages found on that
    website limited by the depth and width parameter. Width is the maximum number of webpages to crawl
    from each page crawled and depth is how many pages should provide source URLs before the process is
    stopped.

    This function uses the webCrawler class to scrape data from each website. Results are periodically
    inserted into a Pandas Dataframe and saved to CSV files.
    '''
    
    def __init__(self,
                 seed_url,
                 **kwargs):

        # Date format
        self.dtformat = "%Y-%m-%d %H:%M:%S"

        # Sleep time between crawls (secs)
        self.wait_time = 1

        # Save threshold - crawler will save results in batches of this size
        self.save_threshold = 100

        # Maximum webpages
        self.max_crawls = 1000

        # Counts
        self.crawl_cnt = 0  # Number of sites crawled
        self.files_cnt = 0  # Number of files downloaded
        self.crawl_results_cnt = 0 # Number of sites producing crawl results
        self.saved_batch_cnt = 0  # Number of saved batches

        # Path to crawl results data local storage
        self.results_path = ""
        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcs_bucket_name = "ccc-crawl_data_xb"
        self.gcs_directory = "crawl_data"

        # Output filename base - if this is blank, the crawler will assign a name
        self.output_filename_base = ""

        # Acceptable file extensions
        self.file_extentions = [".zip", ".pdf", ".csv"]

        # Seed url
        self.seed_url = seed_url

        # Good domains - if blank only the seed url
        # If not blank it will be overwritten when keywords are updated
        self.good_domains = [urlparse(self.seed_url).netloc]

        # Show URLs that are being crawled
        self.verbose = False
        # self.verbose = True

        # Update any key word args
        self.__dict__.update(kwargs)

        # Authenticate by setting environment variables
        dotenv_path = "../../data/environment"
        api_configs = ApiAuthentication(dotenv_path=dotenv_path)
        api_configs.set_environ_variables()

        # Set GCS class variables
        self.storage_client = storage.Client(project=self.gcp_project_id)
        self.gcs_bucket = self.storage_client.bucket(self.gcs_bucket_name)
    
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

    
        ## Step 0.5: Set up crawling records
        # A list of dictionaries to hold crawl results
        all_sites_results = []
        # A list of sites to crawl - usually these come from URLs found on crawled pages
        to_crawl_urls = []
        # Starting depth
        depth_cnt = 0
    
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

                if self.verbose:
                    print("depth: {}: 1; :Len to_crawl_urls: {}".format(depth_cnt, len(to_crawl_urls)))
    
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

                    if self.verbose:
                        print(r_url)

                    ## Step 2.6. Check if this is a pdf that we want to read
                    if self.is_file_url(r_url) == ".pdf":

                        # Read file content
                        fd_obj = wfd.webFileDownloader(url=r_url)
                        rf_res = fd_obj.read_document()

                        ## Step 2.7: Crawl and pause
                        if rf_res != -1:

                            # Add this to the dataframe of crawl results
                            all_sites_results.append(dict(seed_url=self.seed_url,
                                                          page_url=r_url,
                                                          site_name="",
                                                          page_title=rf_res["title"],
                                                          html_code_string="",
                                                          ptag_text=rf_res["text_content"],
                                                          atag_urls="",
                                                          content_type="pdf_file",
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          ))
                            self.files_cnt += 1

                    ## Step 2.8: Check if this is a zip or csv file that we want to download
                    elif self.is_file_url(r_url) in [".zip", ".csv"]:

                        # Download file content
                        fd_obj = wfd.webFileDownloader(url=r_url,
                                                       gcs_directory=os.path.join("{}/zipcsv_files".format(self.gcs_directory)))
                        dd_res = fd_obj.download_document()

                        # Add this to the dataframe of crawl results
                        if dd_res != -1:
                            resheadmsg = ("response_header_content_type: {}; size: {}")

                            all_sites_results.append(dict(seed_url=self.seed_url,
                                                          page_url=r_url,
                                                          site_name="",
                                                          page_title=os.path.basename(r_url),
                                                          html_code_string=resheadmsg.format(fd_obj.content_type,
                                                                                             fd_obj.total_file_size),
                                                          ptag_text="**file download**",
                                                          atag_urls="",
                                                          content_type="zip_file",
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          )
                                                     )
                            self.files_cnt += 1

                    ## Step 2.9: Crawl and pause
                    else:
                        self.crawl_cnt += 1
                        # print("Crawl No: {}; URl {}".format(crawl_cnt, r_url))
                        crawl = ws.webScraper()
                        crawl.visit_page(url=r_url)

                        # Pause
                        time.sleep(self.wait_time)

                        ## Step 2.10: Add these crawl results to the list of dictionaries; if data return
                        if len(crawl.result) > 0:

                            # Add to count of found crawl results
                            self.crawl_results_cnt += 1

                            ## Add these crawl results
                            all_sites_results.append(dict(seed_url=self.seed_url,
                                                          page_url=r_url,
                                                          site_name=crawl.result["site_name"],
                                                          page_title=crawl.result["page_title"],
                                                          html_code_string=crawl.result["html_code_string"],
                                                          ptag_text=crawl.result["ptag_text"],
                                                          atag_urls=crawl.result["atag_urls"],
                                                          content_type="web_page",
                                                          crawl_time=datetime.now().strftime(self.dtformat)
                                                          ))

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
            msg = ("Depth level finished: {}: {} URLs crawled; {} files downloaded; "
                   "{} URLs in to_crawl_urls; {} URLs in dont_crawl_urls").format(depth_cnt,
                                                                                  self.crawl_cnt,
                                                                                  self.files_cnt,
                                                                                  len(to_crawl_urls),
                                                                                  len(dont_crawl_urls))
            print(msg)
    
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
            print("dave directory")
            print("{}/webpages_pdfs".format(self.gcs_directory))

            # Save descriptions dataframe in a CSV file on GCP
            gct.write_pandas_as_csv_file_on_gcs(gcs_project_id=self.gcp_project_id,
                                                df=df,
                                                gcs_bucket_name=self.gcs_bucket_name,
                                                gcs_directory="{}/webpages_pdfs".format(self.gcs_directory),
                                                file_name=res_filename)

            # Save data in a CSV file
            # df.to_csv(path_or_buf=os.path.join(self.results_path, res_filename))

            ## Update User
            msg = ("Batch {} saved to disk").format(self.saved_batch_cnt)
            print(msg)


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

