# Agent name
memory_agent_name = "memory_recall_agent"

# Agent description
memory_agent_description = "An agent for retrieving relevant information from the chatbot's memory service."

# Create an agent instruction
memory_agent_instruction = """
                           Answer the user's question. Use the 'load_memory' tool 
                           if the answer might be in past conversations. 
                           """