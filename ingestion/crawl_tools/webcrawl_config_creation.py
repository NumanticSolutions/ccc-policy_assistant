# © 2025 Numantic Solutions LLC
# MIT License
#
# Create a CSV file with web crawl configurations

import os, json
import pandas as pd
import urllib


class CCCWebCrawlConfigCreator:
    '''
    Class object to create a web-crawl configuration file. This configuration file contains
    the parameters necessary to crawl each site providing data to the CCC Policy assistant. The
    class attribute containing configuraton data is df_cp - a Pandas dataframe.

    '''

    def __init__(self, **kwargs):
        '''
        Initialize the object
        '''

        # Configuration files path
        self.input_data_path = "data/crawler_params"

        # Files with seed URls

        # Aggregation sites
        self.agg_seeds_file = "aggregator_seeds_parameters.json"

        # Individual school sites
        self.school_seeds_file = "school_seeds.json"

        # School board docs sites
        self.board_seeds_file = "board_seeds.json"

        # Depth and width of school site crawls
        self.school_seed_crawl_depth = 5
        self.school_seed_crawl_width = 10

        # Depth and width of school site crawls
        self.board_seed_crawl_depth = 5
        self.board_seed_crawl_width = 10

        # Output parameters
        self.cp_output_filename = "crawl_configuraton.csv"
        self.cp_output_path = "../data/crawler_params"
        self.save_out_to_file = False

        # Update any key word args
        self.__dict__.update(kwargs)

        # Create crawl configuration

        ### Step 1: Read seed URls
        self.read_seed_urls()

        ### Step 2: Read seed URls
        self.add_in_exclusions()

        ### Step 3: Add school seeds
        self.add_school_seeds()

        ### Step 4: Add board URls
        self.add_board_seeds()

        ### Step 5. Create dataframe and save it
        self.create_dataframe()

    def read_seed_urls(self):
        '''
        Method to read seed URLs
        '''

        # Read aggregator sites - which also have other parameters
        with open(os.path.join(self.input_data_path, self.agg_seeds_file), "r") as file:
            self.cpdat = json.load(file)

        # Read individual school site seeds
        with open(os.path.join(self.input_data_path, self.school_seeds_file), "r") as file:
            self.school_seeds = json.load(file)

        # Read individual school site seeds
        with open(os.path.join(self.input_data_path, self.board_seeds_file), "r") as file:
            self.board_seeds = json.load(file)

    def add_in_exclusions(self):
        '''
        Method to add to the crawl configuration data inclusion and exclusion sites which are specific URLs
        associated with each seed URL that designated to be included with the crawl (inclusion) or excluded
        from the crawl (exclusion)

        '''

        # Step 1: Use the file names to create a dictionary of inclusions and exclusions
        sources_list = []
        url_exin_config = {}
        for file_name in os.listdir(self.input_data_path):
            if file_name.find("inclusions") >= 0 or file_name.find("exclusions") >= 0:
                sources_list.append(file_name[:file_name.find("_")])

        for source in sources_list:
            url_exin_config[source] = {"inclusions": {"filename": "",
                                                      "url_list": ""},
                                       "exclusions": {"filename": "",
                                                      "url_list": ""}
                                       }

        for file_name in os.listdir(self.input_data_path):
            for ftype in ["inclusions", "exclusions"]:
                if file_name.find(ftype) >= 0:
                    source = file_name[:file_name.find("_")]
                    url_exin_config[source][ftype]["filename"] = file_name

        # Step 2: Load URL lists
        for source in url_exin_config.keys():

            for ftype in ["inclusions", "exclusions"]:

                if len(url_exin_config[source][ftype]["filename"]) > 0:
                    with open(os.path.join(self.input_data_path,
                                           url_exin_config[source][ftype]["filename"]), "r") as file:
                        url_list = json.load(file)

                    url_exin_config[source][ftype]["urls"] = url_list["urls"]

        # Step 3: Add crawl counts
        for crawl_param in self.cpdat:
            source = crawl_param["storage_folder"]
            if source in url_exin_config.keys():
                if "urls" in url_exin_config[source]["inclusions"].keys():
                    crawl_param["crawl_urls"] = ";".join(url_exin_config[source]["inclusions"]["urls"])
                    crawl_param["crawl_width"] = len(url_exin_config[source]["inclusions"]["urls"]) + 1
                if "urls" in url_exin_config[source]["exclusions"].keys():
                    crawl_param["dont_crawl_urls"] = ";".join(url_exin_config[source]["exclusions"]["urls"])

    def add_school_seeds(self):
        '''
        Method to add school seeds to the configuration data
        '''

        for url in self.school_seeds["urls"]:
            self.cpdat.append({"seed_url": url,
                               "storage_folder": self.get_school_folder_name(url),
                               "organization": "",
                               "about": "",
                               "crawl_urls": "",
                               "dont_crawl_urls": "",
                               "crawl_depth": self.school_seed_crawl_depth,
                               "crawl_width": self.school_seed_crawl_width
                               }
                              )

    def add_board_seeds(self):
        '''
        Method to add board seeds to the configuration data
        '''

        for url in self.board_seeds["urls"]:
            self.cpdat.append({"seed_url": url,
                               "storage_folder": self.get_seed_storage_folder(url),
                               "organization": "",
                               "about": "",
                               "crawl_urls": "",
                               "dont_crawl_urls": "",
                               "crawl_depth": self.board_seed_crawl_depth,
                               "crawl_width": self.board_seed_crawl_width
                               }
                              )

    def create_dataframe(self):
        '''
        Method to create a dataframe from the configuration data
        '''

        # Create a dataframe
        self.df_cp = pd.DataFrame(data=self.cpdat)

        # Save it to the crawl configuration path
        if self.save_out_to_file:
            self.df_cp.to_csv(os.path.join(self.cp_output_path, self.cp_output_filenamecp_filename),
                              index=False)

    def get_school_folder_name(self, url):
        '''
        Method to extract the storage folder name from a seed URL
        '''

        parsed_url = urllib.parse.urlparse(url)
        nt_tokens = parsed_url.netloc.split(".")

        if parsed_url.netloc == "www.westhillscollege.com":
            nlpath = parsed_url.path.replace("/", "")
            return "{}_col".format(nlpath.lower())

        elif len(nt_tokens) <= 2 or nt_tokens[1] == "yccd":
            return "{}_col".format(nt_tokens[0].lower())
        else:
            return "{}_col".format(nt_tokens[1].lower())

    def get_seed_storage_folder(self, url):
        '''
        Method to extract the storage folder name from a seed URL
        '''

        if url.find("go.boarddocs.com") >= 0:

            url = url.replace("https://go.boarddocs.com/ca/", "")
            end = url.find("/")
            return "{}_brd".format(url[:end].lower())

        else:

            parsed_url = urllib.parse.urlparse(url)
            nt_tokens = parsed_url.netloc.split(".")

            if len(nt_tokens) <= 2:
                return "{}_brd".format(nt_tokens[0].lower())
            else:
                return "{}_brd".format(nt_tokens[1].lower())


