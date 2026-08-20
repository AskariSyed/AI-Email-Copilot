def calculate_hit_rate(retrieved_ids: list[int], expected_ids: list[int]) -> float:
    """Returns 1.0 if at least one expected chunk is in the retrieved results, 0.0 otherwise."""
    if not expected_ids:
        return 0.0
    for expected in expected_ids:
        if expected in retrieved_ids:
            return 1.0
    return 0.0


def calculate_mrr(retrieved_ids: list[int], expected_ids: list[int]) -> float:
    """Calculates Mean Reciprocal Rank (MRR)."""
    if not expected_ids:
        return 0.0
    for rank, retrieved_id in enumerate(retrieved_ids, 1):
        if retrieved_id in expected_ids:
            return 1.0 / rank
    return 0.0


def calculate_recall_at_k(retrieved_ids: list[int], expected_ids: list[int]) -> float:
    """Calculates what fraction of the expected chunks were retrieved."""
    if not expected_ids:
        return 0.0
    hits = sum(1 for expected in expected_ids if expected in retrieved_ids)
    return hits / len(expected_ids)


def evaluate_retrieval(retrieved_results: list[dict], expected_ids: list[int]) -> dict:
    """
    Evaluates a single retrieval response.

    Args:
        retrieved_results: List of dicts [{"chunk_id": 1, "distance": 0.12}, ...]
        expected_ids: List of ground truth chunk IDs.

    Returns:
        Dictionary containing deterministic retrieval metrics.
    """
    retrieved_ids = [res["chunk_id"] for res in retrieved_results]

    metrics = {
        "hit_rate": calculate_hit_rate(retrieved_ids, expected_ids),
        "mrr": calculate_mrr(retrieved_ids, expected_ids),
        "recall": calculate_recall_at_k(retrieved_ids, expected_ids),
        "distances": [res.get("distance", 0.0) for res in retrieved_results],
    }

    return metrics
