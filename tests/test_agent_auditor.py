from pathlib import Path

from finevalkit.agent_auditor import (
    evaluate_auditors,
    load_cases,
    run_agent_auditor,
    write_evaluation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_development_set_scores_baseline_alerts_without_inventing_categories():
    report = evaluate_auditors(load_cases(ROOT / "data" / "agent_auditor" / "cases.jsonl"))
    baseline = report["baseline"]["metrics"]
    agent = report["agent_auditor"]["metrics"]
    assert report["run"]["case_count"] == 10
    assert baseline["review_decision"]["recall"] == 1 / 9
    assert baseline["typed_findings"]["supported"] is False
    assert baseline["typed_findings"]["per_category_recall"]["numeric"]["recall"] is None
    assert agent["typed_findings"]["recall"] == 1.0
    assert agent["typed_findings"]["false_negative_count"] == 0


def test_conflict_case_uses_independent_verification_and_requires_human_review():
    case = next(item for item in load_cases(ROOT / "data" / "agent_auditor" / "cases.jsonl") if item["case_id"] == "AA-07-conflict")
    result = run_agent_auditor(case)
    assert result["decision"] == "escalate_to_human"
    verification = next(event for event in result["trajectory"] if event["event"] == "independent_verification")
    assert verification["result"]["status"] == "confirmed"


def test_heldout_cases_cover_adversarial_variants_with_independent_gold_labels(tmp_path):
    heldout = load_cases(ROOT / "data" / "agent_auditor" / "heldout_cases.jsonl")
    assert len(heldout) == 10
    assert all("gold_critical_labels" in case and "gold_review_required" in case for case in heldout)
    report = evaluate_auditors(heldout, "agent_auditor_heldout_v1")
    agent = report["agent_auditor"]["metrics"]
    assert agent["typed_findings"]["recall"] == 1.0
    assert agent["review_decision"]["false_positive_count"] == 0
    written = write_evaluation(ROOT, tmp_path)
    assert written["heldout"]["run"]["case_count"] == 10
    assert (tmp_path / "comparison.json").exists()
