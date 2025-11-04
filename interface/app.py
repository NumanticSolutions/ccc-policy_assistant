# © 2025 Numantic Solutions LLC
# MIT License
#
#
# A retrieval-centric interface for CCC-PA Version 3
#

import sys, os
import json
import time
from datetime import datetime
import traceback
import streamlit as st
import vertexai

# Import authentication object
if os.environ['USER'] == 'numantic':
    utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
elif os.environ['USER'] == 'stephengodfrey':
    utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
else:
    utils_path = "/utilities/"

sys.path.insert(0, utils_path)
from utilities.osa_tools.authentication import ApiAuthentication
import utilities.logging.response_logger as rl

sys.path.insert(0, "utilities/")
import random_questions as rq

# Chatbot
chatbot_path = "agent_handlers/"
sys.path.insert(0, chatbot_path)
from ccc_report_writer import ReportWriterResults

# Report writer
from report_display import display_report


if "GOOGLE_API_KEY" not in os.environ.keys():
    api_configs = ApiAuthentication(client="CCC")

# Initialize Vertex AI
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

### Set up Streamlit
menu_items = {"Get help": "https://numanticsolutions.com/#contactus"}
st.set_page_config(page_title="CCC-PA",
                   page_icon="data/images/Numantic Solutions_Fav Icon_orange.png",
                   initial_sidebar_state="auto",
                   menu_items=menu_items)

### Step 1. Set up center page
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

# st.text(bot_summary)
st.markdown(bot_summary)
st.markdown(example_qs)

# Reset button
columns = st.columns(5)
reset_button = columns[4].button("Clear Chat")
st.divider()

### Step 2. Set up sidebar
if "questions" not in st.session_state:
    st.session_state.questions = rq.generate_questions()
with st.sidebar:
    sidebar_msg = ("Objectives")

    st.header(sidebar_msg)
    st.text("\n\n\n")

    invite = ("- In this open-source project, we demonstrate "
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
        version_msg = ("Version deployed : " + "Nov 3, 2025")
        st.markdown(version_msg)

### Handle conversations in Streamlit
### Step 3. Initialize Session State
if "pol_report_writer" not in st.session_state:
    user_id = "ccc_generic_user"
    session_id = datetime.now().strftime("%Y%m%d")
    agent_server = "vertexai_client"

    st.session_state.pol_report_writer = ReportWriterResults(
        user_id=user_id,
        session_id=session_id,
        agent_server=agent_server
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

### Step 4. Display Chat Messages (used to track user interaction)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Messages from the assistant will be a JSON object containing the report dictionary
        if message["role"] == "assistant":
            # If the content is a dictionary, display it using the custom function
            if isinstance(message["content"], dict):
                st.subheader("Report Generated:")
                display_report(message["content"])
            else:
                st.markdown(message["content"])
        else:
            # Display user query as simple markdown
            st.markdown(message["content"])

### Step 5. Accept User Input and Generate Report
if user_input := st.chat_input("Ask a policy-level question ..."):

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get the policy assistant's response
    spinner_msg = "Working ... generating a policy report in response to your query; this can take 30 to 90 seconds."
    with st.chat_message("assistant"):
        with st.spinner(spinner_msg):
            # --- Key Steps ---
            ### Step 5.1. Call the function
            st.session_state.pol_report_writer.create_policy_report(query=user_input)

            ### Step 5.2. ACCESS THE RESULT FROM THE SPECIFIED ATTRIBUTE
            report_data = st.session_state.pol_report_writer.report_dict

            ### Step 5.3. Display the structured report using the helper function
            display_report(report_data)

            #### Step 5.4. Add the structured report (dictionary) to chat history for persistence
            st.session_state.messages.append({"role": "assistant", "content": report_data})

            ### Step 5.5. Create response logger object parameters
            rlog_params = {"query": user_input,
                           "response": json.dumps(report_data),
                           "app": "ccc_policy_assist",
                           "version": "2511",
                           "ai": "gemini-2.5-flash",
                           "agent": "synthesis",
                           "comments": "production ccc streamlit app"}

            bq_logger = rl.ResponseLogger()
            bq_logger.response_to_bq(rlog_params=rlog_params)

### Step 6. Provide option to clear chat history
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    # st.session_state["bot"] = None
    # memory.clear()
    st.rerun()
    st.cache_data.clear()
    # rest_button = False


