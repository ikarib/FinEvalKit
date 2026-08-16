"""Offline v0.2 demonstration covering the remaining evaluation gaps."""

from __future__ import annotations

import json
from pathlib import Path

from .ingest import ingest_directory
from .judge import calibrate_judge, load_judgments
from .monitoring import categorical_psi, slice_report
from .multimodal import evaluate_multimodal_cases, load_multimodal_cases
from .observability import JsonlTracker, RunContext
from .retrieval import BM25Retriever, DenseRetriever, HashEmbeddingBackend, HybridRetriever
from .table_eval import evaluate_table, load_table_cells, ocr_numeric_error_rate
from .xbrl import load_companyfacts


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def run_v2_demo(project_root: str | Path, output_dir: str | Path) -> dict[str, object]:
    root = Path(project_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    policy = json.loads((root / "config" / "evaluation_policy.json").read_text(encoding="utf-8"))
    thresholds = policy["thresholds"]

    fixture = root / "data" / "public_filing_fixture"
    facts = load_companyfacts(fixture / "companyfacts_reduced.json")
    table_report = evaluate_table(load_table_cells(fixture / "statement_table.csv"), facts)
    ocr_report = ocr_numeric_error_rate(
        "Total net sales were $416,161 million; net income was $112,010 million.",
        "Total net sales were $416,161 million; net income was $112,010 million.",
    )
    multimodal_report = evaluate_multimodal_cases(load_multimodal_cases(fixture / "chart_qa.jsonl"))

    chunks = ingest_directory(root / "data" / "source_documents")
    lexical = BM25Retriever(chunks)
    dense = DenseRetriever(chunks, HashEmbeddingBackend())
    hybrid = HybridRetriever(lexical, dense)
    query = "What annual revenue did the company report?"
    retrieval = {
        "query": query,
        "backend": "BM25 + deterministic hash embedding (CI test backend)",
        "results": [
            {"citation": chunk.citation, "score": score}
            for chunk, score in hybrid.search(query, top_k=3)
        ],
    }

    calibration = calibrate_judge(
        load_judgments(root / "data" / "judge_calibration" / "sample_judgments.jsonl"),
        confidence_threshold=float(thresholds["judge_confidence_review_below"]),
    )
    monitoring = _load_jsonl(root / "data" / "monitoring" / "evaluation_runs.jsonl")
    current = [record for record in monitoring if record["window"] == "current"]
    baseline = [record for record in monitoring if record["window"] == "baseline"]
    monitoring_report = {
        "modality_slices": slice_report(
            current, "modality", pass_threshold=float(thresholds["evaluation_pass_score"])
        ),
        "workflow_slices": slice_report(
            current, "workflow", pass_threshold=float(thresholds["evaluation_pass_score"])
        ),
        "modality_drift": categorical_psi(
            [str(record["modality"]) for record in baseline],
            [str(record["modality"]) for record in current],
            review_threshold=float(thresholds["categorical_psi_review_above"]),
            material_threshold=float(thresholds["categorical_psi_material_above"]),
        ),
    }

    report = {
        "run": {
            "dataset_version": "public_filing_reduced_v1+calibration_v1",
            "model_version": "offline-deterministic-baseline",
            "prompt_version": "judge-rubric-v1",
            "code_version": "finevalkit-v0.2.0",
            "policy_version": policy["version"],
        },
        "public_filing": {
            "issuer": "Apple Inc.",
            "filing": "2025 Form 10-K",
            "xbrl_fact_count": len(facts),
            "table_evaluation": table_report,
            "ocr_numeric_evaluation": ocr_report,
            "multimodal_evaluation": multimodal_report,
        },
        "hybrid_retrieval": retrieval,
        "judge_calibration": calibration,
        "monitoring": monitoring_report,
        "policy_checks": {
            "table_accuracy": table_report["exact_accuracy"]
            >= float(thresholds["table_exact_accuracy_min"]),
            "ocr_numeric_error": ocr_report["numeric_error_rate"]
            <= float(thresholds["ocr_numeric_error_rate_max"]),
            "judge_macro_f1": calibration["macro_f1"]
            >= float(thresholds["judge_macro_f1_review_below"]),
            "slice_gap_requires_review": monitoring_report["modality_slices"]["max_mean_gap"]
            > float(thresholds["slice_mean_gap_review_above"]),
        },
    }
    report_path = output / "v2_evaluation_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    context = RunContext(run_id="offline-v2-demo", **report["run"])
    tracker = JsonlTracker(output / "experiment_events.jsonl")
    tracker.log(
        context,
        "evaluation_complete",
        {
            "table_accuracy": table_report["exact_accuracy"],
            "judge_macro_f1": calibration["macro_f1"],
            "review_queue_size": len(calibration["review_queue"]),
        },
    )
    return report
