"""Annotation loading, agreement measurement, and adjudication support."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ALLOWED_LABELS = {"pass", "minor_error", "major_error", "unsafe"}


@dataclass(frozen=True)
class Annotation:
    case_id: str
    annotator_id: str
    label: str
    rationale: str
    evidence_citations: tuple[str, ...]


def load_annotations(path: str | Path) -> list[Annotation]:
    annotations: list[Annotation] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            label = record["label"]
            if label not in ALLOWED_LABELS:
                raise ValueError(f"Invalid label on line {line_number}: {label}")
            annotations.append(
                Annotation(
                    case_id=record["case_id"],
                    annotator_id=record["annotator_id"],
                    label=label,
                    rationale=record["rationale"],
                    evidence_citations=tuple(record.get("evidence_citations", [])),
                )
            )
    return annotations


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b) or not labels_a:
        raise ValueError("Paired, non-empty label sequences are required")
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / len(labels_a)
    counts_a, counts_b = Counter(labels_a), Counter(labels_b)
    labels = set(counts_a) | set(counts_b)
    expected = sum(
        (counts_a[label] / len(labels_a)) * (counts_b[label] / len(labels_b))
        for label in labels
    )
    return 1.0 if expected == 1.0 and observed == 1.0 else (observed - expected) / (1 - expected)


def agreement_report(annotations: Iterable[Annotation]) -> dict[str, object]:
    by_case: dict[str, list[Annotation]] = {}
    for annotation in annotations:
        by_case.setdefault(annotation.case_id, []).append(annotation)
    paired = {
        case_id: sorted(items, key=lambda item: item.annotator_id)
        for case_id, items in by_case.items()
        if len(items) == 2
    }
    labels_a = [items[0].label for items in paired.values()]
    labels_b = [items[1].label for items in paired.values()]
    disagreements = [
        {
            "case_id": case_id,
            "labels": [item.label for item in items],
            "rationales": [item.rationale for item in items],
            "status": "requires_adjudication",
        }
        for case_id, items in paired.items()
        if items[0].label != items[1].label
    ]
    return {
        "paired_cases": len(paired),
        "percent_agreement": sum(a == b for a, b in zip(labels_a, labels_b)) / max(len(paired), 1),
        "cohen_kappa": cohen_kappa(labels_a, labels_b) if paired else None,
        "adjudication_queue": disagreements,
    }
