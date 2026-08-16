from finevalkit.models import Chunk
from finevalkit.retrieval import (
    BM25Retriever,
    DenseRetriever,
    HashEmbeddingBackend,
    HybridRetriever,
)


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(chunk_id, "doc", text, 1, "text", "fixture", "hash")


def test_hybrid_retrieval_returns_fused_rankings():
    chunks = [
        _chunk("revenue", "Annual net sales and revenue were 416 billion dollars."),
        _chunk("risk", "Credit risk requires independent escalation and review."),
        _chunk("capital", "Capital ratios measure bank solvency."),
    ]
    lexical = BM25Retriever(chunks)
    dense = DenseRetriever(chunks, HashEmbeddingBackend(dimensions=64))
    hybrid = HybridRetriever(lexical, dense)

    results = hybrid.search("annual revenue", top_k=2)

    assert results[0][0].chunk_id == "revenue"
    assert len(results) == 2


def test_hash_embedding_backend_is_deterministic():
    backend = HashEmbeddingBackend(dimensions=32)
    assert backend.encode(["same text"])[0] == backend.encode(["same text"])[0]
