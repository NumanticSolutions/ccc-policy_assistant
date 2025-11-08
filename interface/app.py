# © 2025 Numantic Solutions LLC
# MIT License
#
#
# A retrieval-centric interface for CCC-PA Version 3
#

### Step 1. Import libraries
import sys, os
import json
import time
import base64
from datetime import datetime
import traceback
import streamlit as st
import vertexai

### Step 1.1. Import Numantic utilities
try:
    if 'USER' in os.environ.keys() and os.environ['USER'] == 'numantic':
        utils_path = "/Users/numantic/Documents/GitHub/utilities/.."
    elif 'USER' in os.environ.keys() and os.environ['USER'] == 'stephengodfrey':
        utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
    else:
        utils_path = "utilities/"
except:
    utils_path = "utilities/"
sys.path.insert(0, utils_path)
try:
    from utilities.osa_tools.authentication import ApiAuthentication
    import utilities.logging.response_logger as rl
except:
    from authentication import ApiAuthentication
    import response_logger as rl

try:
    import random_questions as rq
except:
    utils_path = "utilities/"
    sys.path.insert(0, utils_path)
    import random_questions as rq

### Step 1.2. Import agent handlers
chatbot_path = "agent_handlers/"
sys.path.insert(0, chatbot_path)
from ccc_report_writer import ReportWriterResults

### Step 1.3. Import report writers
from report_display import display_report
from report_display import format_download_content

### Step 1.4. Authenticate if needed
if "GOOGLE_API_KEY" not in os.environ.keys():
    api_configs = ApiAuthentication(client="CCC")

### Step 1.5. Initialize Vertex AI
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

### Step 1.6. Set parameters
time_fmt = "%Y%m%d_%H%M%S"

### Step 2. Initialize Streamlit message service
if "pol_report_writer" not in st.session_state:
    user_id = "ccc_generic_user"
    session_id = datetime.now().strftime(time_fmt)
    agent_server = "vertexai_client"

    st.session_state.pol_report_writer = ReportWriterResults(
        user_id=user_id,
        session_id=session_id,
        agent_server=agent_server
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

### Step 2.5. Set up download content
if st.session_state.messages:
    # If there are messages, generate the full formatted content
    st.session_state.download_content = format_download_content(st.session_state.messages)
else:
    # Default message content
    st.session_state.download_content = ("No report history to download yet. "
                                         "If you don't see your report, try hitting the download button again.")

### Step 3. Set up Streamlit Interface
menu_items = {"Get help": "https://numanticsolutions.com/#contactus"}
st.set_page_config(page_title="CCC-PA",
                   page_icon="data/images/Numantic Solutions_Fav Icon_orange.png",
                   initial_sidebar_state="auto",
                   menu_items=menu_items)

### Step 3.1. Set up center page
images_path = "data/images"
logo_file = "Numantic Solutions_Logotype_light.png"

### Step 3.2. Create a clickable logo link
with open(os.path.join(images_path, logo_file), "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()
link_url = "https://numanticsolutions.com/#"
full_data_uri = f"data:image/png;base64,{encoded_string}"
html_code = f"""
<div style="text-align: center;"> 
    <a href="{link_url}" target="_blank">
        <img src="{full_data_uri}" width="400">
    </a>
</div>
"""
st.markdown(html_code, unsafe_allow_html=True)

### Step 3.3. Set up center panel
st.title("California Community College Policy Assistant")
bot_summary = ("This an experimental chatbot employing Artificial Intelligence "
               "to help users improve their understanding of  "
               "California community college policy topics. \n "
               "\nThe target audience are stakeholders "
               "in the community college decision making process who would benefit from more relevant "
               "and thorough information. \n\n"
               "More information: "
               "[GitHub - ccc-policy_assistant](https://github.com/NumanticSolutions/ccc-policy_assistant)"
               )
st.markdown(bot_summary)

### Step 4. Add action buttons
st.markdown(
    """
    <hr style="border: none; height: 1px; background-color: #ED8428;">
    """, unsafe_allow_html=True
)
columns = st.columns(3)

### Step 4.1. Add example links button
columns[0].link_button(label="Example Reports",
                       url="https://eternal-bongo-435614-b9.uc.r.appspot.com/example_reports")

### Step 4.2. Add download conversation button
download_label = "Download Reports"
columns[1].download_button(
    label=download_label,
    data=st.session_state.download_content,
    file_name=f"policy_chat_export_{datetime.now().strftime(time_fmt)}.txt",
    mime="text/markdown",
    help="Download the entire chat history, including the structured report."
)

### Step 4.3. Add Clear conversation button
reset_button = columns[2].button("Clear Reports")
st.markdown(
    """
    <hr style="border: none; height: 1px; background-color: #ED8428;">
    """, unsafe_allow_html=True
)

### Step 5. Set up interface side bar
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
        st.subheader("Version 3")
        version_msg = ("- Deployed : " + "Nov 8, 2025")
        st.markdown(version_msg)

### Step 6. Display Chat Messages (used to track user interaction)
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

### Step 7. Accept User Input and Generate Report
if user_input := st.chat_input("Ask a policy-level question ..."):

    ### Step 7.1 Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    ### Step 7.2. Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    ### Step 7.3. Get the policy assistant's response
    spinner_msg = ("Working ... generating a policy report in response to your query; "
                   "this can take 1 to 3 minutes.")

    with st.chat_message("assistant"):
        with st.spinner(spinner_msg):

            ### Step 7.3.1: Get start time
            ai_starttime = datetime.now()

            ### Step 7.3.2. Call the function
            st.session_state.pol_report_writer.create_policy_report(query=user_input)

            ### Step 7.3.3. ACCESS THE RESULT FROM THE SPECIFIED ATTRIBUTE
            report_data = st.session_state.pol_report_writer.report_dict

            ### Step 7.3.4. Display the structured report using the helper function
            display_report(report_data)

            #### Step 7.3.5. Add the structured report (dictionary) to chat history for persistence
            st.session_state.messages.append({"role": "assistant", "content": report_data})

            ### Step 7.3.6: Get finish time
            ai_endtime = datetime.now()

            ### Step 7.3.7. Create response logger object parameters
            gen_time = ai_endtime - ai_starttime
            comments = ("production ccc streamlit app;"
                        "report generation time (sec): {}").format(gen_time.total_seconds())

            rlog_params = {"query": user_input,
                           "response": json.dumps(report_data),
                           "app": "ccc_policy_assist",
                           "version": "2511_T",
                           "ai": "gemini-2.5-flash",
                           "agent": "synthesis",
                           "comments": comments}

            bq_logger = rl.ResponseLogger()
            bq_logger.response_to_bq(rlog_params=rlog_params)

### Step 8. Clear history if requested
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    session_id = datetime.now().strftime(time_fmt)
    st.rerun()



