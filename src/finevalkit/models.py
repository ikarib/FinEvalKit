"""Typed domain models shared by the evaluation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    page: int | None
    modality: str
    source_path: str
    source_sha256: str
    extraction_status: str = "native_text"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def citation(self) -> str:
        return f"{self.document_id}#{self.chunk_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    question: str
    answer: str
    retrieved_citations: tuple[str, ...]
    expected_behavior: str = "answer"


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
