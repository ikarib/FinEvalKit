"""Privacy, leakage, and audit controls for financial AI datasets."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Iterable

from .models import Chunk


PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"(?<!\d)(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}(?!\d)"),
    "sin_like": re.compile(r"(?<!\d)\d{3}[- ]?\d{3}[- ]?\d{3}(?!\d)"),
}


def scan_pii(text: str) -> dict[str, list[str]]:
    return {name: pattern.findall(text) for name, pattern in PII_PATTERNS.items() if pattern.search(text)}


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    redacted = text
    for name, pattern in PII_PATTERNS.items():
        redacted, count = pattern.subn(f"[REDACTED_{name.upper()}]", redacted)
        if count:
            counts[name] = count
    return redacted, counts


def _normalized_fingerprint(text: str) -> str:
    normalized = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def leakage_report(chunks_by_split: dict[str, Iterable[Chunk]]) -> dict[str, object]:
    locations: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for split, chunks in chunks_by_split.items():
        for chunk in chunks:
            locations[_normalized_fingerprint(chunk.text)].append((split, chunk.citation))
    duplicates = [
        {"locations": values}
        for values in locations.values()
        if len({split for split, _ in values}) > 1
    ]
    return {"cross_split_duplicates": duplicates, "passed": not duplicates}
