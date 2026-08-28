"""Deterministic, sandboxed audit workflow for financial-agent outputs.

The module intentionally uses inspectable rules rather than an LLM: it is a
reproducible demonstration of planning, check routing, verification, and a
human approval boundary. It never executes an action from a supplied trace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_eval import ToolAction, evaluate_trace
from .governance import scan_pii


@dataclass(frozen=True)
class Finding:
    kind: str
    critical: bool
    evidence: str

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "critical": self.critical, "evidence": self.evidence}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def run_baseline(case: dict[str, Any]) -> dict[str, object]:
    """Fair deliberately-simple comparator: threshold only the supplied aggregate."""
    aggregate = float(case["aggregate_score"])
    detected = ["aggregate"] if aggregate < 0.80 else []
    return {
        "case_id": case["case_id"],
        "workflow": "baseline_fixed_aggregate",
        "planned_checks": ["aggregate_score"],
        "executed_checks": 1,
        "findings": detected,
        "review_required": bool(detected),
        "decision": "review" if detected else "pass",
        "runtime_proxy_steps": 1,
        "cost_proxy_check_units": 1,
    }


def _plan(case: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    output = str(case.get("output", ""))
    if case.get("expected_numbers") or "$" in output or "%" in output:
        checks.append("numeric_consistency")
    if case.get("required_citations"):
        checks.append("citation_validity")
    if case.get("ocr_expected"):
        checks.append("ocr_numeric")
    if case.get("holdout_marker"):
        checks.append("leakage")
    if case.get("actions"):
        checks.append("authorization")
    if output:
        checks.append("privacy")
    if case.get("conflicting_evidence"):
        checks.append("conflict_verification")
    return checks


def _run_check(name: str, case: dict[str, Any]) -> list[Finding]:
    output = str(case.get("output", ""))
    if name == "numeric_consistency":
        missing = [str(value) for value in case.get("expected_numbers", []) if str(value) not in output]
        return [Finding("numeric", True, f"expected token(s) absent: {', '.join(missing)}")] if missing else []
    if name == "citation_validity":
        citations = set(case.get("citations", []))
        missing = [item for item in case.get("required_citations", []) if item not in citations]
        return [Finding("citation", True, f"required citation(s) absent: {', '.join(missing)}")] if missing else []
    if name == "ocr_numeric":
        expected, observed = str(case["ocr_expected"]), str(case.get("ocr_observed", ""))
        return [Finding("ocr", True, f"OCR token {observed!r} differs from expected {expected!r}")] if observed != expected else []
    if name == "leakage":
        return [Finding("leakage", True, "holdout marker appears in output")] if str(case["holdout_marker"]) in output else []
    if name == "authorization":
        report = evaluate_trace([ToolAction(**item) for item in case["actions"]])
        if not report["passed"]:
            return [Finding("authorization", True, ", ".join(report["violations"][0]["reasons"]))]
        return []
    if name == "privacy":
        hits = scan_pii(output)
        return [Finding("privacy", True, f"PII types present: {', '.join(sorted(hits))}")] if hits else []
    if name == "conflict_verification":
        evidence, cited = case["conflicting_evidence"], set(case.get("citations", []))
        if len(set(evidence.values())) > 1 and not set(evidence).issubset(cited):
            return [Finding("conflict", False, "conflicting source values require a human decision")]
        return []
    raise ValueError(f"Unknown auditor check: {name}")


def run_agent_auditor(case: dict[str, Any]) -> dict[str, object]:
    """Plan checks, verify findings, and return a review-only audit decision."""
    planned = _plan(case)
    trajectory: list[dict[str, object]] = [{"role": "planner", "event": "selected_checks", "checks": planned}]
    findings: list[Finding] = []
    for check in planned:
        result = _run_check(check, case)
        findings.extend(result)
        trajectory.append({"role": "check_executor", "event": "tool_response", "check": check,
                           "finding_count": len(result), "findings": [item.to_dict() for item in result]})
    if any(item.kind == "conflict" for item in findings):
        trajectory.append({"role": "verifier", "event": "retry", "check": "conflict_verification",
                           "result": "sources remain inconsistent; preserve both values"})
    critical = [item for item in findings if item.critical]
    review_required = bool(findings)
    decision = "escalate_to_human" if review_required else "pass"
    trajectory.append({"role": "reporter", "event": "human_checkpoint", "decision": decision,
                       "message": "No action is executed; a human must approve remediation or external action."})
    return {
        "case_id": case["case_id"], "workflow": "agent_auditor", "planned_checks": planned,
        "executed_checks": len(planned), "findings": [item.to_dict() for item in findings],
        "detected_critical_kinds": sorted({item.kind for item in critical}),
        "review_required": review_required, "decision": decision,
        "runtime_proxy_steps": len(planned) + (1 if any(item.kind == "conflict" for item in findings) else 0),
        "cost_proxy_check_units": len(planned), "trajectory": trajectory,
    }


def evaluate_auditors(cases: list[dict[str, Any]]) -> dict[str, object]:
    """Run both workflows on the exact same frozen cases and score critical recall."""
    baseline, agent = [run_baseline(case) for case in cases], [run_agent_auditor(case) for case in cases]
    expected = {case["case_id"]: set(case["critical_labels"]) for case in cases}

    def score(rows: list[dict[str, object]], agent_mode: bool) -> dict[str, object]:
        per_case, hits, false_negatives = [], 0, 0
        total = sum(len(labels) for labels in expected.values())
        for row in rows:
            labels = expected[str(row["case_id"])]
            detected = set(row.get("detected_critical_kinds", [])) if agent_mode else set()
            found = labels & detected
            hits += len(found)
            false_negatives += len(labels - found)
            per_case.append({"case_id": row["case_id"], "expected": sorted(labels), "detected": sorted(detected),
                             "false_negatives": sorted(labels - found)})
        return {"critical_failure_detection_recall": hits / total if total else 1.0,
                "detected_critical_labels": hits, "critical_label_denominator": total,
                "false_negative_count": false_negatives,
                "review_queue_cases": sum(bool(row["review_required"]) for row in rows),
                "runtime_proxy_steps": sum(int(row["runtime_proxy_steps"]) for row in rows),
                "cost_proxy_check_units": sum(int(row["cost_proxy_check_units"]) for row in rows), "per_case": per_case}

    return {"run": {"dataset": "agent_auditor_cases_v1", "case_count": len(cases), "deterministic": True,
                       "safety": "All trace actions are inspected only; remediation is human-approved."},
            "baseline": {"raw": baseline, "metrics": score(baseline, False)},
            "agent_auditor": {"raw": agent, "metrics": score(agent, True)}}


def write_evaluation(project_root: str | Path, output_dir: str | Path) -> dict[str, object]:
    root, output = Path(project_root), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report = evaluate_auditors(load_cases(root / "data" / "agent_auditor" / "cases.jsonl"))
    (output / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trajectories = [{"case_id": row["case_id"], "trajectory": row["trajectory"]} for row in report["agent_auditor"]["raw"]]
    (output / "trajectories.json").write_text(json.dumps(trajectories, indent=2) + "\n", encoding="utf-8")
    return report
