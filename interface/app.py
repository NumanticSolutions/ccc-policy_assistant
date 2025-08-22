# © 2025 Numantic Solutions LLC
# MIT License
#

#
# A retrieval-centric interface for CCC-PA Version 2
#

import sys, os
import json
import time
import traceback
import streamlit as st
import vertexai

# Import authentication object
utils_path = "utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import response_logger as rl
import random_questions as rq

# Import chatbot
chatbot_path = "agent_handlers/"
sys.path.insert(0, chatbot_path)
from ccc_chatbot_agent import cccChatBot
from ccc_datascience_agent import cccDataScienceBot

if "GOOGLE_API_KEY" not in os.environ.keys():
    api_configs = ApiAuthentication(client="CCC")

# Initialize Vertex AI
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

########## Set up Streamlit
st.set_page_config(page_title="CCC-PA")
font_url="https://fonts.googleapis.com/css?family=Roboto"
streamlit_style = """
			<style>
			@import url({font_url});
			html, body, [class*="css"]  {{
			font-family: 'Roboto', sans-serif;
			}}
			</style>
			"""
st.markdown(streamlit_style, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* Target the container that holds the chat input */
    .stBottom {
        padding-bottom: 50px; /* Adjust this value to increase or decrease the margin */
    }
    </style>
    """,
    unsafe_allow_html=True
)

images_path = "data/images"
logo_file = "Numantic Solutions_Logotype_light.png"
st.image(os.path.join(images_path, logo_file), width=600)
st.title("California Community College Policy Assistant")
bot_summary = ("This an experimental chatbot employing Artificial Intelligence "
               "to help users improve their understanding of  "
               "California community college policy topics. \n "
               "\nThe target audience are stakeholders "
               "in the community college decision making process who would benefit from more relevant "
               "and thorough information. \n"
               )
example_qs = "- [Example Queries and Responses](https://eternal-bongo-435614-b9.uc.r.appspot.com/example_reports) \n"
# Some examples might include board members,
# administrators, staff, students, community activists or legislators.

# st.text(bot_summary)
st.markdown(bot_summary)
st.markdown(example_qs)
st.divider()

########## Handle conversations in Streamlit
# Build session components if needed
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "questions" not in st.session_state:
    st.session_state.questions = rq.generate_questions()

if "bot" not in st.session_state:
    # Create a chatbot for this user
    user_id = "u_123"
    try:
        # Synthesis chatbot
        st.session_state["bot"] = cccChatBot(user_id=user_id)
        #Data science chatbot
        st.session_state["ds_bot"] = cccDataScienceBot(user_id=user_id)

    except:
        time.sleep (5)
        msg = ("TRY BOT: We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
               "doesn't work, please refresh this web page and try again. ")
        st.markdown(msg)
        st.markdown(traceback.format_exc())
        st.session_state["bot"] = cccChatBot(user_id=user_id)
        st.session_state["ds_bot"] = cccChatBot(user_id=user_id)

if "messages" not in st.session_state:
    st.session_state.messages = []

# display function
def format_agent_output(report_dict: dict):
    """
    Function to format agent's output into Markdown for interface display
    """
    # Display results
    for key in report_dict.keys():

        # remove markdown

        if key == "report_title":
            title_text = report_dict[key].replace("#","")
            st.markdown("## {}\n\n".format(title_text))

        elif key == "report_executive_summary":
            st.markdown("### Summary: \n{}\n".format(report_dict[key]))

        elif key == "report_body":
            st.markdown("### Report: \n{}\n".format(report_dict[key]))

        elif key == "report_references":
            st.markdown("### References: \n{}\n".format(report_dict[key]))

        elif key == "reference_uris":
            # Convert URLs to markdown list
            ref_uris_md = ["- {}\n".format(u) for u in report_dict["reference_uris"]]
            st.markdown("### Reference URLs \n")
            st.markdown(" ".join(ref_uris_md))

        elif key == "relevant_data_yes_or_no":
            st.markdown("### IPEDS metadata search results:")
            st.markdown(report_dict["description_of_relevant_data"])

            # Look for tables
            if "relevant_table_names" in report_dict.keys():
                if type(report_dict["relevant_table_names"]) == list \
                        and len(report_dict["relevant_table_names"]) > 0:
                    tables_listing = ", ".join(report_dict["relevant_table_names"])

                elif type(report_dict["relevant_table_names"]) == str \
                        and len(report_dict["relevant_table_names"]) > 0:
                    tables_listing = ", ".join(report_dict["relevant_table_names"])

                st.markdown("Relevant tables: {}".format(tables_listing))

with st.sidebar:
    sidebar_msg = ("Objectives")

    st.header(sidebar_msg)
    st.text("\n\n\n")

    invite = ("- We hope to demonstrate "
              "how policy advocacy can be advanced through technology. ")
    invite2 = ("- Chats are logged for evaluation purposes. Please don't "
               "provide confidential, proprietary or restricted data.")
    invite3 = ("- To learn more or share your thoughts, please contact Steve or Nathan at "
               "[Numantic Solutuons](https://numanticsolutions.com/#contactus)")

    st.markdown(invite)
    st.markdown(invite2)
    st.markdown(invite3)
    st.text("\n\n\n")


    tab1, tab2 = st.tabs(["Example Questions", "Useful Links"])
    with tab1:
        st.header("Example Queries")
        for question in st.session_state.questions:
            st.text("• "+question)
    with tab2:
        links = ("- [Example Reports](https://eternal-bongo-435614-b9.uc.r.appspot.com/example_reports)\n"
                 "- [CCC-Bot Analytics](https://eternal-bongo-435614-b9.uc.r.appspot.com/home)\n"
                 "- [GitHub](https://github.com/NumanticSolutions/ccc-policy_assistant)\n"
                 "- [Numantic Solutions](https://numanticsolutions.com)\n\n"
                 "- [Terms of Use](https://numanticsolutions.com/#termsofservice)\n"
                 "- [Privacy Policy](https://numanticsolutions.com/#privacy)\n"
                 )
        st.text("\n")
        st.markdown(links)

        st.text("\n")
        ### ??? st.session_state["bot"].version
        version_msg = ("Version deployed : " + "Aug 15, 2025")
        st.markdown(version_msg)

# Reset button
columns = st.columns(4)
reset_button = columns[3].button("Clear Chat")

# Object to hold content so screen can be cleared
chat_placeholder = st.empty()

# Input box for user's query
user_input = st.chat_input("Your message")

dsa_msg = ("This is an experimental data science agent using the "
           "Integrated Postsecondary Education Data System (IPEDS) datasets from the U.S. Department "
           "of Education. We're now checking to see if any IPEDS data would be useful in answering "
           "your query.")

######## Chat stuff
if user_input:

    # Empty the screen
    # chat_placeholder.empty()

    # show previous chat history
    with chat_placeholder.container():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):

                if message["role"] == "user":
                    st.markdown(message["content"])

                elif message["role"] == "data_assistant":
                    st.markdown("### Data Analysis Assistant")
                    st.markdown(dsa_msg)
                    format_agent_output(report_dict=message["content"])

                else:
                    format_agent_output(report_dict=message["content"])

    # Display user's message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Store user's query in the chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Query the agent
    with st.spinner("I'm generating a report in response to your query; this can take 30 to 90 seconds. "):
        user_id = "u_123"
        try:
            st.session_state["bot"].stream_and_parse_query(query=user_input)
        except:
            time.sleep(5)
            msg = ("We're having trouble submitting queries to the CCC Policy Assistant. We're going to try again, but if that "
                   "doesn't work, please refresh this web page and try again. ")
            st.markdown(msg)
            st.markdown(traceback.format_exc())
            st.session_state["bot"].stream_and_parse_query(query=user_input)

    # Add agent results to session messages
    st.session_state.messages.append({"role": "assistant",
                                      "content": st.session_state["bot"].report_dict})

    # Display report results
    format_agent_output(report_dict=st.session_state["bot"].report_dict)


    ## Data Science Agent
    # Display IPEDS search results
    st.markdown("## Data Analysis Assistant")
    st.markdown(dsa_msg)

    # Check IPEDS data
    st.session_state["ds_bot"].search_ipeds_metadata(query=user_input)

    # Format and display IPEDS metadata findings
    if type(st.session_state["ds_bot"].report_dict) == dict and \
        len(st.session_state["ds_bot"].report_dict) > 0:
        format_agent_output(report_dict=st.session_state["ds_bot"].report_dict)
    else:
        no_ipeds_msg = ("Our search of the Integrated Postsecondary Education Data System (IPEDS) "
                        "did not find data relevant to your query.")
        report_dict = dict(relevant_data_yes_or_no=False,
                           description_of_relevant_data=no_ipeds_msg)
        print(report_dict)
        format_agent_output(report_dict=report_dict)

    # Add IPEDS
    st.session_state.messages.append({"role": "data_assistant",
                                      "content": st.session_state["ds_bot"].report_dict})


    # Add Chatbot BigQuery
    # Create response logger object parameters
    rlog_params = {"query": user_input,
                   "response": json.dumps(st.session_state["bot"].report_dict),
                   "app": "ccc_policy_assist",
                   "version": "2508",
                   "ai": "gemini-2.5-flash",
                   "agent": "synthesis",
                   "comments": "production ccc streamlit app"}

    bq_logger = rl.ResponseLogger()
    bq_logger.response_to_bq(rlog_params=rlog_params)


    # Add DataScience agent BigQuery
    # Create response logger object parameters
    rlog_params = {"query": user_input,
                   "response": json.dumps(st.session_state["ds_bot"].report_dict),
                   "app": "ccc_policy_assist",
                   "version": "2508",
                   "ai": "gemini-2.5-flash",
                   "agent": "rag_ipeds",
                   "comments": "production ccc streamlit app"}

    bq_logger = rl.ResponseLogger()
    bq_logger.response_to_bq(rlog_params=rlog_params)


# Option to clear chat history
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    # st.session_state["bot"] = None
    # memory.clear()
    st.rerun()
    st.cache_data.clear()
    # rest_button = False
