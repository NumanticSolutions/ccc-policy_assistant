# © 2025 Numantic Solutions LLC
# MIT License
#

import sys, os, io

from google.cloud import storage
import pandas as pd

from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langchain_core.messages import SystemMessage
# from langgraph.prebuilt import ToolNode
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings, ChatVertexAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import List, TypedDict
# from langchain import hub
import vertexai
from langchain.tools.base import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
from langchain_experimental.tools import PythonAstREPLTool

from langchain_core.messages import HumanMessage, AIMessage

########## Change for rag testing
sys.path.insert(0, "utils")
sys.path.insert(0, "../../interface/utils")
from gcp_tools import download_directory_from_gcs
from authentication import ApiAuthentication

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


class CCCPolicyAssistant:
    '''
    The CCCPolicyAssistant class provides full functionality for a large language model
    chatbot covering policy issues related to California community colleges. It is an
    experimental tool created by the Numantic Solutions team that is designed to
    demonstrate how such tools can be used to provide a public service.
    More information can be found at Numanticsolutions.com.

    The primary building blocks are LangGraph (www.langchain.com/langgraph) components
    wrapping Google Gemini (deepmind.google/technologies/gemini/) AI models. This tool
    employs a Retrieval Augmented Generation (RAG) pipeline to respond to user queries.
    The RAG tools pull curated information about California community colleges which
    has been gathered primarily from web crawling and embedding (in an upstream
    process).

    The source information for this chatbot is stored on Google Cloud Storage.

    There are two main tools supporting the LLM:

    - retrieve - for searching a Chroma vector database with web page and PDF text
    - query_data - for querying Pandas dataframes

    The RAG workflow responds to user requests by
        1. Conducting a vector search for similar chunked documents
        2. Feeding these documents into the LLM prompt (unless a CSV is found as noted in 3)
        3. Running a Pandas agent if any of the vector searches point to variables in a
           curated CSV files
        4. Providing results to the user

    '''

    def __init__(self, **kwargs):
        self.version = "25.02.27"
        self.dot_env_path = "../data/environment"

        self.transcript_name_base = "cccbot_transcript"
        self.transcript_path = "./local_transcripts/"
        self.transcript_gcs_bucket = "cccbot-transcripts"
        self.transcript_gcs_directory = ""
        self.chroma_collection_name = "crawl_docs1"

        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcp_location = "us-central1"
        self.gcs_embeddings_bucket_name = "ccc-chromadb-vai-2"
        self.gcs_embeddings_directory = ""

        self.gcs_csv_file_bucket_name = "ccc-crawl_data"
        self.gcs_csv_file_directory = "{}/zipcsv_files/prep"

        self.embedding_model = "text-embedding-004"
        self.embedding_num_batch = 5
        self.embeddings_local_path = "data/local_chromadb/"

        # self.llm_model = "gemini-1.5-pro"
        self.llm_model = "gemini-2.0-flash"
        self.llm_model_max_output_tokens = 8192
        self.llm_model_temperature = 0.2
        self.llm_model_top_p = 0.8
        self.llm_model_top_k = 40
        self.llm_model_verbose = True

        self.retriever_search_type = "similarity"
        self.retriever_search_kwargs = {"k": 3}

        self.default_question = "What shall we discuss?"
        self.prompt_template = ("You are a California Community College AI assistant. "
                                "Use the following pieces of context and your knowledge base "
                                "If the context does not contain the answer use your "
                                "training to answer. Your response should be between 5 and 10 sentences. "
                                )
        self.chat_hist_memory_key = "chat_history"
        self.chat_hist_return_messages = True
        self.chat_hist_output_key = "answer"

        self.conv_chain_chain_type = "stuff"
        self.conv_chain_chain_type_verbose = True
        self.conv_chain_chain_type_return_source_documents = True
        self.chat_bot_verbose = True

        self.doc_search_retrieval_k = 4

        # Update any keyword args
        self.__dict__.update(kwargs)

        # Get creds if needed
        if len(self.dot_env_path) > 0:
            creds = ApiAuthentication(dotenv_path=self.dot_env_path)

            # LangSmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = creds.apis_configs["LANGCHAIN_API_KEY"]
            # Google
            os.environ["GOOGLE_API_KEY"] = creds.apis_configs["GOOGLE_API_KEY"]

        ### Step 2: Initialize Vertex AI
        vertexai.init(project=self.gcp_project_id,
                      location=self.gcp_location)

        ### Step 3. Instantiate an LLM
        self.llm = ChatVertexAI(model=self.llm_model,
                                temperature=self.llm_model_temperature,
                                max_output_tokens=self.llm_model_max_output_tokens,
                                top_k=self.llm_model_top_k,
                                top_p=self.llm_model_top_p)

        ### Step 4. Establish an embeddings model
        self.embeddings = VertexAIEmbeddings(model=self.embedding_model)

        ### Step 5: Establish vector store
        self.vector_store = self.setup_vectorstore()

        ### Step 6: Set up conversational graph
        self.graph = self.setup_conversation_graph()

    def setup_vectorstore(self):
        '''
        Function to set up vector store. This returns a vector store that
        can be set in the Streamlit session eliminating the automatic
        refresh that would happen with each new question

        '''

        # Download files from GCP
        download_directory_from_gcs(gcs_project_id=self.gcp_project_id,
                                    gcs_bucket_name=self.gcs_embeddings_bucket_name,
                                    gcs_directory=self.gcs_embeddings_directory,
                                    local_directory=self.embeddings_local_path)

        # # Load embeddings and persisted data
        # embeddings = VertexAIEmbeddings(model_name=self.embedding_model)

        # Load Chroma data from local persisted directory
        db = Chroma(persist_directory=self.embeddings_local_path,
                    collection_name=self.chroma_collection_name,
                    embedding_function=self.embeddings)

        return db

    # @tool(response_format="content_and_artifact")
    def retrieve(self, query: str):
        """Retrieve information related to a query."""

        self.retrieved_docs = self.vector_store.similarity_search(query,
                                                                  k=self.doc_search_retrieval_k)

        # Get all documents from these web pages
        self.extended_retrieved_docs = []
        for doc in self.retrieved_docs:

            # Get all documents from this source
            self.extended_retrieved_docs.append(self.vector_store.get(where={"page_url": {"$eq": doc.metadata["page_url"]}}))

        # Get the full texts of the extended retrieved  docs
        self.ext_docs_texts = [" ".join(doc["documents"]) for doc in self.extended_retrieved_docs]

        # Get a list of CSV files returned by the doc search (if any)
        # This returns a list of tuples with this format (source, file_name)
        self.retrieved_csv_files = []
        self.query_data_result = "" # O Overwrite this if do a CSV query
        for doc in self.retrieved_docs:
            if doc.metadata["input_type"].endswith(".csv"):
                self.retrieved_csv_files.append(dict(source=doc.metadata["source"],
                                                     input_type=doc.metadata["input_type"],
                                                     seed_url=doc.metadata["seed_url"]))

        # create a serialized version of retrieved docs
        self.serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in self.retrieved_docs
        )

        return self.serialized, self.retrieved_docs

    def query_data(self, state: MessagesState):
        '''
        Use Pandas to query CSV data loaded into a dataframe

        '''

        # Read the CSV file
        if len(self.retrieved_csv_files) > 0:
            idx0 = 0

            #############
            # We should update to the read_csv_file_into_pandas function in GCP tools
            df = self.read_csv_file(file_source=self.retrieved_csv_files[idx0]["source"],
                                    file_name=self.retrieved_csv_files[idx0]["input_type"])

            # Create a pandas agent
            prefix = ("This dataframe only contains information on California "
                      "community colleges and no other schools. If the user asks "
                      "about california community colleges or schools use all rows in the "
                      "dataframe. ")
            agent_executor = create_pandas_dataframe_agent(self.llm,
                                                           df=df,
                                                           agent_type="tool-calling",
                                                           prefix=prefix,
                                                           verbose=self.chat_bot_verbose,
                                                           allow_dangerous_code=True)

            msg = [m for m in state["messages"] if m.type == "human"]

            response = agent_executor.invoke(msg)

            src_des = ("The data used by policy assistant to answer this question can be found at {} "
                       "in the {} file. You may want to visit that site to validate this result "
                       "and continue your research. "
                       "This tool and this feature are still under development and mistakes can be made. "
                       "Please validate all results. ").format(self.retrieved_csv_files[idx0]["seed_url"],
                                                               self.retrieved_csv_files[idx0]["input_type"])

            self.query_data_result = "{} {}".format(response["output"], src_des)

            return {"messages": [AIMessage(self.query_data_result)]}

        else:
            return None


    # Step 1: Generate an AIMessage that may include a tool-call to be sent.
    def query_or_respond(self, state: MessagesState):
        """Generate tool call for retrieval or respond."""

        # llm_with_tools = self.llm.bind_tools([self.retrieve,
        #                                       self.query_data])
        llm_with_tools = self.llm.bind_tools([self.retrieve])
        response = llm_with_tools.invoke(state["messages"])

        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}


    # Step 3: Generate a response using the retrieved content.
    def generate(self, state: MessagesState):
        """Generate answer."""

        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (f"{self.prompt_template}"
                                  "\n\n"
                                  f"{docs_content}")

        self.conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + self.conversation_messages

        # Run
        response = self.llm.invoke(prompt)
        return {"messages": [response]}

    def setup_conversation_graph(self):
        '''
        Set up a Streamlit conversational graph

        :return:
        '''

        ## Step 12: Create graph_builder
        graph_builder = StateGraph(MessagesState)

        # Step 14: Execute the retrieval.
        # tools = ToolNode([self.retrieve])
        tools = ToolNode([StructuredTool.from_function(self.retrieve)])

        # Step 16: Build graph
        graph_builder.add_node(self.query_or_respond)
        graph_builder.add_node(tools)
        graph_builder.add_node(self.query_data)
        graph_builder.add_node(self.generate)

        graph_builder.set_entry_point("query_or_respond")
        graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {END: END, "tools": "tools"},
        )
        graph_builder.add_edge("tools", "query_data")
        graph_builder.add_edge("query_data", "generate")
        graph_builder.add_edge("generate", END)

        memory = MemorySaver()

        graph = graph_builder.compile(checkpointer=memory)

        self.config = {"configurable": {"thread_id": "abc123"}}

        return graph

    def show_conversation(self, input_message: str):
        '''
        Method to output the chatbot conversation
        '''

        self.saved_steps = []
        for step in self.graph.stream(
            {"messages": [{"role": "user", "content": input_message}]},
            stream_mode="values",
            config=self.config
        ):
            if self.chat_bot_verbose:
                step["messages"][-1].pretty_print()
                self.saved_steps.append(step)

            if step["messages"][-1].type == "ai":
                self.ai_response = step["messages"][-1].content

            try:
                self.retrieved_urls = list(set([(doc.metadata["seed_url"], doc.metadata["page_url"]) \
                                             for doc in self.retrieved_docs]))

            except:
                self.retrieved_urls = []

    def read_csv_file(self, file_source, file_name):
        '''
        Method to read a csv file from GCS

        ##################
        Update to read_csv_file_into_pandas from gcp_tools

        '''

        # Create a storage client
        storage_client = storage.Client(project=self.gcp_project_id)

        # Get the bucket
        bucket = storage_client.bucket(bucket_name=self.gcs_csv_file_bucket_name)

        # Note: Client.list_blobs requires at least package version 1.17.0.
        blobs = storage_client.list_blobs(bucket,
                                          prefix=self.gcs_csv_file_directory.format(file_source))

        # Note: The call returns a response only when the iterator is consumed.
        for blob in blobs:
            if blob.name.find(file_name) >= 0:
                # Get the blob
                blob_file = bucket.blob(blob.name)

                # Works
                data = blob_file.download_as_bytes()
                return pd.read_csv(io.BytesIO(data))

        return None


