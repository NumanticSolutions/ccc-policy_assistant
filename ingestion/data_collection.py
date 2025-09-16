# © 2025 Numantic Solutions LLC
# MIT License
#
# Configure and run a crawl job

import os, sys
# import pandas as pd
from datetime import datetime
from tqdm import tqdm
import asyncio

# Numantic utilities
utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
from utilities.logging.logging_utils import LoggingUtils

# Tools for crawling
sys.path.insert(0, "crawl_tools/")
from webcrawl_config_creation import CCCWebCrawlConfigCreator
import web_scraper as ws
import webfile_downloader as wfd
import web_crawler as wc


if __name__ == "__main__":

    ### Step 1: Initialize and start the logger
    log_modes = ["screen", "file", "gcp"]
    logging_utils = LoggingUtils(log_modes=log_modes,
                                 logs_file_path="data/logs")

    # Start logger
    date_format = "%Y%m%d"
    logfile_name = "{}_{}.log".format("crawl_log",
                                      datetime.now().strftime(date_format))
    logger = logging_utils.create_logger(logfile_name=logfile_name)

    ### Step 1: Create a crawling configuration file
    evt_msg = "creating crawling configuration file"
    logging_utils.log_event(logger=logger,
                            log_entry=dict(file=os.path.basename(__file__),  # Examples of possible logged values
                                           event=evt_msg
                                           )
                            )
    crwl_cnfg = CCCWebCrawlConfigCreator()
    evt_msg = "crawl configuration file successfully created: {} rows".format(len(crwl_cnfg.df_cp))
    logging_utils.log_event(logger=logger,
                            log_entry=dict(file=os.path.basename(__file__),  # Examples of possible logged values
                                           event=evt_msg
                                           )
                            )

    ### Step 2: Create a crawling configuration file
    crawl_sources = ["numantic"]
    mask = crwl_cnfg.df_cp["storage_folder"].isin(crawl_sources)

    # Close the logger
    logging_utils.close_logger()

    async def main():

        for idx in tqdm(crwl_cnfg.df_cp[mask].index):

            # evt_msg = "crawling source: {}".format(crwl_cnfg.df_cp.loc[idx, "storage_folder"])
            # logging_utils.log_event(logger=logger,
            #                         log_entry=dict(file=os.path.basename(__file__),
            #                                        # Examples of possible logged values
            #                                        event=evt_msg
            #                                        )
            #                         )

            # self.bq_table_name = ""
            # self.bq_if_exists = ""

            # seed_url: str,
            # source_index: str,
            # save_location: str,
            # log_crawls: bool = True,

            # crawler = wc.webCrawler(seed_url=crwl_cnfg.df_cp.loc[idx, "seed_url"],
            #                         source_index=crwl_cnfg.df_cp.loc[idx, "storage_folder"],
            #                         gcp_project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            #                         log_crawls=True,
            #                         gcs_directory="crawl_data/{}".format(crwl_cnfg.df_cp.loc[idx, "storage_folder"]),
            #                         logfile_name=logfile_name)
            crawler = wc.webCrawler(seed_url=crwl_cnfg.df_cp.loc[idx, "seed_url"],
                                    source_index=crwl_cnfg.df_cp.loc[idx, "storage_folder"],
                                    log_crawls=True,
                                    save_location="bq",
                                    gcp_project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
                                    bq_dataset_id="ccc_polasst",
                                    bq_table_name="crawl_text",
                                    bq_if_exists="append",
                                    logfile_name=logfile_name)
            crlres = await crawler.crawl_sites(dont_crawl_urls=crwl_cnfg.df_cp.loc[idx, "dont_crawl_urls"].split(";"),
                                               crawl_urls=crwl_cnfg.df_cp.loc[idx, "crawl_urls"].split(";"),
                                               depth=crwl_cnfg.df_cp.loc[idx, "crawl_depth"],
                                               width=crwl_cnfg.df_cp.loc[idx, "crawl_width"])

    # Run the main function
    asyncio.run(main())


