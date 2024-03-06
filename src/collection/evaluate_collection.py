from src.collection.query_collection import get_top_k_results
from sentence_transformers import SentenceTransformer
from typing import List
from qdrant_client import QdrantClient
from src.utils.bigquery import query_bigquery
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
EVALUATION_DATASET = os.getenv("EVALUATION_DATASET")


def load_model(model_name: str) -> SentenceTransformer:
    """
    Load the SentenceTransformer model.

    Args:
        model_name (str): The name of the model.

    Returns:
        SentenceTransformer: The loaded model.
    """
    model = SentenceTransformer(model_name)
    return model


def calculate_precision(retrieved_records, relevant_records):
    # Calculate precision
    true_positives = len(retrieved_records.intersection(relevant_records))
    return true_positives / len(retrieved_records) if retrieved_records else 0


def calculate_recall(retrieved_records, relevant_records):
    # Calculate recall
    true_positives = len(retrieved_records.intersection(relevant_records))
    return true_positives / len(relevant_records) if relevant_records else 0


def calculate_f1_score(precision, recall):
    # Calculate F1 score
    return (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )


def get_data_for_evaluation() -> dict:
    """
    Query BQ for labelled feedback data. for use in evaluation.

    Returns:
        list(dict): Feedback data IDs and labels
    """
    query = """
    SELECT
        id,
        ARRAY_TO_STRING(labels, ", ") as labels,
        urgency
    FROM
        @evaluation_dataset
    """
    query = query.replace("@evaluation_dataset", EVALUATION_DATASET)
    data = query_bigquery(
        project_id=PROJECT_ID,
        dataset_id=EVALUATION_DATASET,
        query=query,
    )
    return [data]


def assess_retrieval_accuracy(
    client: QdrantClient, collection_name: str, labels: List[dict], k_threshold: int
) -> None:
    """
    Assess the retrieval accuracy of a collection.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        labels (List[str]): The list of labels.
        k_threshold (int): The threshold for retrieving top K results.

    Returns:
        None
    """

    # Load the model once
    model = load_model("all-mpnet-base-v2")

    # Get unique labels
    unique_labels = set(label["labels"] for label in labels)

    # Retrieve top K results for each label
    for label in unique_labels:
        # Calculate how many ids contain the label from labels["id"] and labels["labels"]
        relevant_records = len(
            set(label["id"] for label in labels if label in label["labels"])
        )

        # Embed the label
        query_embedding = model.encode(label)

        # Retrieve the top K results for the label
        results = get_top_k_results(
            client=client,
            collection_name=collection_name,
            query_embedding=query_embedding,
            k=k_threshold,
            filter_key="label",
            filter_values=[label],
        )

        # Calculate precision, recall, and F1 score using the functions defined above
        precision = calculate_precision(results, relevant_records)
        recall = calculate_recall(results, relevant_records)
        f1_score = calculate_f1_score(precision, recall)

        # Print the results
        print(
            f"Label: {label}, Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}"
        )


if __name__ == "__main__":
    # Initialize a Qdrant client
    client = QdrantClient()

    # Get the data for evaluation
    data = get_data_for_evaluation()

    # Assess the retrieval accuracy
    assess_retrieval_accuracy(
        client=client,
        collection_name="feedback_collection",
        labels=data,
        k_threshold=10,
    )
