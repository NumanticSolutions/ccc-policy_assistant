import os, sys

from google.adk.evaluation.agent_evaluator import AgentEvaluator

import pathlib

import pytest

utils_path = "../../interface/utils"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication

# Set environment variables
dotenv_path = "../../data/environment"
api_configs = ApiAuthentication(dotenv_path=dotenv_path)
# api_configs.set_environ_variables()


# qa_data_path = "../evaluation/rag_tests/data/eval_data"
# qa_data_path = "data"
# qa_adk_file = "ccc_test.test.json"

# print(os.listdir("../"))
# agent_path = "rag"
# print(os.listdir(agent_path))

# def test_with_single_test_file():
#     """Test the agent's basic ability via a session file."""
#     AgentEvaluator.evaluate(
#         agent_module="rag",
#         eval_dataset_file_path_or_dir=os.path.join(qa_data_path, qa_adk_file),
#         num_runs=1
#     )

@pytest.fixture(scope='session', autouse=True)
def load_env():
    # dotenv.load_dotenv()
    api_configs.set_environ_variables()

def test_with_single_test_file():
    """Test the agent's basic ability via a session file."""
    AgentEvaluator.evaluate(
        agent_module="rag",
        eval_dataset_file_path_or_dir=str(pathlib.Path(__file__).parent / "data/ccc_test.test.json"),
        num_runs=1
    )
