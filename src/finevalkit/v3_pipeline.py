"""v0.3 demonstration: OCR execution, IFRS/XBRL, and ISO 20022 controls."""

from __future__ import annotations

import json
from pathlib import Path

from .iso20022 import evaluate_payment_controls, parse_pacs008
from .observability import JsonlTracker, RunContext
from .ocr_engine import TesseractOCR, evaluate_ocr_result
from .table_eval import evaluate_table, load_table_cells
from .xbrl import load_companyfacts


def run_v3_demo(project_root: str | Path, output_dir: str | Path) -> dict[str, object]:
    root = Path(project_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    ifrs_fixture = root / "data" / "ifrs_filing_fixture"
    ifrs_facts = load_companyfacts(ifrs_fixture / "companyfacts_reduced.json", forms=("20-F",))
    ifrs_table = evaluate_table(load_table_cells(ifrs_fixture / "statement_table.csv"), ifrs_facts)

    message = parse_pacs008(root / "data" / "iso20022" / "pacs008_valid.xml")
    payment_authorized = evaluate_payment_controls(
        message, authorization_present=True, confirmation_present=True
    )
    payment_blocked = evaluate_payment_controls(
        message, authorization_present=False, confirmation_present=False
    )

    ocr_fixture = root / "data" / "ocr_fixture"
    reference = (ocr_fixture / "filing_table_gold.txt").read_text(encoding="utf-8").strip()
    ocr_result = TesseractOCR().extract(ocr_fixture / "filing_table_scan.png")
    ocr_evaluation = evaluate_ocr_result(ocr_result, reference)

    report: dict[str, object] = {
        "run": {
            "dataset_version": "ifrs_iso20022_ocr_v1",
            "model_version": ocr_result.engine_version,
            "prompt_version": "not-applicable",
            "code_version": "finevalkit-v0.3.0",
            "policy_version": "3.0",
        },
        "ocr": ocr_evaluation,
        "ifrs_xbrl": {
            "issuer": "Infosys Limited",
            "filing": "2025 Form 20-F",
            "taxonomy": sorted({fact.taxonomy for fact in ifrs_facts}),
            "fact_count": len(ifrs_facts),
            "table_evaluation": ifrs_table,
        },
        "iso20022": {
            "message": message.to_dict(),
            "authorized_trace": payment_authorized,
            "blocked_trace": payment_blocked,
            "validation_scope": "pacs.008.001.14 structural profile; not full official XSD validation",
        },
    }
    (output / "v3_evaluation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    context = RunContext(run_id="offline-v3-demo", **report["run"])
    JsonlTracker(output / "experiment_events.jsonl").log(
        context,
        "v3_evaluation_complete",
        {
            "ocr_wer": ocr_evaluation["word_error_rate"],
            "ocr_numeric_error_rate": ocr_evaluation["numeric"]["numeric_error_rate"],
            "ifrs_table_accuracy": ifrs_table["exact_accuracy"],
            "unauthorized_payment_blocked": not payment_blocked["passed"],
        },
    )
    return report
