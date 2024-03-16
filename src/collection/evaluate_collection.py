from src.collection.query_collection import get_top_k_results
from sentence_transformers import SentenceTransformer
from typing import List
from qdrant_client import QdrantClient
from src.utils.bigquery import query_bigquery
import regex as re


def load_qdrant_client(qdrant_host: str, port: int) -> QdrantClient:
    client = QdrantClient(qdrant_host, port=port)
    return client


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


def calculate_precision(retrieved_records: list, relevant_records: int) -> float:
    """
    Calculate precision

    Args:
        retrieved_records (int): Number of retrieved records
        relevant_records (int): Number of relevant records

    Returns:
        float: Precision
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    print(f"true_positives: {true_positives}")
    return true_positives / len(retrieved_records) if retrieved_records else 0


def calculate_recall(retrieved_records: dict, relevant_records: int) -> float:
    """
    Calculate recall

    Args:
        retrieved_records (int): Number of retrieved records
        relevant_records (int): Number of relevant records

    Returns:
        float: Recall
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    return true_positives / len(relevant_records) if relevant_records else 0


def calculate_f1_score(precision: dict, recall: int) -> float:
    """
    Calculate F1 score

    Args:
        precision (float): Precision
        recall (float): Recall

    Returns:
        float: F1 score
    """
    return (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )


def get_data_for_evaluation(
    evaluation_table: str,
    project_id: str,
) -> dict:
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
        @evaluation_table
    """
    query = query.replace("@evaluation_table", evaluation_table)
    data = query_bigquery(
        project_id=project_id,
        query=query,
    )
    return data  # TODO: Check if this is the correct return type


def get_all_labels(data: List[dict]) -> str:
    """
    Get all labels from the feedback data.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[str]: The list of labels.
    """
    labels = []
    for record in data:
        for label in record["labels"].split(","):
            labels.append(label)
    return " ".join(labels)


def get_unique_labels(data: List[dict]) -> List[str]:
    """
    Get unique labels from the feedback data.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[str]: The list of unique labels.
    """
    unique_labels = set()
    for record in data:
        for label in record["labels"].split(","):
            unique_labels.add(label)
    return list(unique_labels)


def get_regex_comparison(label: str, all_labels: str) -> int:
    """
    Given 1 label, use re.findall to get a regex count of how many records would
    be returned if we search for it.

    Args:
        label (str): A unique label to search for.
        all_labels (str): All labels joined together via \s.

    Returns:
        int: The number of matches.
    """
    matches = len(re.findall(label, all_labels, flags=re.IGNORECASE))
    return {"label": label, "n_matches": matches}


def get_all_regex_counts(data: List[dict]) -> dict:
    """
    Get the regex counts for all labels.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[dict]: The list of regex counts.
    """
    all_labels = get_all_labels(data)  # Get single string of all labels
    unique_labels = get_unique_labels(data)  # Get list of unique labels
    regex_counts = {}  # Initialise dict to store label and regex counts
    for unique_label in unique_labels:  # Loop through unique labels
        count = get_regex_comparison(unique_label, all_labels)  # Get regex count
        regex_counts[unique_label] = count  # Store in dict
    return regex_counts


def assess_retrieval_accuracy(
    client: QdrantClient,
    collection_name: str,
    data: List[dict],
    k_threshold: int,
) -> None:
    """
    Assess the retrieval accuracy of a collection.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        data (List[dict]): The list of id, labels, and urgency.
        k_threshold (int): The threshold for retrieving top K results.

    Returns:
        None
    """

    # Load the model once
    model = load_model("all-mpnet-base-v2")

    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Retrieve top K results for each label
    for unique_label in unique_labels:
        # Calculate how many ids contain the label from labels["id"] and labels["labels"]
        relevant_records = [
            int(label["id"]) for label in data if unique_label in label["labels"]
        ]

        # Embed the label
        query_embedding = model.encode(unique_label)

        # Retrieve the top K results for the label
        try:
            results = get_top_k_results(
                client=client,
                collection_name=collection_name,
                query_embedding=query_embedding,
                k=k_threshold,
                filter_key="labels",
                filter_values=[unique_label],
            )
            for scored_point in results:
                payload = scored_point.payload
                print(
                    f"{payload["feedback_record_id"]}: {payload["labels"]}, {payload["response_value"]}"
                )
        except Exception as e:
            print(f"get_top_k_results error: {e}")
            continue

        result_ids = [result.id for result in results]
        print(result_ids, relevant_records)
        # Calculate precision, recall, and F1 score using the functions defined above
        precision = calculate_precision(result_ids, relevant_records)
        recall = calculate_recall(result_ids, relevant_records)
        f1_score = calculate_f1_score(precision, recall)

        # Print the results
        print(
            f"Label: {unique_label}, Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}"
        )


# TODO: Calculate Average Precision, Recall, and F1 Score
# TODO: Use micro or macro precision, recall, and F1 score?
