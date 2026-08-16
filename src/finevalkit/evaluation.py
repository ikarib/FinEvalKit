"""Grounding, numerical, retrieval, and OCR quality metrics."""

from __future__ import annotations

import math
import random
import re
from collections.abc import Callable, Sequence
from decimal import Decimal, InvalidOperation

from .models import Chunk, MetricResult
from .retrieval import tokenize


CITATION_RE = re.compile(r"\[([A-Za-z0-9_-]+#[A-Za-z0-9_-]+)\]")
NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:CAD|USD|\$)?\s*-?\d[\d,]*(?:\.\d+)?%?(?![A-Za-z0-9])"
)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "that", "the", "this", "to", "was", "were", "with",
}


def extract_citations(text: str) -> list[str]:
    return CITATION_RE.findall(text)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _content_tokens(text: str) -> set[str]:
    return {token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2}


def citation_validity(answer: str, chunks: Sequence[Chunk]) -> MetricResult:
    available = {chunk.citation for chunk in chunks}
    supplied = extract_citations(answer)
    valid = [citation for citation in supplied if citation in available]
    invalid = sorted(set(supplied) - available)
    score = len(valid) / len(supplied) if supplied else 0.0
    return MetricResult(
        "citation_validity",
        score,
        bool(supplied) and not invalid,
        {"citations": supplied, "invalid": invalid},
    )


def citation_coverage(answer: str) -> MetricResult:
    claim_sentences = [
        sentence
        for sentence in _sentences(answer)
        if NUMBER_RE.search(sentence)
        or any(word in sentence.lower() for word in ("must", "may", "limit", "risk", "requires"))
    ]
    covered = [sentence for sentence in claim_sentences if extract_citations(sentence)]
    score = len(covered) / len(claim_sentences) if claim_sentences else 1.0
    return MetricResult(
        "citation_coverage",
        score,
        score >= 0.8,
        {"claim_count": len(claim_sentences), "covered_count": len(covered)},
    )


def citation_faithfulness(answer: str, chunks: Sequence[Chunk]) -> MetricResult:
    lookup = {chunk.citation: chunk for chunk in chunks}
    scores: list[float] = []
    unsupported: list[str] = []
    for sentence in _sentences(answer):
        citations = extract_citations(sentence)
        if not citations:
            continue
        claim = CITATION_RE.sub("", sentence)
        claim_tokens = _content_tokens(claim)
        evidence_tokens: set[str] = set()
        for citation in citations:
            if citation in lookup:
                evidence_tokens |= _content_tokens(lookup[citation].text)
        overlap = len(claim_tokens & evidence_tokens) / max(len(claim_tokens), 1)
        scores.append(overlap)
        if overlap < 0.35:
            unsupported.append(sentence)
    score = sum(scores) / len(scores) if scores else 0.0
    return MetricResult(
        "citation_faithfulness",
        score,
        bool(scores) and not unsupported,
        {"unsupported_sentences": unsupported, "sentence_scores": scores},
    )


def _normalize_number(raw: str) -> Decimal | None:
    cleaned = re.sub(r"CAD|USD|\$|,|\s", "", raw)
    percent = cleaned.endswith("%")
    cleaned = cleaned.removesuffix("%")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    return value / 100 if percent else value


def numeric_consistency(answer: str, chunks: Sequence[Chunk]) -> MetricResult:
    answer_numbers = {
        value for raw in NUMBER_RE.findall(answer) if (value := _normalize_number(raw)) is not None
    }
    evidence_text = " ".join(chunk.text for chunk in chunks)
    evidence_numbers = {
        value
        for raw in NUMBER_RE.findall(evidence_text)
        if (value := _normalize_number(raw)) is not None
    }
    unsupported = sorted(str(value) for value in answer_numbers - evidence_numbers)
    score = (
        len(answer_numbers & evidence_numbers) / len(answer_numbers) if answer_numbers else 1.0
    )
    return MetricResult(
        "numeric_consistency",
        score,
        not unsupported,
        {"answer_numbers": sorted(map(str, answer_numbers)), "unsupported": unsupported},
    )


def retrieval_recall(retrieved: Sequence[str], relevant: Sequence[str]) -> MetricResult:
    relevant_set = set(relevant)
    hits = relevant_set & set(retrieved)
    score = len(hits) / len(relevant_set) if relevant_set else 1.0
    return MetricResult(
        "retrieval_recall",
        score,
        score >= 0.8,
        {"hits": sorted(hits), "misses": sorted(relevant_set - hits)},
    )


def _edit_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row, ref_item in enumerate(reference, start=1):
        current = [row]
        for column, hyp_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (ref_item != hyp_item),
                )
            )
        previous = current
    return previous[-1]


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = tokenize(reference)
    hyp_words = tokenize(hypothesis)
    return _edit_distance(ref_words, hyp_words) / max(len(ref_words), 1)


def bootstrap_mean_ci(
    values: Sequence[float],
    confidence: float = 0.95,
    samples: int = 2_000,
    seed: int = 42,
) -> tuple[float, float]:
    if not values:
        return (math.nan, math.nan)
    generator = random.Random(seed)
    means = sorted(
        sum(generator.choice(values) for _ in values) / len(values) for _ in range(samples)
    )
    tail = (1 - confidence) / 2
    low = means[int(tail * (samples - 1))]
    high = means[int((1 - tail) * (samples - 1))]
    return (low, high)


def evaluate_answer(answer: str, evidence: Sequence[Chunk]) -> list[MetricResult]:
    evaluators: tuple[Callable[[str, Sequence[Chunk]], MetricResult], ...] = (
        citation_validity,
        citation_faithfulness,
        numeric_consistency,
    )
    results = [evaluator(answer, evidence) for evaluator in evaluators]
    results.append(citation_coverage(answer))
    return results
