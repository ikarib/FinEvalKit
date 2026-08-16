from pathlib import Path

from finevalkit.table_eval import evaluate_table, load_table_cells
from finevalkit.xbrl import load_companyfacts

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "ifrs_filing_fixture"


def test_ifrs_20f_facts_reconcile_to_statement_table():
    facts = load_companyfacts(FIXTURE / "companyfacts_reduced.json", forms=("20-F",))
    report = evaluate_table(load_table_cells(FIXTURE / "statement_table.csv"), facts)

    assert {fact.taxonomy for fact in facts} == {"ifrs-full"}
    assert len(facts) == 3
    assert report["exact_accuracy"] == 1.0
