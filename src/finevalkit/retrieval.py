"""Inspectable lexical, dense, and hybrid retrieval implementations."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from hashlib import sha256
from typing import Protocol

from .models import Chunk

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.%-]*")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.tokens = [tokenize(chunk.text) for chunk in chunks]
        self.term_counts = [Counter(tokens) for tokens in self.tokens]
        self.avg_length = sum(map(len, self.tokens)) / max(len(self.tokens), 1)
        self.document_frequency: Counter[str] = Counter()
        for tokens in self.tokens:
            self.document_frequency.update(set(tokens))

    def _idf(self, term: str) -> float:
        total = len(self.chunks)
        frequency = self.document_frequency[term]
        return math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        query_terms = tokenize(query)
        scores: list[tuple[Chunk, float]] = []
        for chunk, counts, tokens in zip(self.chunks, self.term_counts, self.tokens):
            score = 0.0
            for term in query_terms:
                frequency = counts[term]
                if not frequency:
                    continue
                norm = frequency + self.k1 * (
                    1 - self.b + self.b * len(tokens) / max(self.avg_length, 1)
                )
                score += self._idf(term) * frequency * (self.k1 + 1) / norm
            scores.append((chunk, score))
        return sorted(scores, key=lambda pair: (-pair[1], pair[0].citation))[:top_k]


class EmbeddingBackend(Protocol):
    """Minimal adapter boundary for local or hosted embedding models."""

    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashEmbeddingBackend:
    """Deterministic test backend; useful in CI, not a semantic model."""

    def __init__(self, dimensions: int = 128):
        if dimensions < 8:
            raise ValueError("dimensions must be at least 8")
        self.dimensions = dimensions

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in tokenize(text):
                digest = sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class SentenceTransformerBackend:
    """Optional production-shaped adapter for sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:  # pragma: no cover - optional dependency
            raise RuntimeError("install FinEvalKit with the 'semantic' extra") from error
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


class DenseRetriever:
    def __init__(self, chunks: list[Chunk], backend: EmbeddingBackend):
        self.chunks = chunks
        self.backend = backend
        self.vectors = backend.encode([chunk.text for chunk in chunks])

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        query_vector = self.backend.encode([query])[0]
        scores = [
            (chunk, _cosine(query_vector, vector))
            for chunk, vector in zip(self.chunks, self.vectors)
        ]
        return sorted(scores, key=lambda pair: (-pair[1], pair[0].citation))[:top_k]


class HybridRetriever:
    """Fuse lexical and dense rankings with reciprocal-rank fusion."""

    def __init__(
        self,
        lexical: BM25Retriever,
        dense: DenseRetriever,
        lexical_weight: float = 0.55,
        dense_weight: float = 0.45,
        rrf_k: int = 60,
    ):
        if not math.isclose(lexical_weight + dense_weight, 1.0):
            raise ValueError("retrieval weights must sum to 1")
        self.lexical = lexical
        self.dense = dense
        self.lexical_weight = lexical_weight
        self.dense_weight = dense_weight
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        candidate_count = max(top_k * 4, top_k)
        lexical = self.lexical.search(query, candidate_count)
        dense = self.dense.search(query, candidate_count)
        chunk_by_citation = {chunk.citation: chunk for chunk, _ in [*lexical, *dense]}
        scores: Counter[str] = Counter()
        for rank, (chunk, _) in enumerate(lexical, start=1):
            scores[chunk.citation] += self.lexical_weight / (self.rrf_k + rank)
        for rank, (chunk, _) in enumerate(dense, start=1):
            scores[chunk.citation] += self.dense_weight / (self.rrf_k + rank)
        ranked = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:top_k]
        return [(chunk_by_citation[citation], score) for citation, score in ranked]
