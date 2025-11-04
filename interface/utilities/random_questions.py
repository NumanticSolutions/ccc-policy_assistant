# [2507] n8
#

import json, os, requests


def generate_questions():
    """ Generate random questions, if unable to do so will return default questions. """


    ######### This needs to be updated when we shut down the old project
    project = os.environ["GOOGLE_CLOUD_PROJECT"]

    ######### Overriding with old name
    project = "eternal-bongo-435614-b9"

    url = "https://" + project + ".uc.r.appspot.com/random_questions"

    defaults = (
        "How many districts are there in the California community college system?",
        "What is the part-time enrollment of Foothill College?",
        "What college is designated a Center of Excellence in bioprocessing?",
        "How many California community colleges partner with the California " +
            "Department of Corrections and Rehabilitation (CDCR) to provide in‑person courses?",
        "What are the responsibilities of the board members of a California community college?",
        "Which California community colleges have radio stations?",
        "Which California community colleges have a student run bakery?",
        "Which California community college awarded the most number of bachelor's degrees?"
    )

    questions = []
    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            for question in data["questions"]:
                questions.append(question)
        else:
            questions = defaults

    except requests.exceptions.RequestException as e:
        questions = defaults

    return questions
