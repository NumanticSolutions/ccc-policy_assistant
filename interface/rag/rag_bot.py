# © 2025 Numantic Solutions LLC
# MIT License
#

import sys, os
import re
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
    """ BotCCCGlobals class holds globals for a chatbot based on a
    pre-trained model (phi3) and document retrieval from a vector
    database (ChromaDB). It includes a range of defaults, including
    an (optional) succinctness constraint, the default question, the
    file name for any saved transcripts, and the path & collection
    name for the vector database. """

    def __init__(self, **kwargs):
        self.version = "25.02.24"

        self.transcript_name_base = "cccbot_transcript"
        self.transcript_path = "./local_transcripts/"
        self.transcript_gcs_bucket = "cccbot-transcripts"
        self.transcript_gcs_directory = ""
        self.chroma_collection_name = "crawl_docs1"

        self.gcp_project_id = "eternal-bongo-435614-b9"
        self.gcp_location = "us-central1"
        self.gcs_embeddings_bucket_name = "ccc-chromadb-vai-2"
        self.gcs_embeddings_directory = ""

        self.embedding_model = "text-embedding-004"
        self.embedding_num_batch = 5
        self.embeddings_local_path = "data/local_chromadb/"
        # self.embeddings_local_path = ("/Users/stephengodfrey/OneDrive - numanticsolutions.com"
        #                               "/Engagements/Projects/ccc_policy_assistant/data/embeddings-vai")

        self.llm_model = "gemini-1.5-pro"
         # self.llm_model = "gemini-2.0-flash-exp"
        self.llm_model_max_output_tokens = 8192
        self.llm_model_temperature = 0.2
        self.llm_model_top_p = 0.8
        self.llm_model_top_k = 40
        self.llm_model_verbose = True

        self.retriever_search_type = "similarity"
        self.retriever_search_kwargs = {"k": 3}

        self.default_question = "What shall we discuss?"
        # self.be_succinct = ('Please provide only a one or two word answer' +
        #                     'Be as succinct as possible when answering. ')
        # self.prompt_template = """
        #                         You are a California Community College AI assistant.
        #                         You're tasked to answer the question given below,
        #                         but only based on the context provided.
        #                         context: {context}
        #                         question: {input}
        #                         If you cannot find an answer ask the user to rephrase the question.
        #                         answer:
        #                        """
        # self.prompt_template = ("You are a California Community College AI assistant. "
        #                         "Use the following pieces of context to answer the question at the end. "
        #                         "If you don't know the answer, just say that you don't know, "
        #                         "don't try to make up an answer. ")
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

        self.doc_search_retrieval_k = 4

        # Update any keyword args
        self.__dict__.update(kwargs)

        creds = ApiAuthentication()

        # LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        # os.environ["LANGCHAIN_API_KEY"] = creds.apis_configs["LANGCHAIN_API_KEY"]    [2502] n8

        # Google
        # os.environ["GOOGLE_API_KEY"] = creds.apis_configs["GOOGLE_API_KEY"]          [2502] n8

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

        # Get documents before and after
        self.extended_retrieved_docs = []
        for i, doc in enumerate(self.retrieved_docs):

            # Get dall documents from this source
            self.extended_retrieved_docs.append(self.vector_store.get(where={"page_url": {"$eq": doc.metadata["page_url"]}}))

            # Add the retrieved doc
            self.extended_retrieved_docs.append(doc)

        self.extended_retrieved_docs = self.retrieved_docs

        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in self.extended_retrieved_docs
        )

        return serialized, self.extended_retrieved_docs

    # Step 1: Generate an AIMessage that may include a tool-call to be sent.
    def query_or_respond(self, state: MessagesState):
        """Generate tool call for retrieval or respond."""

        # llm_with_tools = self.llm.bind_tools([self.retrieve])
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
        graph_builder.add_node(self.generate)

        graph_builder.set_entry_point("query_or_respond")
        graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {END: END, "tools": "tools"},
        )
        graph_builder.add_edge("tools", "generate")
        graph_builder.add_edge("generate", END)

        memory = MemorySaver()

        graph = graph_builder.compile(checkpointer=memory)

        self.config = {"configurable": {"thread_id": "abc123"}}

        return graph

    def show_conversation(self, input_message: str, verbose=False):
        self.saved_steps = []
        for step in self.graph.stream(
            {"messages": [{"role": "user", "content": input_message}]},
            stream_mode="values",
            config=self.config
        ):
            if verbose:
                step["messages"][-1].pretty_print()
                self.saved_steps.append(step)

            if step["messages"][-1].type == "ai":
                self.ai_response = step["messages"][-1].content

            try:
                self.source_urls = list(set([(doc.metadata["seed_url"], doc.metadata["page_url"]) \
                                             for doc in self.retrieved_docs]))

            except:
                self.source_urls = []




