# [2502] n8
#

import streamlit as st
import sys, os
import json
from datetime import datetime
import time
import hashlib

sys.path.insert(0, "rag")
sys.path.insert(0, "utils")
from rag_bot import CCCPolicyAssistant


def portable_hash(string):
    encoded_string = string.encode('utf-8')
    hash_object = hashlib.sha256(encoded_string)
    return hash_object.hexdigest()

testing_path = os.environ.get('MOUNT_PATH', '/c3pa-app/testing')    # gcs
# testing_path = 'c3pa-app/testing'

# name_txt = 'questions-250226-q10-a.txt'
# name_txt = 'questions-250226-q10-b.txt'
# name_txt = 'questions-250226-q10-c.txt'
name_txt = 'questions-250226-q10-d.txt'
# name_txt = 'questions-2502-q26.txt'

in_path = os.path.join(testing_path, name_txt)


st.subheader("C3PA Testing")
st.text('Batch mode testing of the California Community Colleges Policy-Assistant.')

st.divider()

bot = CCCPolicyAssistant()

questions = []
with open(in_path, "r") as file:
    for line in file:
        questions.append(line.strip())

qn = str(len(questions))
dt = str(datetime.now()).replace(" ", "-")

data = []
for i, question in enumerate(questions) :

    st.text(question.upper())

    h1 = portable_hash(question)

    prompt = question
    t1 = str(datetime.now()).replace(" ", "_")

    time.sleep(15)
    #
    response = bot.show_conversation(input_message=prompt, verbose=False)
    context_urls = bot.source_urls
    ai_response = bot.ai_response

    if len(context_urls) > 0:
        ai_response += " Context URLs : "
        for url in context_urls:
            ai_response += (" " + url + " ")

    st.text("\n")
    st.text(ai_response)
    st.divider()


    t2 = str(datetime.now()).replace(" ", "_")

    dict_ = {
        "n" : str(i+1),
        "qn" : qn,
        "question" : question,
        "prompt" : prompt,
        "response" : ai_response,
        "start" : t1,
        "stop" : t2,
        "hash" : h1,
        "version" : bot.version
    }
    data.append(dict_)

json_str = json.dumps(data)

name_json = "log_testing-c3pa-" + dt + ".json"
out_path = os.path.join(testing_path, name_json)
with open(out_path, "w") as f:
    f.write(json_str)

