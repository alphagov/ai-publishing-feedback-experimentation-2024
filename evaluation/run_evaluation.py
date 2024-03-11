import os

from src.collection.evaluate_collection import (
    assess_retrieval_accuracy,
    get_data_for_evaluation,
    load_qdrant_client,
)

# Get env vars
PROJECT_ID = os.getenv("PROJECT_ID")
EVALUATION_DATASET = os.getenv("EVALUATION_DATASET")
QDRANT_HOST = os.getenv("QDRANT_HOST")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def main():
    # Initialize a Qdrant client
    client = load_qdrant_client(host=QDRANT_HOST, port=6333)

    # Get the data for evaluation
    data = get_data_for_evaluation(
        project_id=PROJECT_ID,
        evaluation_dataset=EVALUATION_DATASET,
    )

    # Assess the retrieval accuracy
    assess_retrieval_accuracy(
        client=client,
        collection_name=COLLECTION_NAME,
        labels=data,
        k_threshold=10,
    )


if __name__ == "__main__":
    main()