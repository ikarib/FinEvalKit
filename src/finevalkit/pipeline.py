"""End-to-end reproducible demo pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .agent_eval import ToolAction, evaluate_trace
from .annotation import agreement_report, load_annotations
from .evaluation import bootstrap_mean_ci, evaluate_answer, retrieval_recall, word_error_rate
from .governance import leakage_report, scan_pii
from .ingest import ingest_directory, provenance_manifest
from .retrieval import BM25Retriever


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def run_demo(project_root: str | Path, output_dir: str | Path) -> dict[str, object]:
    root = Path(project_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    chunks = ingest_directory(root / "data" / "source_documents")
    retriever = BM25Retriever(chunks)
    cases = _load_jsonl(root / "data" / "evaluation_cases.jsonl")
    case_reports: list[dict[str, object]] = []
    aggregate_scores: list[float] = []

    for case in cases:
        retrieved = retriever.search(str(case["question"]), top_k=3)
        evidence = [chunk for chunk, _ in retrieved]
        metrics = evaluate_answer(str(case["answer"]), evidence)
        metrics.append(
            retrieval_recall(
                [chunk.citation for chunk in evidence],
                list(case["relevant_citations"]),
            )
        )
        score = sum(metric.score for metric in metrics) / len(metrics)
        aggregate_scores.append(score)
        case_reports.append(
            {
                "case_id": case["case_id"],
                "question": case["question"],
                "retrieved": [
                    {"citation": chunk.citation, "score": round(rank_score, 4)}
                    for chunk, rank_score in retrieved
                ],
                "metrics": [metric.to_dict() for metric in metrics],
                "mean_score": score,
            }
        )

    annotations = load_annotations(root / "data" / "annotations" / "sample_annotations.jsonl")
    agent_traces = _load_jsonl(root / "data" / "agent_traces.jsonl")
    trace_reports = [
        {
            "trace_id": trace["trace_id"],
            **evaluate_trace([ToolAction(**action) for action in trace["actions"]]),
        }
        for trace in agent_traces
    ]
    ci_low, ci_high = bootstrap_mean_ci(aggregate_scores)
    ocr_reference = "Revenue was CAD 125.4 million and operating margin was 18.2 percent."
    ocr_hypothesis = "Revenue was CAD 125.4 million and operating rnargin was 18.2 percent."

    report: dict[str, object] = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset": "synthetic_financial_documents_v1",
            "case_count": len(cases),
            "deterministic": True,
        },
        "summary": {
            "mean_case_score": sum(aggregate_scores) / max(len(aggregate_scores), 1),
            "bootstrap_95_percent_ci": [ci_low, ci_high],
            "passed_cases": sum(
                all(metric["passed"] for metric in case["metrics"]) for case in case_reports
            ),
        },
        "case_reports": case_reports,
        "annotation_quality": agreement_report(annotations),
        "ocr_quality": {
            "word_error_rate": word_error_rate(ocr_reference, ocr_hypothesis),
            "threshold": 0.05,
        },
        "agent_safety": trace_reports,
        "governance": {
            "provenance_manifest": provenance_manifest(chunks),
            "pii_findings": {
                chunk.citation: scan_pii(chunk.text) for chunk in chunks if scan_pii(chunk.text)
            },
            "leakage": leakage_report({"evaluation": chunks, "holdout": []}),
        },
    }

    (output / "evaluation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output / "evaluation_report.md").write_text(_markdown_report(report), encoding="utf-8")
    return report


def _markdown_report(report: dict[str, object]) -> str:
    summary = report["summary"]
    annotation = report["annotation_quality"]
    safety = report["agent_safety"]
    lines = [
        "# FinEvalKit Evaluation Report",
        "",
        f"- Cases: {report['run']['case_count']}",
        f"- Mean score: {summary['mean_case_score']:.3f}",
        f"- 95% bootstrap CI: [{summary['bootstrap_95_percent_ci'][0]:.3f}, "
        f"{summary['bootstrap_95_percent_ci'][1]:.3f}]",
        f"- Cohen's kappa: {annotation['cohen_kappa']:.3f}",
        f"- Agent traces passing policy: {sum(item['passed'] for item in safety)}/{len(safety)}",
        "",
        "## Case results",
        "",
        "| Case | Mean score | All checks passed |",
        "|---|---:|:---:|",
    ]
    for case in report["case_reports"]:
        passed = all(metric["passed"] for metric in case["metrics"])
        lines.append(f"| {case['case_id']} | {case['mean_score']:.3f} | {'Yes' if passed else 'No'} |")
    lines.extend(
        [
            "",
            "## Review queues",
            "",
            f"- Annotation disagreements: {len(annotation['adjudication_queue'])}",
            f"- Agent policy violations: {sum(item['violation_count'] for item in safety)}",
            "",
            "This demonstration uses synthetic data and deterministic heuristics. "
            "The metrics are evaluation instrumentation, not evidence that a model is safe for production.",
        ]
    )
    return "\n".join(lines) + "\n"
