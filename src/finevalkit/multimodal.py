"""Model-agnostic scoring for chart and document-image QA outputs."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any


def load_multimodal_cases(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def evaluate_multimodal_cases(cases: list[dict[str, Any]]) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for case in cases:
        expected = Decimal(str(case["expected_value"]))
        observed = Decimal(str(case["model_value"]))
        numeric_match = expected == observed
        has_provenance = bool(case.get("source_locator"))
        results.append(
            {
                "case_id": case["case_id"],
                "modality": case["modality"],
                "numeric_match": numeric_match,
                "has_visual_provenance": has_provenance,
                "passed": numeric_match and has_provenance,
            }
        )
    return {
        "case_count": len(results),
        "pass_rate": sum(result["passed"] for result in results) / max(len(results), 1),
        "results": results,
        "scope": "Scores supplied model/VLM outputs; it does not perform model inference.",
    }
