# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for testing the CCC-Bot Rag pipeline
#%%
import os, sys
import json

from langsmith import wrappers, Client
from openai import OpenAI
from langsmith import traceable
from langchain_openai import ChatOpenAI

from typing_extensions import Annotated, TypedDict

########## Change for rag testing
sys.path.insert(0, "utils")
sys.path.insert(0, "../../interface/utils")
from gcp_tools import download_directory_from_gcs
from authentication import ApiAuthentication

sys.path.insert(0, "../../interface/rag")
import rag_bot as rb

class ragTester():
    '''
    Class to test the CCC Bot against dimensions of
    '''

    def __init__(self):
        '''
        Constructor
        '''

        self.chroma_collection_name = "crawl_docs-vai-2"
        self.chat_bot_verbose = False
        self.dot_env_path = "../../data/environment"

        self.evaluators=[self.correctness_grader,
                         self.groundedness_grader,
                         self.relevance_grader,
                         self.retrieval_relevance_grader]
        self.experiment_prefix = "ccc-test1"
        self.max_concurrency = 1

        # Graders
        self.grader_llm_model = "gpt-4o"
        self.grader_llm_temperature = 0

        # Examples
        self.examples_local_data_path = "../../../../Numantic/Archive/ccc-tests/data/qa_ipeds_data"
        self.examples_file_name = "ipeds_qa_1.json"
        self.examples_dataset_name = "ccc-testdata-1"
        self.examples_dataset_description = "A CCC Policy Assistant testing dataset."

        # Set environment API keys
        self.set_environ_vars()

        # Set Langchain components
        self.set_langchain()

        # Instantiate a CCC bot
        self.bot = rb.CCCPolicyAssistant(chroma_collection_name=self.chroma_collection_name,
                                    chat_bot_verbose=self.chat_bot_verbose,
                                    dot_env_path=self.dot_env_path)

        self.metadata={"version": self.bot.version}


    def set_environ_vars(self):
        '''
        Set environment variables
        '''

        # Get creds if needed
        if len(self.dot_env_path) > 0:
            self.creds = ApiAuthentication(dotenv_path=self.dot_env_path)

            # LangSmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_TRACING"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.creds.apis_configs["LANGCHAIN_API_KEY"]
            # Google
            os.environ["GOOGLE_API_KEY"] = self.creds.apis_configs["GOOGLE_API_KEY"]
            # OpenAI
            os.environ["OPEN_API_KEY"] = self.creds.apis_configs["OPENAI_KEY"]

    def set_langchain(self):
        '''
        Set language chain client and wrapper
        '''

        # Langchain testing client
        self.client = Client()

        # Not sure this is needed
        self.openai_client = wrappers.wrap_openai(OpenAI(api_key=os.environ["OPEN_API_KEY"]))

        # Correctness grader LLM
        self.correctness_grader_llm = \
            ChatOpenAI(model=self.grader_llm_model,
                       temperature=self.grader_llm_temperature,
                       api_key=self.creds.apis_configs["OPENAI_KEY"]).with_structured_output(CorrectnessGrade,
                                                                                             method="json_schema",
                                                                                             strict=True)

        # Relevance grader LLM
        self.relevance_grader_llm = \
            ChatOpenAI(model=self.grader_llm_model,
                       temperature=self.grader_llm_temperature,
                       api_key=self.creds.apis_configs["OPENAI_KEY"]).with_structured_output(RelevanceGrade,
                                                                                             method="json_schema",
                                                                                             strict=True)

        # Groundness grader LLM
        self.groundedness_grader_llm = \
            ChatOpenAI(model=self.grader_llm_model,
                       temperature=self.grader_llm_temperature,
                       api_key=self.creds.apis_configs["OPENAI_KEY"]).with_structured_output(GroundedGrade,
                                                                                             method="json_schema",
                                                                                             strict=True)

        # Retrieval relevance grader LLM
        self.retrieval_relevance_grader_llm = \
            ChatOpenAI(model=self.grader_llm_model,
                       temperature=self.grader_llm_temperature,
                       api_key=self.creds.apis_configs["OPENAI_KEY"]).with_structured_output(RetrievalRelevanceGrade,
                                                                                             method="json_schema",
                                                                                             strict=True)

    # Add decorator so this function is traced in LangSmith
    @traceable()
    def rag_bot(self, question: str) -> dict:
        # Get the bot response
        # bot.show_conversation(input_message=inputs["question"])

        self.bot.show_conversation(input_message=question)

        # Combine into a single response
        ai_response = "{}".format(self.bot.ai_response)

        # retrieved_urls = ["- [{}]({})\n".format(up[0], up[1]) for up in bot.retrieved_urls]
        # retrieved_urls = list(set(retrieved_urls))
        #
        # # Create a single string of retrieved URLs
        # res_phrase = ""
        # if len(retrieved_urls) > 0:
        #     res_phrase = "\n\nThese references might be useful: \n{}".format(" ".join(retrieved_urls))
        #
        # # Combine into a single response
        # ai_response = "{} {}".format(bot.ai_response, res_phrase)

        # Add query result response
        if len(self.bot.query_data_result) > 0:
            ai_response = "{}\n{}".format(ai_response, self.bot.query_data_result)

        return {"answer": ai_response, "documents": self.bot.retrieved_docs}

    def correctness_grader(self,
                           inputs: dict,
                           outputs: dict,
                           reference_outputs: dict) -> bool:
        '''
            An evaluator for RAG answer accuracy
        '''

        # Grade prompt
        correctness_instructions = """You are a teacher grading a quiz.

        You will be given a QUESTION, the GROUND TRUTH (correct) ANSWER, and the STUDENT ANSWER.

        Here is the grade criteria to follow:
        (1) Grade the student answers based ONLY on their factual accuracy relative to the ground truth answer.
        (2) Ensure that the student answer does not contain any conflicting statements.
        (3) It is OK if the student answer contains more information than the ground truth answer, as long as it is factually accurate relative to the  ground truth answer.

        Correctness:
        A correctness value of True means that the student's answer meets all of the criteria.
        A correctness value of False means that the student's answer does not meet all of the criteria.

        Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct.

        Avoid simply stating the correct answer at the outset."""

        answers = f"""\
        QUESTION: {inputs['question']}
        GROUND TRUTH ANSWER: {reference_outputs['answer']}
        STUDENT ANSWER: {outputs['answer']}"""

        # Run evaluator
        grade = self.correctness_grader_llm.invoke([
            {"role": "system", "content": correctness_instructions},
            {"role": "user", "content": answers}
        ])
        return grade["correct"]

    def relevance_grader(self, inputs: dict, outputs: dict) -> bool:
        '''
            An evaluator for RAG answer relevance
        '''

        relevance_instructions = """You are a teacher grading a quiz.

        You will be given a QUESTION and a STUDENT ANSWER.

        Here is the grade criteria to follow:
        (1) Ensure the STUDENT ANSWER is concise and relevant to the QUESTION
        (2) Ensure the STUDENT ANSWER helps to answer the QUESTION

        Relevance:
        A relevance value of True means that the student's answer meets all of the criteria.
        A relevance value of False means that the student's answer does not meet all of the criteria.

        Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct.

        Avoid simply stating the correct answer at the outset."""

        answer = f"QUESTION: {inputs['question']}\nSTUDENT ANSWER: {outputs['answer']}"

        grade = self.relevance_grader_llm.invoke([
            {"role": "system", "content": relevance_instructions},
            {"role": "user", "content": answer}
        ])
        return grade["relevant"]

    def groundedness_grader(self, inputs: dict, outputs: dict) -> bool:
        '''
            An evaluator for RAG answer groundedness
        '''

        grounded_instructions = """You are a teacher grading a quiz.

        You will be given FACTS and a STUDENT ANSWER.

        Here is the grade criteria to follow:
        (1) Ensure the STUDENT ANSWER is grounded in the FACTS.
        (2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

        Grounded:
        A grounded value of True means that the student's answer meets all of the criteria.
        A grounded value of False means that the student's answer does not meet all of the criteria.

        Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct.

        Avoid simply stating the correct answer at the outset."""

        doc_string = "\n\n".join(doc.page_content for doc in outputs["documents"])
        answer = f"FACTS: {doc_string}\nSTUDENT ANSWER: {outputs['answer']}"
        grade = self.groundedness_grader_llm.invoke(
            [{"role": "system", "content": grounded_instructions}, {"role": "user", "content": answer}])
        return grade["grounded"]

    def retrieval_relevance_grader(self, inputs: dict, outputs: dict) -> bool:
        '''
            An evaluator for RAG answer groundedness
        '''

        retrieval_relevance_instructions = """You are a teacher grading a quiz.

        You will be given a QUESTION and a set of FACTS provided by the student.

        Here is the grade criteria to follow:
        (1) You goal is to identify FACTS that are completely unrelated to the QUESTION
        (2) If the facts contain ANY keywords or semantic meaning related to the question, consider them relevant
        (3) It is OK if the facts have SOME information that is unrelated to the question as long as (2) is met

        Relevance:
        A relevance value of True means that the FACTS contain ANY keywords or semantic meaning related to the QUESTION and are therefore relevant.
        A relevance value of False means that the FACTS are completely unrelated to the QUESTION.

        Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct.

        Avoid simply stating the correct answer at the outset."""

        doc_string = "\n\n".join(doc.page_content for doc in outputs["documents"])
        answer = f"FACTS: {doc_string}\nQUESTION: {inputs['question']}"

        # Run evaluator
        grade = self.retrieval_relevance_grader_llm.invoke([
            {"role": "system", "content": retrieval_relevance_instructions},
            {"role": "user", "content": answer}
        ])
        return grade["relevant"]
        # return {"score": grade["relevant"], "comment": grade["explanation"]}

    def target(self, inputs: dict) -> dict:
        '''

        '''
        return self.rag_bot(inputs["question"])

    def run_test(self):
        '''
        Run the evaluation test
        '''

        self.experiment_results = self.client.evaluate(self.target,
                                                       data=self.examples_dataset_name,
                                                       evaluators= self.evaluators,
                                                       experiment_prefix=self.experiment_prefix,
                                                       max_concurrency=self.max_concurrency,
                                                       metadata=self.metadata)

        # Get the name
        self.experiment_name = self.experiment_results.experiment_name

        # Get the results in a dataframe
        self.results_df = self.experiment_results.to_pandas()

    def load_example_dataset(self):
        '''
        Method to load the example dataset stored in a JSON file

        '''

        with open(os.path.join(self.examples_local_data_path, self.examples_file_name), "r") as file:
            self.examples_from_file = json.load(file)

    def create_test_examples(self):
        '''
        Method to create the test examples used by LangChain in evaluation
        '''

        # Create a list of dictionaries for inputs and outputs
        inputs = [{"question": input_prompt} for input_prompt, _ in self.examples_from_file]
        outputs = [{"answer": output_answer} for _, output_answer in self.examples_from_file]

        examples = [dict(inputs=i, outputs=o) for i, o in zip(inputs, outputs)]

        # Create the dataset and examples in LangSmith
        dataset = self.client.create_dataset(dataset_name=self.examples_dataset_name)
        self.client.create_examples(dataset_id=dataset.id,
                                    description=self.examples_dataset_description,
                                    examples=examples)

    def delete_test_examples(self):
        '''
        Method to delete a Langchain examples dataset
        '''

        # Delete dataset in LangSmith
        self.client.delete_dataset(dataset_name=self.examples_dataset_name)


# Grade output schema
class CorrectnessGrade(TypedDict):
    # Note that the order in the fields are defined is the order in which the model will generate them.
    # It is useful to put explanations before responses because it forces the model to think through
    # its final response before generating it:
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    correct: Annotated[bool, ..., "True if the answer is correct, False otherwise."]

# Grade output schema
class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "Provide the score on whether the answer addresses the question"]

# Grade output schema
class GroundedGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    grounded: Annotated[bool, ..., "Provide the score on if the answer hallucinates from the documents"]

# Grade output schema
class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "True if the retrieved documents are relevant to the question, False otherwise"]