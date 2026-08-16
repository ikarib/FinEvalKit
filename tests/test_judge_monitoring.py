from pathlib import Path

from finevalkit.judge import calibrate_judge, load_judgments
from finevalkit.monitoring import categorical_psi, slice_report
from finevalkit.multimodal import evaluate_multimodal_cases, load_multimodal_cases

ROOT = Path(__file__).resolve().parents[1]


def test_judge_calibration_produces_confusion_metrics_and_queue():
    records = load_judgments(ROOT / "data" / "judge_calibration" / "sample_judgments.jsonl")
    report = calibrate_judge(records)

    assert report["case_count"] == 12
    assert 0.0 < report["macro_f1"] < 1.0
    assert {item["case_id"] for item in report["review_queue"]} >= {"judge-006", "judge-011"}


def test_slice_report_and_drift_surface_distribution_changes():
    records = [
        {"modality": "text", "score": 0.9},
        {"modality": "text", "score": 0.8},
        {"modality": "chart", "score": 0.6},
    ]
    report = slice_report(records, "modality")
    drift = categorical_psi(["text", "text", "chart"], ["chart", "chart", "chart"])

    assert report["max_mean_gap"] == 0.25
    assert drift["severity"] == "material_shift"


def test_multimodal_cases_require_numeric_match_and_provenance():
    cases = load_multimodal_cases(ROOT / "data" / "public_filing_fixture" / "chart_qa.jsonl")
    report = evaluate_multimodal_cases(cases)
    assert report["pass_rate"] == 1.0
    assert all(result["has_visual_provenance"] for result in report["results"])
