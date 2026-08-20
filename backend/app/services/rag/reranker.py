import time
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.rag.reranker")

# Lazily load the model to save memory if reranking is disabled
_cross_encoder_model = None


def get_reranker_model():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        from sentence_transformers import CrossEncoder

        logger.info("Loading CrossEncoder model for reranking...")
        _cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder_model


def rerank_documents(
    query: str, documents: list[Any], extract_text_fn, top_k: int = 5
) -> list[Any]:
    """
    Reranks a list of documents based on relevance to the query using a CrossEncoder.

    Args:
        query: The search query/incoming email context.
        documents: The candidate documents (e.g., EmailChunk objects).
        extract_text_fn: A function that takes a document and returns its string content.
        top_k: The final number of documents to return.

    Returns:
        The top_k documents sorted by relevance.
    """
    if not settings.ENABLE_RERANKING or not documents:
        # Pass-through behavior if disabled or empty
        return documents[:top_k]

    start_time = time.perf_counter()
    model = get_reranker_model()

    # Format inputs as pairs: (query, document_text)
    pairs = [[query, extract_text_fn(doc)] for doc in documents]

    # Get relevance scores
    scores = model.predict(pairs)

    # Combine documents with scores and sort them in descending order
    doc_score_pairs = list(zip(documents, scores))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

    latency_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Reranking {len(documents)} candidates took {latency_ms:.2f}ms", 
        extra={"latency_ms": latency_ms, "candidates_count": len(documents), "top_k": top_k}
    )

    # Extract the original documents from the sorted pairs
    reranked_docs = [doc for doc, score in doc_score_pairs]

    return reranked_docs[:top_k]
