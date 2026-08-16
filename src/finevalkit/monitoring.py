"""Slice quality and input-distribution drift monitoring."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

from .evaluation import bootstrap_mean_ci


def slice_report(
    records: Iterable[dict[str, Any]],
    slice_field: str,
    score_field: str = "score",
    pass_threshold: float = 0.8,
) -> dict[str, object]:
    groups: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        groups[str(record[slice_field])].append(float(record[score_field]))
    slices: dict[str, dict[str, object]] = {}
    means: list[float] = []
    for name, values in sorted(groups.items()):
        mean = sum(values) / len(values)
        low, high = bootstrap_mean_ci(values, samples=500)
        means.append(mean)
        slices[name] = {
            "count": len(values),
            "mean": mean,
            "pass_rate": sum(value >= pass_threshold for value in values) / len(values),
            "bootstrap_95_percent_ci": [low, high],
        }
    return {
        "slice_field": slice_field,
        "slices": slices,
        "max_mean_gap": round(max(means) - min(means), 12) if means else 0.0,
        "pass_threshold": pass_threshold,
        "interpretation": "A gap is a review signal, not by itself a fairness conclusion.",
    }


def categorical_psi(
    baseline: Iterable[str],
    current: Iterable[str],
    epsilon: float = 1e-6,
    review_threshold: float = 0.1,
    material_threshold: float = 0.25,
) -> dict[str, object]:
    baseline_values = list(baseline)
    current_values = list(current)
    baseline_counts = Counter(baseline_values)
    current_counts = Counter(current_values)
    categories = sorted(set(baseline_counts) | set(current_counts))
    contributions: dict[str, float] = {}
    for category in categories:
        expected = baseline_counts[category] / max(len(baseline_values), 1)
        actual = current_counts[category] / max(len(current_values), 1)
        expected = max(expected, epsilon)
        actual = max(actual, epsilon)
        contributions[category] = (actual - expected) * math.log(actual / expected)
    psi = sum(contributions.values())
    severity = (
        "stable"
        if psi < review_threshold
        else "review"
        if psi < material_threshold
        else "material_shift"
    )
    return {
        "psi": psi,
        "severity": severity,
        "thresholds": {"review": review_threshold, "material": material_threshold},
        "contributions": contributions,
    }
