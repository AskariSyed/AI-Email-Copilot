from app.core.config import settings
from app.services.rag.reranker import rerank_documents


class MockDoc:
    def __init__(self, text):
        self.text = text


def test_reranker_disabled():
    original_setting = settings.ENABLE_RERANKING
    try:
        settings.ENABLE_RERANKING = False
        docs = [MockDoc("A"), MockDoc("B"), MockDoc("C")]

        # Should just return top_k without scoring
        result = rerank_documents("query", docs, lambda d: d.text, top_k=2)
        assert len(result) == 2
        assert result[0].text == "A"
        assert result[1].text == "B"
    finally:
        settings.ENABLE_RERANKING = original_setting


def test_reranker_enabled():
    original_setting = settings.ENABLE_RERANKING
    try:
        settings.ENABLE_RERANKING = True

        docs = [
            MockDoc("The sky is beautiful today."),
            MockDoc("Apples are a very tasty fruit."),
            MockDoc("I love programming in Python."),
        ]

        # Query is about fruit
        query = "Tell me about a delicious fruit."

        # Reranking should put Apples first
        result = rerank_documents(query, docs, lambda d: d.text, top_k=1)

        assert len(result) == 1
        assert "Apples" in result[0].text
    finally:
        settings.ENABLE_RERANKING = original_setting
