"""Small, inspectable BM25 retriever for deterministic demonstrations."""

from __future__ import annotations

import math
import re
from collections import Counter

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
