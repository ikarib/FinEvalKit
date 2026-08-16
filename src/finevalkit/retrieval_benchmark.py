"""Reproducible lexical, Hugging Face, and hybrid retrieval benchmark."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .models import Chunk
from .retrieval import BM25Retriever, DenseRetriever, HybridRetriever, SentenceTransformerBackend


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def load_benchmark(dataset_dir: str | Path) -> tuple[list[Chunk], list[dict[str, Any]]]:
    root = Path(dataset_dir)
    documents = _load_jsonl(root / "documents.jsonl")
    chunks = [
        Chunk(
            chunk_id=str(item["chunk_id"]),
            document_id=str(item["document_id"]),
            text=str(item["text"]),
            page=item.get("page"),
            modality=str(item.get("modality", "text")),
            source_path=str(root / "documents.jsonl"),
            source_sha256="benchmark-fixture",
        )
        for item in documents
    ]
    return chunks, _load_jsonl(root / "cases.jsonl")


def _score_retriever(retriever: Any, cases: list[dict[str, Any]], top_k: int) -> dict[str, float]:
    reciprocal_ranks: list[float] = []
    recalls: list[float] = []
    latencies: list[float] = []
    for case in cases:
        start = time.perf_counter()
        results = retriever.search(str(case["query"]), top_k=top_k)
        latencies.append((time.perf_counter() - start) * 1000)
        retrieved = [chunk.citation for chunk, _ in results]
        relevant = set(map(str, case["relevant_citations"]))
        recalls.append(len(set(retrieved) & relevant) / len(relevant))
        ranks = [index for index, citation in enumerate(retrieved, start=1) if citation in relevant]
        reciprocal_ranks.append(1 / min(ranks) if ranks else 0.0)
    return {
        f"recall_at_{top_k}": sum(recalls) / len(recalls),
        "mean_reciprocal_rank": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "mean_query_latency_ms": sum(latencies) / len(latencies),
    }


def run_embedding_benchmark(
    dataset_dir: str | Path,
    output_path: str | Path,
    *,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    model_revision: str | None = None,
    top_k: int = 3,
) -> dict[str, object]:
    chunks, cases = load_benchmark(dataset_dir)
    lexical = BM25Retriever(chunks)
    backend = SentenceTransformerBackend(model_name, revision=model_revision, device="cpu")
    dense = DenseRetriever(chunks, backend)
    hybrid = HybridRetriever(lexical, dense)
    report: dict[str, object] = {
        "dataset": "financial_retrieval_benchmark_v1",
        "case_count": len(cases),
        "document_count": len(chunks),
        "model": {
            "provider": "Hugging Face",
            "model_name": model_name,
            "revision": model_revision or "default",
        },
        "top_k": top_k,
        "results": {
            "bm25": _score_retriever(lexical, cases, top_k),
            "dense": _score_retriever(dense, cases, top_k),
            "hybrid": _score_retriever(hybrid, cases, top_k),
        },
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
