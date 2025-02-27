# © 2025 Numantic Solutions LLC
# MIT License
#

#
# * A retrieval-centric interface for CCC-PA
#


import streamlit as st

# import json
import sys, os
# import re
# import datetime


# import gcp_tools as gct
# import authentication as auth

# import rag_bot_1 as rb1
sys.path.insert(0, "rag")
sys.path.insert(0, "utils")
from rag_bot import CCCPolicyAssistant

st.set_page_config(page_title="CCC-PA")

########## Set up Streamlit
font_url = ("https://fonts.googleapis.com/css2?family=Lato:ital,wght"
            "@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&display=swap")
streamlit_style = """
			<style>
			@import url({font_url});

			html, body, [class*="css"]  {{
			font-family: 'Roboto', sans-serif;
			}}
			</style>
			"""
st.markdown(streamlit_style, unsafe_allow_html=True)

images_path = "data/images"
logo_file = "Numantic Solutions_Logotype_light.png"
st.image(os.path.join(images_path, logo_file), width=600)
st.title("California Community College Policy Assistant")
bot_summary = ("This an experimental chatbot employing Artificial Intelligence tools "
               "to help users easily improve their understanding of policy topics related "
               "to California's community colleges. "
               "The bot's target audience are stakeholders who would like to participate "
               "in community college decision making and would benefit from curated and detailed "
               "information related to community colleges. Some examples might include board members, "
               "administrators, staff, students, community activists or legislators. \n")

invite = ("By making this tool available, we hope to demonstrate "
          "how policy advocacy can be supported through the use of technology. "
          "If you want to learn more or have thoughts about this application or similar "
          "tools or the underlying technology, please reach out to Steve or Nathan at "
          ":primary[info@numanticsolutions.com]")

st.text(bot_summary)
st.markdown(invite)
st.divider()

########## Handle conversations in Streamlit
# Build session components if needed
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "bot" not in st.session_state:
    # st.session_state["bot"] = CCCPolicyAssistant(chroma_collection_name = "crawl_docs-vai-2",
    #                                              chat_bot_verbose=False,
    #                                              dot_env_path = "../data/environment")

    # # For use when API keys are in GCP secrets
    st.session_state["bot"] = CCCPolicyAssistant(chroma_collection_name = "crawl_docs-vai-2",
                                                 chat_bot_verbose=False,
                                                 dot_env_path = "")

if "messages" not in st.session_state:
    st.session_state.messages = []

# displays the chat history when app is rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.sidebar:
    sidebar_msg = ("This is an experimental chatbot that is still under development. "
                   "Please reach out with feedback, suggestions and comments."
                   )
    github_url = "https://github.com/NumanticSolutions/ccc-policy_assistant"
    github_msg = ("Code can be found at [github.com/NumanticSolutions]({})").format(github_url)

    st.header(sidebar_msg)
    st.markdown(github_msg)

    tab1, tab2 = st.tabs(["Example Questions", "Terms & Privacy"])

    with tab1:
        st.header("Example Questions")
        st.text("• How many districts are there in the California community college system?")
        st.text("• What is the part-time enrollment of Foothill College?")
        st.text("• What college is designated a Center of Excellence in bioprocessing?")
        st.text("• How many California community colleges partner with the California Department of Corrections and Rehabilitation (CDCR) to provide in‑person courses?")
        st.text("• What are the responsibilities of the board members of a California community college?")
    with tab2:
        st.header("Terms & Privacy")
        terms_url = "https://numanticsolutions.com/#terms"
        terms_msg = ("The full terms of use can be found [here]({}).").format(terms_url)
        st.markdown(terms_msg)

        privacy_url = "https://numanticsolutions.com/#privacy"
        privacy_msg = ("A complete privacy policy is [here]({}). Note that for this assistant, sessions are logged for testing and development purposes.").format(privacy_url)
        st.markdown(privacy_msg)

        version_msg = ("Version : " + st.session_state["bot"].version)
        st.markdown(version_msg)

# displays the chat history when app is rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Reset button
columns = st.columns(4)
reset_button = columns[3].button("Clear Chat")
# reset_button = st.button3("Clear Chat")

# Input box for user's query
user_input = st.chat_input("Your message")

if user_input:
    # Display user's message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Store user's query in the chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get the AI assistant's response
    st.session_state["bot"].show_conversation(input_message=user_input)

    # Get retrieved urls
    retrieved_urls = ["- [{}]({})\n".format(up[0], up[1]) for up in st.session_state["bot"].retrieved_urls]
    retrieved_urls = list(set(retrieved_urls))

    # Create a single string of retrieved URLs
    res_phrase = ""
    if len(retrieved_urls) > 0:
        res_phrase = "\n\nThese references might be useful: \n{}".format(" ".join(retrieved_urls))

    # Combine into a single response
    ai_response = "{} {}".format(st.session_state["bot"].ai_response, res_phrase)

    # Add query result response
    if len(st.session_state["bot"].query_data_result) > 0:
        ai_response = "{}\n{}".format(ai_response, st.session_state["bot"].query_data_result)

    # Store AI's response in the chat history
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Display assistant's message
    with st.chat_message("assistant"):
        st.markdown(ai_response)

# Option to clear chat history
# if st.button("Clear Chat"):
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    # st.session_state["bot"] = None
    # memory.clear()
    st.rerun()
    # st.cache_data.clear()
    rest_button = False

