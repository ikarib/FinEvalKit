"""Calibrate automated judges against human gold labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_judgments(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def calibrate_judge(
    records: list[dict[str, Any]], confidence_threshold: float = 0.8
) -> dict[str, object]:
    labels = sorted(
        {str(record["human_label"]) for record in records}
        | {str(record["judge_label"]) for record in records}
    )
    confusion = {gold: {pred: 0 for pred in labels} for gold in labels}
    review_queue: list[dict[str, object]] = []
    correct = 0
    for record in records:
        gold = str(record["human_label"])
        predicted = str(record["judge_label"])
        confusion[gold][predicted] += 1
        correct += gold == predicted
        confidence = float(record.get("confidence", 0.0))
        risk = str(record.get("risk", "standard"))
        if (
            gold != predicted
            or confidence < confidence_threshold
            or (risk == "high" and predicted == "pass")
        ):
            review_queue.append(
                {
                    "case_id": record["case_id"],
                    "reason": "disagreement" if gold != predicted else "risk_or_confidence",
                }
            )

    per_label: dict[str, dict[str, float]] = {}
    for label in labels:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[gold][label] for gold in labels if gold != label)
        false_negative = sum(confusion[label][pred] for pred in labels if pred != label)
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        per_label[label] = {"precision": precision, "recall": recall, "f1": f1}

    total = len(records)
    human_counts = Counter(str(record["human_label"]) for record in records)
    judge_counts = Counter(str(record["judge_label"]) for record in records)
    expected = sum(human_counts[label] * judge_counts[label] for label in labels)
    expected = expected / (total * total) if total else 0.0
    accuracy = correct / total if total else 0.0
    kappa = (accuracy - expected) / (1 - expected) if expected < 1 else 1.0
    return {
        "case_count": total,
        "accuracy": accuracy,
        "macro_f1": sum(item["f1"] for item in per_label.values()) / max(len(labels), 1),
        "cohen_kappa": kappa,
        "labels": labels,
        "confusion_matrix": confusion,
        "per_label": per_label,
        "review_queue": review_queue,
        "confidence_threshold": confidence_threshold,
    }
