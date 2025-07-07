# © 2025 Numantic Solutions LLC
# MIT License
#

#
# A retrieval-centric interface for CCC-PA
#

import sys, os
import json
import time
import streamlit as st
import vertexai
# from vertexai import agent_engines
# from google.adk.memory import InMemoryMemoryService


# Import authentication object
utils_path = "utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
api_configs = ApiAuthentication(client="CCC")
import response_logger as rl


# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

# Import chatbot
chatbot_path = "agent_handlers/"
sys.path.insert(0, chatbot_path)
from ccc_chatbot_agent import cccChatBot

########## Set up Streamlit
st.set_page_config(page_title="CCC-PA")
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

st.text(bot_summary)
st.divider()

########## Handle conversations in Streamlit
# Build session components if needed
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "bot" not in st.session_state:
    # Create a chatbot for this user
    user_id = "u_123"
    try:
        st.session_state["bot"] = cccChatBot(user_id=user_id)
    except:
        try:
            time.sleep (5)
            msg = ("We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
                   "doesn't work, please refresh this web page and try again. ")
            st.markdown(msg)
            st.session_state["bot"] = cccChatBot(user_id=user_id)

        except:
            msg = ("We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
                   "doesn't work, please refresh this web page and try again. ")
            st.markdown(msg)
            time.sleep(5)
            st.experimental_rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# display function
def format_agent_output(report_dict: dict):
    """
    Function to format agent's output into Markdown for interface display
    """

    # Display results
    for key in report_dict.keys():
        if key == "report_title":
            st.markdown("## {}\n\n".format(report_dict[key]))
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


with st.sidebar:
    # sidebar_msg = ("This is an experimental chatbot that is still under development. "
    #                "Please reach out with feedback, suggestions and comments."
    #                )

    sidebar_msg = ("Overview")

    st.header(sidebar_msg)
    st.text("\n\n\n")

    invite = ("By making this tool available, we hope to demonstrate "
              "how policy advocacy can be supported through the use of technology. ")
    invite2 = ("If you want to learn more or have thoughts about this application, similar "
              "tools or the underlying technology, please reach out to Steve or Nathan at "
              ":primary[info@numanticsolutions.com] ")

    st.markdown(invite)
    st.markdown(invite2)
    st.text("\n\n\n")


    tab1, tab2 = st.tabs(["Example Questions", "Useful Links"])
    with tab1:
        st.header("Example Questions")
        st.text("• How many districts are there in the California community college system?")
        st.text("• What is the part-time enrollment of Foothill College?")
        st.text("• What college is designated a Center of Excellence in bioprocessing?")
        st.text("• How many California community colleges partner with the California Department of Corrections and Rehabilitation (CDCR) to provide in‑person courses?")
        st.text("• What are the responsibilities of the board members of a California community college?")
    with tab2:
        links = ("- [C3PA Studio](https://c3pa-studio-1062597788108.us-central1.run.app/)\n"
                 "- [GitHub](https://github.com/NumanticSolutions/ccc-policy_assistant)\n"
                 "- [Numantic Solutions](https://numanticsolutions.com)\n\n"
                 "- [Terms of Use](https://numanticsolutions.com/#terms)\n"
                 "- [Privacy Policy](https://numanticsolutions.com/#privacy)\n"
                 )
        st.text("\n")
        st.markdown(links)

        st.text("\n")
        ### ??? st.session_state["bot"].version
        version_msg = ("Version : " + "ADK Jun 27, 2025")
        st.markdown(version_msg)


# Reset button
columns = st.columns(4)
reset_button = columns[3].button("Clear Chat")

# Object to hold content so screen can be cleared
chat_placeholder = st.empty()

# Input box for user's query
user_input = st.chat_input("Your message")


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
                    st.markdown(
                        "Here's what my search of the IPEDS data found; Do you want me to run an IPEDS query?")
                    st.markdown(message["content"])

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
            try:
                time.sleep(5)
                msg = ("We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
                       "doesn't work, please refresh this web page and try again. ")
                st.markdown(msg)
                st.session_state["bot"].stream_and_parse_query(query=user_input)

            except:
                msg = ("We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
                       "doesn't work, please refresh this web page and try again. ")
                st.markdown(msg)
                time.sleep(5)
                st.rerun()


    # Add agent results to session messages
    st.session_state.messages.append({"role": "assistant",
                                      "content": st.session_state["bot"].report_dict})

    # Display report results
    format_agent_output(report_dict=st.session_state["bot"].report_dict)

    # Add to BigQuery
    # Create response logger object parameters
    rlog_params = {"query": user_input,
                   "response": json.dumps(st.session_state["bot"].report_dict),
                   "app": "ccc_policy_assist",
                   "version": "2507",
                   "ai": "gemini-2.0-flash-001",
                   "agent": "synthesis",
                   "comments": "testing ccc streamlit app"}

    bq_logger = rl.ResponseLogger()
    bq_logger.response_to_bq(rlog_params=rlog_params)

    # Display IPEDS search results
    st.markdown("### Data Analysis Assistant")
    st.markdown(st.session_state["bot"].ip_results.contents[0])

    # Add IPEDS
    st.session_state.messages.append({"role": "data_assistant",
                                      "content": st.session_state["bot"].ip_results.contents[0]})

    # Add to BigQuery
    # Create response logger object parameters
    rlog_params = {"query": user_input,
                   "response": st.session_state["bot"].ip_results.contents[0],
                   "app": "ccc_policy_assist",
                   "version": "2507",
                   "ai": "gemini-2.0-flash-001",
                   "agent": "rag_ipeds",
                   "comments": "testing ccc streamlit app"}

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

