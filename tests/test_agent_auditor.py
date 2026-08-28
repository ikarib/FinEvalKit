from pathlib import Path

from finevalkit.agent_auditor import evaluate_auditors, load_cases, run_agent_auditor

ROOT = Path(__file__).resolve().parents[1]


def test_agent_auditor_detects_all_frozen_critical_labels():
    report = evaluate_auditors(load_cases(ROOT / "data" / "agent_auditor" / "cases.jsonl"))
    baseline = report["baseline"]["metrics"]
    agent = report["agent_auditor"]["metrics"]
    assert report["run"]["case_count"] == 10
    assert baseline["critical_failure_detection_recall"] == 0.0
    assert agent["critical_failure_detection_recall"] == 1.0
    assert agent["false_negative_count"] == 0


def test_conflict_case_retries_and_requires_human_review():
    case = next(item for item in load_cases(ROOT / "data" / "agent_auditor" / "cases.jsonl") if item["case_id"] == "AA-07-conflict")
    result = run_agent_auditor(case)
    assert result["decision"] == "escalate_to_human"
    assert any(event["event"] == "retry" for event in result["trajectory"])
