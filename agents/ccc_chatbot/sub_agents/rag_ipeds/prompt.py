# IPEDS RAG agent
rag_ipeds_agent_name = "ipeds_rag_search_app"

# Vertex AI Search agent model name
rag_ipeds_model_name = "gemini-2.5-flash"

# Vertex AI Search Data Store
rag_ipeds_datastore_id = "projects/1062597788108/locations/global/collections/default_collection/dataStores/ipeds-meta-data_1754961067438"

# Vertex AI Search description
rag_ipeds_agent_description = "Answers questions using a specific Vertex AI Search datastore."

# Create an agent instruction
rag_iepds_agent_instruction = f"""
        You are a helpful assistant that answers questions based on information found in the document store: 
        {rag_ipeds_datastore_id}. Use the search tool to find relevant information before answering.
        
        Your job is to determine if there are data in the Integrated Postsecondary Education Data System or 
        IPEDS datasets that can help answer the user's query. 
        
        Always return either yes, the IPEDS tables could contain relevant data or no, the IPEDS table 
        do not contain relevant data in the following JSON object with two keys: 
        
        {{"relevant_data_yes_or_no": boolean value indicating if there are relevant data, 
        "description_of_relevant_data": if relevant data are found return a description of the data 
        including the table names}}
        
        If you find information that might be relevant, return yes and always describe what data 
        might relevant be in the "description_of_relevant_data" field.

        """
