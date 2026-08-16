from decimal import Decimal
from pathlib import Path

from finevalkit.table_eval import (
    TableCell,
    evaluate_table,
    load_table_cells,
    ocr_numeric_error_rate,
)
from finevalkit.xbrl import load_companyfacts

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "public_filing_fixture"


def test_companyfacts_and_table_fixture_reconcile():
    facts = load_companyfacts(FIXTURE / "companyfacts_reduced.json")
    report = evaluate_table(load_table_cells(FIXTURE / "statement_table.csv"), facts)

    assert len(facts) == 4
    assert report["exact_accuracy"] == 1.0
    assert report["errors"] == []


def test_table_evaluation_classifies_scale_error():
    facts = load_companyfacts(FIXTURE / "companyfacts_reduced.json")
    bad_cell = TableCell(
        concept="NetIncomeLoss",
        period="2025-09-27",
        unit="USD",
        scale=Decimal(1000),
        raw_value="112010",
        source_locator="test-cell",
    )

    report = evaluate_table([bad_cell], facts)

    assert report["exact_accuracy"] == 0.0
    assert report["errors"][0]["error"] == "scale"


def test_ocr_numeric_error_is_separate_from_text_errors():
    report = ocr_numeric_error_rate(
        "Revenue was $416,161 million.", "Revenue was $416,761 million."
    )
    assert report["numeric_error_count"] == 1
    assert report["numeric_error_rate"] == 1.0
