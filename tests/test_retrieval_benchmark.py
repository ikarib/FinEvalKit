from pathlib import Path

from finevalkit.retrieval import BM25Retriever
from finevalkit.retrieval_benchmark import _score_retriever, load_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_retrieval_benchmark_fixture_and_metrics():
    chunks, cases = load_benchmark(ROOT / "data" / "retrieval_benchmark")
    report = _score_retriever(BM25Retriever(chunks), cases, top_k=3)

    assert len(chunks) == 8
    assert len(cases) == 8
    assert 0.0 <= report["recall_at_3"] <= 1.0
    assert 0.0 <= report["mean_reciprocal_rank"] <= 1.0
