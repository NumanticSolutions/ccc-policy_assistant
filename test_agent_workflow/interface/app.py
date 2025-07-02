# © 2025 Numantic Solutions LLC
# MIT License
#

#
# A retrieval-centric interface for CCC-PA
#

import sys, os
import streamlit as st
import vertexai
# from vertexai import agent_engines
# from google.adk.memory import InMemoryMemoryService


# Import authentication object
utils_path = "../utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
api_configs = ApiAuthentication(client="CCC")


# Initialize Vertex AI API once per session
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

# Import chatbot
chatbot_path = "../"
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
    st.session_state["bot"] = cccChatBot(user_id=user_id)

#
#
if "messages" not in st.session_state:
    st.session_state.messages = []
#
# # displays the chat history when app is rerun
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

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

# displays the chat history when app is rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            format_agent_output(report_dict=message["content"])


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

    # Query the agent
    st.session_state["bot"].stream_and_parse_query(query=user_input)

    st.session_state.messages.append({"role": "assistant",
                                      "content": st.session_state["bot"].report_dict})

    # Display results
    format_agent_output(report_dict=st.session_state["bot"].report_dict)

    # # Display results
    # for key in st.session_state["bot"].report_dict.keys():
    #     if key == "report_title":
    #         st.markdown("## {}\n\n".format(st.session_state["bot"].report_dict[key]))
    #     elif key == "report_executive_summary":
    #         st.markdown("### Summary: \n{}\n".format(st.session_state["bot"].report_dict[key]))
    #     elif key == "report_body":
    #         st.markdown("### Report: \n{}\n".format(st.session_state["bot"].report_dict[key]))
    #     elif key == "report_references":
    #         st.markdown("### References: \n{}\n".format(st.session_state["bot"].report_dict[key]))
    #     elif key == "reference_uris":
    #         # Convert URLs to markdown list
    #         ref_uris_md = ["- {}\n".format(u) for u in st.session_state["bot"].report_dict["reference_uris"]]
    #         st.markdown("### Reference URLs \n")
    #         st.markdown(" ".join(ref_uris_md))




# Option to clear chat history
# if st.button("Clear Chat"):
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    # st.session_state["bot"] = None
    # memory.clear()
    st.rerun()
    st.cache_data.clear()
    # rest_button = False

