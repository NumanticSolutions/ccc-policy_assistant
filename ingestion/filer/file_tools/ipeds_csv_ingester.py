# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for ingesting files from IPEDS (Integrated Postsecondary Education Data System)
# https://nces.ed.gov/ipeds

import os, sys
import pandas as pd
import numpy as np
import zipfile
import tempfile
from datetime import datetime

from google.cloud import storage

sys.path.append("../../interface/utils")
import gcp_tools as gct

class IpedsCsvIngester:
    '''
    Class to ingest files from the IPEDS database into a format that can be effectively incorporated into
    the CCC Policy Assistant Chatbot RAG process and that can be analyzed by a CSV agent. The goal is to let users ask
    natural language questions related to these datasets. For example, How many Community Colleges are in
    Los Angeles county? The CCC Policy Assistant should use the data found in the IPEDS database and perhaps from
    other sources to answer this question.

    Note that as of February 2025, there are 48 IPEDS data files that might contain data relevant to California
    community colleges. Each of these data files has an associated data dictionary file which contains among other
    elements a description of the data file's contents and long column names (as opposed to the shorthand column names
    employed in the data file). All files are stored are compressed into a ZIP format, but one unzipped the data files
    are CSV formatted and the data dictionary files are in Excel. Therefore, working with 96 files in different formats
    and preparing them to be used by an LLM is challenging.

    The logic in this class provide the following functionality:
        1. Create pairs of data and dictionary files
        2. Read and uncompress the Zip files so that the data and dictionary content can be put into Pandas DataFrames
        3. Find the data file overview and variable long names from the data dictionary
        4. Combine the overview and longname columns into single textual document describing the data and columns
        5. Filter the data files to only California community colleges
        6. Replace the shorthand column names with the long names
        7. Save the descriptive documents as text files and the filtered, renamed data as CSV files on Google Cloud


    Source:
    https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx?gotoReportId=7&fromIpeds=true&sid=c3d6e293-2cea-4a98-bca9-f1bd49f195df&rtid=7


    '''

    def __init__(self, **kwargs):
        '''
        Initialize the IPEDS data ingester

        '''

        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcs_bucket_name = "ccc-crawl_data"
        # self.input_data_path = ("/Users/stephengodfrey/OneDrive - numanticsolutions.com"
        #                         "/Engagements/Projects/ccc_policy_assistant/data/ipeds_files")
        self.input_data_path = "ipeds/zipcsv_files/"
        self.filer_config_path = "../data/filer_params"
        self.ccc_listing_filename = "ccc-hifld_oes_wiki_cccco-2501.csv"

        # Update any key word args
        self.__dict__.update(kwargs)

        # Set GCS class variables
        self.storage_client = storage.Client(project=self.gcp_project_id)
        self.gcs_bucket = self.storage_client.bucket(self.gcs_bucket_name)

        # Get a list of CCC
        self.read_ccc_listing()

        # Read the data
        self.read_data_files()

        # Create a descriptions dataframe
        self.create_descriptions_df()

        # Save the results to storage
        self.save_results()

    def read_ccc_listing(self):
        '''
        Method to read the list of CA community colleges
        '''

        # Read CCC college
        self.df_ccc = pd.read_csv(filepath_or_buffer=os.path.join(self.filer_config_path,
                                                                  self.ccc_listing_filename), encoding="cp1252")

        self.ccc_ids = self.df_ccc["IPEDSID"].unique().tolist()


    def read_data_files(self):
        '''
        Method to read and uncompress the Zip files into Pandas DataFrames
        '''

        ## Step 1: Get a list of files to read - list of tuples
        file_pairs = self.get_files_to_read(data_path=self.input_data_path)

        ## Step 2: For each file pair in list - read from the zip file
        ## this is a list of tuples in which each tuple element is a dictionary of datafrmaes
        self.df_tup_dicts = []
        for file_pair in file_pairs:

            # print(file_pair)

            ## Step 2.1:  Read the data file
            dict0 = self.read_zip_file(data_path=self.input_data_path,
                                       zip_file_name=file_pair[0])
            dict0_fn = list(dict0.keys())[0]

            ## Step 2.2:  Read the dictionary file
            dict1 = self.read_zip_file(data_path=self.input_data_path,
                                       zip_file_name=file_pair[1])
            dict1_fn = list(dict1.keys())[0]

            ## Step 2.3:  Get the document overview from the information table
            mask_intro = \
                dict1[dict1_fn]["Introduction"][dict1[dict1_fn]["Introduction"].columns[0]] == "Overview"

            if len(dict1[dict1_fn]["Introduction"][mask_intro]) == 1:
                idxi0 = dict1[dict1_fn]["Introduction"][mask_intro].index[0]
                doc_over = dict1[dict1_fn]["Introduction"].loc[idxi0, "Unnamed: 1"]

            ## Step 2.4: Get the long column names from the varlist
            # Look for var list
            for key in dict1[dict1_fn].keys():
                if key.lower().find("varlist") >= 0:
                    vl_key = key
            col_longnames = ", ".join(dict1[dict1_fn][vl_key]["varTitle"].tolist())

            ## Step 2.5: Create a descriptive document
            doc_descrs = ("CSV data file name: {}. \n"
                          "Overview description of file contents: {}. \n"
                          "Data columns: {}.").format(dict0_fn,
                                                      doc_over,
                                                      col_longnames)

            ## Step 2.6: Replace blank strings with Null values
            # Identify String Columns
            d0_str_cols = dict0[dict0_fn]["data"].select_dtypes(include=['object']).columns

            # Cells with only blanks replace with null
            ###############
            dict0[dict0_fn]["data"][d0_str_cols] = \
                dict0[dict0_fn]["data"][d0_str_cols].replace(to_replace=r"^\s+$",
                                                                value=np.nan,
                                                                regex=True)

            ## Step 2.7: Replace shorthand column names with long names
            column_map = {k: v for k, v in zip(dict1[dict1_fn][vl_key]["varname"],
                                               dict1[dict1_fn][vl_key]["varTitle"])}
            dict0[dict0_fn]["data"] = dict0[dict0_fn]["data"].rename(columns=column_map)

            ## Step 2.8: Remove columns that were not in the map and for which we don't have long names
            ln_cols = [c for c in column_map.values() if c in dict0[dict0_fn]["data"].columns]
            dict0[dict0_fn]["data"] = dict0[dict0_fn]["data"][ln_cols]

            ## Step 2.9: Create a filter data for only CA CC
            mask = dict0[dict0_fn]["data"][column_map["UNITID"]].isin(self.ccc_ids)

            ## Step 3.0: Add the list of tuples of dictionaries
            if len(dict0[dict0_fn]["data"][mask]) < 1:
                pass
                # print(file_pair)
            else:
                dict0[dict0_fn]["data"] = dict0[dict0_fn]["data"][mask]
                dict0[dict0_fn]["data"] = dict0[dict0_fn]["data"].reset_index(drop=True)

                ## Step 2.7: Add these to the list of tuples of dictionaries
                self.df_tup_dicts.append((dict0[dict0_fn], dict1[dict1_fn], doc_descrs))


    def get_zip_file_type(self, filename: str):
        '''
        Function to return file type either dat for data files
        or dict for dictionary files
        :param filename:
        :return: invalid, dict, dat
        '''

        root = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]

        if len(root) == 0 or len(ext) == 0 or ext != ".zip":
            return "invalid"

        elif root.lower().find("_dict") >= 0:
            return "dict"

        else:
            return "dat"


    def get_files_to_read(self, data_path):
        '''
        Functio to return a list of tuples providing the name of the
        data file and the associated dictionary file
        :param data_path: Path to the directory containing the data files
        :return: A list of tuples providing the names of files to be read
        '''

        # Get a list of the contents in input data path
        file_names = gct.gcp_list_bucket(gcp_project_id=self.gcp_project_id,
                                         gcs_bucket_name=self.gcs_bucket_name,
                                         path=self.input_data_path)
        # file_names = os.listdir(data_path)

        # Get a list of all dictionary files
        dict_files_roots = [os.path.splitext(f)[0] for f in file_names \
                            if self.get_zip_file_type(f) == "dict"]

        # Get a list of data files
        dat_files = [f for f in file_names if self.get_zip_file_type(f) == "dat"]

        # Create tuples of files to read - checking that the data file can be
        # found in the dictionary files
        read_files = [(f, "{}_Dict.zip".format(os.path.splitext(f)[0])) for f in dat_files \
                      if "{}_Dict".format(os.path.splitext(f)[0]) in dict_files_roots]

        return read_files


    def read_zip_file(self, data_path: str,
                      zip_file_name: str):
        '''
        Function to read in a zip file and return a dictionary with the name of the file as the key and
        the data in pandas dataframes also as a dictionary or None if the file can't be read
        no file found
        :param data_path:
        :param zip_file_name:
        :return: Dictionary of dataframes
        '''

        # Read the zip file
        zipbytes = gct.read_gcs_file(gcp_project_id=self.gcp_project_id,
                                     gcs_bucket_name=self.gcs_bucket_name,
                                     path="",
                                     filename=zip_file_name)
        # zf = zipfile.ZipFile(os.path.join(data_path, zip_file_name))

        # Check if zip file
        if zipfile.is_zipfile(zipbytes):
            with tempfile.TemporaryDirectory() as tempdir:

                # Extract files
                with zipfile.ZipFile(zipbytes, 'r') as zf:
                    zf.extractall(tempdir)

                # Get a list of files in this directory
                dir_contents = os.listdir(tempdir)

                # If one file - load into a csv and create a dictionary
                if len(dir_contents) == 1 and os.path.splitext(dir_contents[0])[1] == ".csv":
                    data = {dir_contents[0]:
                                {"data": pd.read_csv(filepath_or_buffer=os.path.join(tempdir, dir_contents[0]),
                                                     encoding="cp1252")}}

                # The dictionary files are in Excel and are returned as a dictionary
                # since they have multiple sheets
                elif len(dir_contents) == 1 and os.path.splitext(dir_contents[0])[1] == ".xlsx":
                    data = {dir_contents[0]:
                        pd.read_excel(io=os.path.join(tempdir, dir_contents[0]),
                                       sheet_name=None)}

                # Present a message to the user and return None
                else:
                    # if len(dir_contents) == 0:
                    #     msg = "No files found"
                    # elif len(dir_contents) == 1 and os.path.splitext(dir_contents[0])[1] != ".csv":
                    #     msg = "One file found but not of type '.csv'"
                    # else:
                    #     msg = "{} files found which can not be loaded into a single dataframe with this logic"

                    return None

            return data

        else:
            return None

    def create_descriptions_df(self):
        '''
        Method to create a datframe containing csv file descriptions
        '''

        # Create a dataframe descriptive files
        drows = []
        for ftpl in self.df_tup_dicts:
            drows.append(dict(file_name=ftpl[2][20: ftpl[2].find(".csv") + 4],
                              file_type="csv",
                              num_cols=len(ftpl[0]["data"].columns),
                              cols=",".join(ftpl[0]["data"].columns.tolist()),
                              description=ftpl[2]))

        self.df_descs = pd.DataFrame(data=drows)

    def save_results(self):
        '''
        Function to save results (modified CSV files and descriptions) to storage
        '''

        # Preparation date
        cd_dtformat = "%Y%b%d"
        prep_dt = datetime.now().strftime(cd_dtformat)

        # Save each cleaned csv data file
        for ftpl in self.df_tup_dicts:

            # Set a file
            res_filename = "prep_{}_{}".format(prep_dt,
                                                 ftpl[2][20: ftpl[2].find(".csv") + 4])

            # Save data in a CSV file
            blob = self.gcs_bucket.blob(os.path.join("{}prep".format(self.input_data_path), res_filename))
            blob.upload_from_string(ftpl[0]["data"].to_csv(), 'text/csv')

        # Save the descriptions data frame
        desc_filename = "descriptions_{}.csv".format(prep_dt)

        # Save data in a CSV file
        blob = self.gcs_bucket.blob(os.path.join("{}prep".format(self.input_data_path), desc_filename))
        blob.upload_from_string(self.df_descs.to_csv(), 'text/csv')

