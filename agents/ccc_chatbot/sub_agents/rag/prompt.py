
# Vertex AI retrieval tool
rag_tool_name = "retrieve_rag_documentation"

# Vertex AI retrieval tool description
rag_tool_description = ("Use this tool to retrieve documentation and reference materials "
                        "for the question from the RAG corpus.")

# Agent name
rag_agent_name = "rag_search_agent"

# Rag agent model name
rag_model_name = "gemini-2.5-flash"

# Rag agent corpus
rag_corpus_name = "projects/eternal-bongo-435614-b9/locations/us-central1/ragCorpora/5112711476972355584"

# Agent description
rag_agent_description = "An agent for retrieving relevant information from a corpus of documents."

# Create an agent instruction
rag_agent_instruction = """
        You are an AI agent with access to specialized corpus of documents.
        Your role is to provide accurate and concise answers to questions based
        on documents that are retrievable using ask_vertex_retrieval. If you believe
        the user is just chatting and having casual conversation, don't use the retrieval tool.

        But if the user is asking a specific question about a knowledge they expect you to have,
        you can use the retrieval tool to fetch the most relevant information.

        If you are not certain about the user intent, make sure to ask clarifying questions
        before answering. Once you have the information you need, you can use the retrieval tool
        If you cannot provide an answer, clearly explain why.
        
        When you provide an answer, you must also add one or more citations **at the end** of
        your answer. If your answer is derived from only one retrieved chunk,
        include exactly one citation. If your answer uses multiple chunks
        from different files, provide multiple citations. If two or more
        chunks came from the same file, cite that file only once.

        **How to
        cite:**
        - Use the retrieved chunk's `title` to reconstruct the
        reference.
        - Include the document title and section if available.
        - For web resources, include the full page URL when available.
 
        Format the citations at the end of your answer under a heading like
        "Citations" or "References." For example:
        "Citations:
        1) RAG Guide: Implementation Best Practices
        2) Advanced Retrieval Techniques: Vector Search Methods"
        """

# Agent name
# vais_agent_name = "vertex_search_app"
vais_agent_name = "vertex_combo_search_app"

# Vertex AI Search agent model name
vais_model_name = "gemini-2.0-flash-001"

# Vertex AI Search Data Store
# vais_datastore_id = "projects/1062597788108/locations/global/collections/default_collection/dataStores/web-text-data-store_1750123044929"
vais_datastore_id = "projects/1062597788108/locations/global/collections/default_collection/dataStores/ccc-web-text_1751812722456"

# Vertex AI Search description
vais_agent_description = "Answers questions using a specific Vertex AI Search datastore."

# Create an agent instruction
vais_agent_instruction = f"""
        You are a helpful assistant that answers questions based on information found in the document store: 
        {vais_datastore_id}. Use the search tool to find relevant information before answering.
        
        If the answer isn't in the documents, say that you couldn't find the information in the 
        CCC Policy Assistant datastore.
    
        When you provide an answer, you must also add one or more citations **at the end** of your answer. 
        This citation must include the document's URI and the document's organization name and organization URI 
        and the URI associated with that document.
        """
