# from src.utils.utils import load_qdrant_client
from src.utils.utils import load_model
from src.collection_utils.evaluate_collection import process_labels

from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
import asyncio
import os
import pickle
import argparse
import subprocess

load_dotenv()

# Load env variables
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


def load_async_client(qdrant_host: str, port: int) -> AsyncQdrantClient:
    client = AsyncQdrantClient(qdrant_host, port=port)
    return client


async def main(save_outputs: bool = False):
    """
    Main function to get data for analysis and save the outputs as pickle files

    Requirements:
        Pickle files for unique labels and regex_ids. A Qdrant client and an encoder model.
    """
    if not os.path.exists("data/unique_labels.pkl") or not os.path.exists(
        "data/regex_ids.pkl"
    ):
        # run the evaluation/output_pkl.py script
        print("Running evaluation/output_pkl.py ...")
        subprocess.run(
            ["python", "-u", "evaluation/output_pkl.py", "--save_outputs", "True"]
        )

    # Load regex_ids
    with open("data/regex_ids.pkl", "rb") as f:
        regex_ids = pickle.load(f)

    # Load unique labels
    with open("data/unique_labels.pkl", "rb") as f:
        unique_labels = pickle.load(f)

    # Load qdrant client and model
    try:
        qdrant = load_async_client(QDRANT_HOST, port=QDRANT_PORT)
        model = load_model(HF_MODEL_NAME)
    except Exception as e:
        print(f"Error: {e}")

    precision_values, recall_values, f2_scores = await process_labels(
        unique_labels, regex_ids, model, qdrant, COLLECTION_NAME
    )

    # Print first 10 values
    print(precision_values[:10])
    print(recall_values[:10])
    print(f2_scores[:10])

    # pickle precision and recall values if argument is True
    if save_outputs:
        with open("data/precision_values_async.pkl", "wb") as f:
            pickle.dump(precision_values, f)

        with open("data/recall_values_async.pkl", "wb") as f:
            pickle.dump(recall_values, f)

        with open("data/f2_scores_async.pkl", "wb") as f:
            pickle.dump(f2_scores, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_outputs", type=bool, default=False)
    args = parser.parse_args()
    asyncio.run(main(save_outputs=args.save_outputs))
