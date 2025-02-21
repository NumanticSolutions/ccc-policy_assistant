# © 2025 Numantic Solutions LLC
# MIT License
#

import os, sys, io
import pathlib

import pandas as pd


# from uuid import uuid4

# import langchain
# from jupyterlab.handlers.build_handler import build_path
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain.document_loaders import TextLoader
from langchain_google_community import GCSFileLoader

from langchain.document_loaders import PyPDFLoader
# from langchain.prompts import PromptTemplate
# from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
import vertexai

import chromadb

# from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from google.cloud import storage

# sys.path.insert(0, "../../embedder")
# import chunk_text_3 as ct
# import url_exclusion_list as uel

sys.path.append("../../interface/utils")
import gcp_tools as gct
# import authentication as auth

class EmbedDocuments:

    """Create a named database and embed chunks and corresponding metedata.

    The class constructor creates a new persistent ChromaDB database at a given
    path location and with a given collection name. If a database and collection
    already exist the constructor will fail.

    The 'embed()' method will use a specified model to vector embed chunks and
    corresponding metadatas. The 'meta_key' can be used to specify the key name
    and 'is_verbose' can toggle printing information during embedder. This method
    does not return anything.

    ():
        full_path (str)       : Full path specifying where the database is to be created.
        collection_name (str) : Name of the collection to be created in the database.

    embed():
        chunks [strs]     : The text chunks to be vector embedded in the database
        metas [strs]      : The metadata for each of the chunks to be embedded
        model (str)       : Embedding model to use, such as 'mxbai-embed-large'
        meta_key (str)    : Key to use for the metadats, such as 'url'
        is_verbose (bool) : Print updates during embedder

    """

    def __init__(self,
                 **kwargs):

        # Set project and location
        self.gcs_project_id = "eternal-bongo-435614-b9"
        self.gcs_project_name = "AnalyticsP1"
        self.gcs_location = "us-central1"

        # Get credentials
        # creds = auth.ApiAuthentication(cred_source="dotenv")
        # os.environ["GOOGLE_API_KEY"] = creds.apis_configs["GOOGLE_API_KEY"]

        # Set models
        # self.embedding_model = "textembedding-gecko@003"
        self.embedding_model = "text-embedding-004"
        self.embedding_num_batch = 5

        # Assign class values based on inputs
        self.chroma_collection_name = "crawl_docs1"
        self.gcs_input_bucket_name = "ccc-crawl_data"
        self.gcs_embed_bucket_name = "ccc-chromadb-vai"
        self.embeddings_path = ("/Users/stephengodfrey/OneDrive - numanticsolutions.com"
                                "/Engagements/Projects/ccc_policy_assistant/data/crawls/")

        # Sources to embed
        self.sources_to_embed = ["aacc", "cccaoe", "cccco", "ccleague", "columbia",
                                 "ecs", "lao", "nsc", "wikipedia", "ipeds"]

        # self.sources_to_embed = ["ipeds"]

        # Sources that have csv files for the csv agent
        self.csv_files_sources = ["ipeds"]

        # File column mapping - mapping from the files description file to the webcrawl text
        # There should be a map value for each input column
        self.csv_desc_col_map = {"seed_url": "seed_url",
                                 "page_url": "page_url",
                                 "ptag_text": "description",
                                 "input_type": "file_name"}

        # Text column
        self.url_col = "page_url"
        self.text_col = "ptag_text"
        self.input_source_col = "input_type"
        self.input_df_cols = ["seed_url", "page_url", "ptag_text", self.input_source_col]
        self.metadata_cols = ["seed_url", "page_url", self.input_source_col]
        self.chunk_size = 500
        self.chunk_overlap = 10
        self.minimum_text_length = 10

        # Folder on GCS
        self.gcs_folder = ""

        # Update any keyword args
        self.__dict__.update(kwargs)

        # Set GCS class variables
        self.storage_client = storage.Client(project=self.gcs_project_id)
        self.input_bucket = self.storage_client.bucket(self.gcs_input_bucket_name)


        # Initialize VertexAI
        vertexai.init(project=self.gcs_project_id, location=self.gcs_location)

        # Set up embeddings model
        self.embeddings = VertexAIEmbeddings(model_name=self.embedding_model)

        # Set up text chunker
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size,
                                                            chunk_overlap=self.chunk_overlap,
                                                            length_function=len,
                                                            is_separator_regex=False
                                                            )

        # Documents after splitting
        self.docs = []

        # Set up Chroma
        self.client = chromadb.PersistentClient(path=self.embeddings_path)

        # Create a new collection
        self.collection = self.client.get_or_create_collection(name=self.chroma_collection_name)

        # Create an embeddings model
        self.embeddings_model_obj = VertexAIEmbeddings(model=self.embedding_model)

        # Create a vector store
        self.vector_store = Chroma(client=self.client,
                                   collection_name=self.chroma_collection_name,
                                   embedding_function=self.embeddings_model_obj
                                   )


    def get_input_filenames(self):
        '''
        Method to collect the filenames in the input_webcrawl_data_path - allowing for embedder multiple
        documents in a single run.
        :return:
        '''

        # Get a list of csv files from the webcrawl directory
        # self.webcrawl_input_files = [f for f in os.listdir(self.input_webcrawl_data_path) if f.endswith(".csv")]

        # Get a list of the tables to text data from the tables_to_text direcory
        # self.tablestotext_input_files = [f for f in os.listdir(self.input_tabletotext_data_path) if f.endswith(".txt")]

        # bucket = storage.Client().get_bucket(bucket_name)
        input_files_rows = []
        for blob in self.input_bucket.list_blobs():
            bpath = pathlib.Path(blob.name)
            bps = bpath.parts
            if bps[0] in self.sources_to_embed and blob.name.endswith(".csv") == True and \
                os.path.split(blob.name)[1][:5] != "prep_":

                input_files_rows.append(dict(source=bps[0],
                                             input_type=bps[1],
                                             filename=bps[2],
                                             path=blob.name))

        self.input_files = pd.DataFrame(data=input_files_rows)

    def read_crawl_data(self):
        '''
        Method to read raw text csv files data into a dataframe.
        :return:
        '''

        # # Create a storage client
        # storage_client = storage.Client(project=gcp_project_id)
        #
        # # Get the bucket
        # bucket = storage_client.bucket(gcs_input_bucket_name)
        #
        # # Get the blob
        # blob = bucket.blob(os.path.join(crawl_data_path, crawl_file))
        #
        # # Works
        # data = blob.download_as_bytes()
        # dft = pd.read_csv(io.BytesIO(data))

        ##### Step 1 - read webcrawl files
        # For each source, read all the text files
        input_sources = self.input_files["source"].unique().tolist()

        for input_source in input_sources:

            # Create a mask for this source
            mask = (self.input_files["source"] == input_source)

            if len(self.input_files[mask]) > 0:

                # List to hold dataframes with text content to be embedded
                dfs = []

                # Get the first entry
                idx0 = self.input_files[mask].index[0]


                # If this is a file input source, special handling is required
                if input_source in self.csv_files_sources:

                    # Get the file descriptions into the input text column
                    dfs.append(self.concat_filesource_data(file_source=input_source))
                    self.df_fc = self.concat_filesource_data(file_source=input_source)

                # Otherwise load data from all files from this source
                else:

                    for idx in self.input_files[mask].index:

                        # Walk through GCS directory to geta list of input files
                        blob = self.input_bucket.blob(self.input_files.loc[idx, "path"])
                        data = blob.download_as_bytes()
                        dft = pd.read_csv(io.BytesIO(data))

                        # Add to list of datafranes
                        dfs.append(dft)

                # Create a single dataframe for this input source
                if len(dfs) > 0:
                    src_df = pd.concat(objs=dfs)

                    # Ensure text column is string
                    src_df[self.text_col] = src_df[self.text_col].astype(str)

                    # Drop any rows with null in text column
                    src_df = src_df.dropna(subset=[self.text_col])

                    # Drop rows with identical text to others
                    src_df = src_df.drop_duplicates(subset=[self.text_col])
                    src_df = src_df.reset_index(drop=True)

                    # Add a column for source
                    if self.input_source_col not in src_df.columns:
                        src_df[self.input_source_col] = self.input_files.loc[idx0, self.input_source_col]

                    # Reduce columns
                    src_df = src_df[self.input_df_cols]

                    # Chunk texts and add to docs
                    for idx in src_df.index:

                        texts = self.text_splitter.create_documents([src_df.loc[idx, self.text_col]])

                        # Add metadata
                        for text in texts:
                            text.metadata = {col: src_df.loc[idx, col] for col in self.metadata_cols}
                            text.metadata["source"] = self.input_files.loc[idx0, "source"]

                        self.docs.extend(texts)


        # #### Step 2: Read tables to text
        # tc_rows = []
        # for filename in self.tablestotext_input_files:
        #
        #     # Open the file
        #     with open(os.path.join(self.input_tabletotext_data_path, filename), "r") as file:
        #         data = file.read()
        #
        #     # Split this into a list of text chunks
        #     texts_chunks = data.split("\n\n")
        #
        #     # Add to a list of dictionaries
        #     input_source = "tables_to_text"
        #     url = "hifld_oes_wiki_ccccc"
        #     tc_rows = []
        #     for tc in texts_chunks:
        #
        #         # Split again into sentences
        #         tc_sentences = tc.split(". ")
        #         for tc_sentence in tc_sentences:
        #             entry_dict = {}
        #
        #             entry_dict[self.url_col] = url
        #             entry_dict[self.text_col] = tc_sentence
        #             # entry_dict[self.text_col] = tc
        #
        #             entry_dict[self.input_source_col] = input_source
        #
        #             tc_rows.append(entry_dict)
        #
        # df_tc = pd.DataFrame(data=tc_rows)
        #
        # # Combine the dataframes
        # self.input_df = pd.concat(objs=[self.input_df, df_tc], ignore_index=True)
        #
        # # Drop any rows with less than minimum characters
        # mask = self.input_df["ptag_text"].str.len() > self.minimum_text_length
        # self.input_df = self.input_df[mask]
        #
        # # Reset index
        # self.input_df = self.input_df.reset_index(drop=True)

        #####
        # We might want to reduce some redundant text by checking similarity of input texts
        # Need to figure out how to handle additional documents - do we add to the same collection?

    def read_pdf_data(self):
        '''
        Method to read PDF data found in the GCS input buckets
        '''

        def load_pdf(file_path):
            return PyPDFLoader(file_path)

        input_sources = self.input_files["source"].unique().tolist()

        for input_source in input_sources:

            # Create a mask for this source
            mask = (self.input_files["source"] == input_source) & \
                   (self.input_files["input_type"] == "files")

            if len(self.input_files[mask]) > 0:
                idx0 = self.input_files[mask].index[0]

                pdf_docs = []
                for idx in self.input_files[mask].index:

                    if self.input_files.loc[idx,"path"].endswith('.pdf'):

                        try:
                            loader = GCSFileLoader(project_name=self.gcs_project_name,
                                                   bucket=self.input_bucket,
                                                   blob=self.input_files.loc[idx, "path"],
                                                   loader_func=load_pdf
                            )

                            pdf_docs.extend(loader.load())

                        except:
                            pass

                # Chunk PDF
                self.pdf_docs = pdf_docs
                # texts = self.text_splitter.create_documents(pdf_docs)
                #
                # # Add metadata
                # for text in texts:
                #     text.metadata = {"source": self.input_files.loc[idx0, "source"] }
                #
                # self.docs.extend(texts)

    # def chunk_input_text(self, df):
    #     '''
    #     Method to chunk the input text data into chunks.
    #
    #     :return:
    #     '''
    #
    #     # chunker = ct.ChunkText()
    #     # self.chunks = chunker.chunk_dataframe(df=self.input_df)
    #
    #     # Chunk texts
    #     for idx in df.index:
    #
    #         texts = self.text_splitter.create_documents([df.loc[idx, self.text_col]])
    #
    #         # Add metadata
    #         for text in texts:
    #             text.metadata = {col: df.loc[idx, col] for col in self.metadata_cols}
    #
    #         self.docs.extend(texts)



    def embed(self, meta_key="url",is_verbose=False):
        '''
        Create the embeddings

        '''

        # Check if collection name exists -
        #### Need to add more functionality on how to handle this case
        for c in self.client.list_collections():
            if c.name == self.collection_name:
                print("collection {} already exists; It will be overwritten".format(c.name))
                self.client.delete_collection(name=c.name)

        # Add documents to the vector sore
        self.vector_store.add_documents(documents=self.docs)

        # Add IDs to all documents
        for id, doc in zip(range(len(self.docs)), self.docs):
            doc.metadata["id"] = id + 1


    def copy_embeddings_to_gcs(self):
        '''
        Method to copy embeddings from a local store to GCS.
        :return:
        '''

        gct.upload_directory_to_gcs(local_directory=self.embeddings_path,
                                    gcs_project_id=self.gcs_project_id,
                                    gcs_input_bucket_name=self.gcs_input_bucket_name,
                                    gcs_directory=self.gcs_folder)


    def concat_filesource_data(self, file_source):
        '''
        Function to prepare CSV files descriptions by concatenating the crawl history and
        descriptions data into a single dataframe.

        '''

        # Create a mask for these dataframes
        mask = (self.input_files["source"] == file_source)

        if len(self.input_files[mask]) == 2:

            dfs = []
            for idx in self.input_files[mask].index:
                # Walk through GCS directory to geta list of input files
                blob = self.input_bucket.blob(self.input_files.loc[idx, "path"])
                data = blob.download_as_bytes()
                dfs.append(pd.read_csv(io.BytesIO(data)))


            for df in dfs:

                # Find the dataframe that doesn't have the self.text_col (ptag_text) column
                # since we're going to add it
                if self.text_col not in df.columns:
                    dft1 = df
                else:
                    dft2 = df

            # Add these columns to dft1 (the one without self.text_col column
            for col in self.input_df_cols:
                dft1[col] = ""

            for idx in dft1.index:

                # Get the base file name and look for it in the descriptions
                filenamebase = os.path.splitext(dft1.loc[idx, "file_name"])[0]
                mask = dft2["page_title"].str.lower().str.find("{}.".format(filenamebase)) == 0

                # Get these values from the other dataframe
                if len(dft2[mask]) == 1:
                    idx20 = dft2[mask].index[0]

                    for col_key in self.csv_desc_col_map.keys():
                        # Try to find the column in dft2; if not look in dft1
                        try:
                            dft1.loc[idx, col_key] = dft2.loc[idx20, self.csv_desc_col_map[col_key]]
                        except:
                            dft1.loc[idx, col_key] = dft1.loc[idx, self.csv_desc_col_map[col_key]]

            return dft1[self.input_df_cols]

        else:
            return None

