"""Financial-table and OCR evaluation against XBRL ground truth."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .evaluation import NUMBER_RE, _normalize_number
from .xbrl import XBRLFact, latest_facts


@dataclass(frozen=True)
class TableCell:
    concept: str
    period: str
    unit: str
    scale: Decimal
    raw_value: str
    source_locator: str

    @property
    def value(self) -> Decimal | None:
        cleaned = self.raw_value.strip().replace(",", "").replace("$", "")
        if cleaned in {"", "—", "-"}:
            return None
        negative = cleaned.startswith("(") and cleaned.endswith(")")
        cleaned = cleaned.strip("()")
        try:
            value = Decimal(cleaned) * self.scale
        except InvalidOperation:
            return None
        return -value if negative else value

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["scale"] = str(self.scale)
        payload["value"] = str(self.value) if self.value is not None else ""
        return payload


def load_table_cells(path: str | Path) -> list[TableCell]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return [
            TableCell(
                concept=row["concept"],
                period=row["period"],
                unit=row["unit"],
                scale=Decimal(row["scale"]),
                raw_value=row["raw_value"],
                source_locator=row["source_locator"],
            )
            for row in csv.DictReader(stream)
        ]


def evaluate_table(
    cells: list[TableCell], facts: list[XBRLFact], tolerance: Decimal = Decimal(0)
) -> dict[str, object]:
    truth = latest_facts(facts)
    errors: list[dict[str, str]] = []
    matched = 0
    for cell in cells:
        fact = truth.get((cell.concept, cell.period, cell.unit))
        if fact is None:
            errors.append({"concept": cell.concept, "error": "missing_xbrl_fact"})
            continue
        value = cell.value
        if value is None:
            errors.append({"concept": cell.concept, "error": "unparseable_cell"})
        elif abs(value - fact.value) > tolerance:
            ratio = abs(value / fact.value) if fact.value else Decimal(0)
            category = "scale" if ratio in {Decimal(1000), Decimal("0.001")} else "value"
            if value == -fact.value:
                category = "sign"
            errors.append(
                {
                    "concept": cell.concept,
                    "error": category,
                    "observed": str(value),
                    "expected": str(fact.value),
                    "source_locator": cell.source_locator,
                }
            )
        else:
            matched += 1
    total = len(cells)
    return {
        "cell_count": total,
        "matched_cells": matched,
        "exact_accuracy": matched / total if total else 1.0,
        "critical_error_rate": len(errors) / total if total else 0.0,
        "errors": errors,
    }


def ocr_numeric_error_rate(reference: str, hypothesis: str) -> dict[str, object]:
    """Measure critical numeric corruption separately from generic WER."""

    def numbers(text: str) -> list[Decimal]:
        values: list[Decimal] = []
        for raw in NUMBER_RE.findall(text):
            value = _normalize_number(raw)
            if value is not None:
                values.append(value)
        return values

    reference_values = numbers(reference)
    hypothesis_values = numbers(hypothesis)
    mismatches = sum(
        left != right for left, right in zip(reference_values, hypothesis_values)
    ) + abs(len(reference_values) - len(hypothesis_values))
    return {
        "reference_values": [str(value) for value in reference_values],
        "hypothesis_values": [str(value) for value in hypothesis_values],
        "numeric_error_count": mismatches,
        "numeric_error_rate": mismatches / max(len(reference_values), 1),
    }
