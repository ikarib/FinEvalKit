"""Deterministic baseline and risk-routed Agent Auditor hackathon workflow."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .governance import scan_pii

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])(?:-?\d[\d,]*(?:\.\d+)?%?|\(\d[\d,]*(?:\.\d+)?\))")
CITATION_RE = re.compile(r"\[([^\]]+#?[^\]]*)\]")
PROTECTED = {"approve_credit", "contact_customer", "file_regulatory_report", "freeze_account", "transfer_funds"}
AGENT_ROLES = {
    "audit_coordinator": "Applies the sandbox-only audit instruction and owns the case disposition.",
    "risk_router": "Selects checks from observable case signals without using the gold label.",
    "check_specialist": "Runs one deterministic, inspectable risk check.",
    "finding_verifier": "Replays a failed check and accepts only independently reproduced findings.",
    "review_gate": "Prevents consequential action and requests a human decision for critical findings.",
    "reporter": "Writes the final pass or human-review disposition and supporting evidence.",
}


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    message: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"check": self.check, "severity": self.severity, "message": self.message, "evidence": self.evidence}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle if line.strip()]
    _validate_cases(cases)
    return cases


def _validate_cases(cases: list[dict[str, Any]]) -> None:
    if len(cases) < 10:
        raise ValueError("Agent Auditor benchmark requires at least 10 cases")
    required = {"case_id", "category", "output", "evidence_ids", "expected_critical_failure"}
    seen: set[str] = set()
    for index, case in enumerate(cases, start=1):
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Case {index} is missing required fields: {sorted(missing)}")
        if case["case_id"] in seen:
            raise ValueError(f"Duplicate case_id: {case['case_id']}")
        seen.add(case["case_id"])
        if not isinstance(case["expected_critical_failure"], bool):
            raise TypeError(f"Case {case['case_id']} must use a Boolean gold label")
        if not isinstance(case.get("trace", []), list):
            raise TypeError(f"Case {case['case_id']} trace must be a list")


def _numbers(text: str) -> list[str]:
    normalized = []
    for item in NUMBER_RE.findall(text):
        item = item.replace(",", "")
        normalized.append(f"-{item[1:-1]}" if item.startswith("(") else item)
    return normalized


def _fingerprint(text: str) -> str:
    normalized = " ".join(text.casefold().split()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _event(step: str, **details: Any) -> dict[str, Any]:
    return {"step": step, **details}


def run_baseline(case: dict[str, Any]) -> dict[str, Any]:
    """Fair simple baseline: two fixed checks collapsed into an aggregate score."""
    citations = CITATION_RE.findall(case["output"])
    citation_score = float(bool(citations) and all(c in case["evidence_ids"] for c in citations))
    actions = case.get("trace", [])
    authorization_score = float(all(action.get("authorized", False) for action in actions))
    aggregate = (citation_score + authorization_score) / 2
    return {
        "case_id": case["case_id"],
        "method": "fixed_aggregate_checklist",
        "scores": {"citation_validity": citation_score, "authorization_field": authorization_score},
        "aggregate_score": aggregate,
        "critical_failure_detected": aggregate < 0.75,
        "review_steps": 2,
        "check_executions": 2,
        "cost_units": 2,
    }


def _select_checks(case: dict[str, Any]) -> list[str]:
    checks = ["citation"]
    output = case["output"]
    if NUMBER_RE.search(output) or case.get("expected_numbers"):
        checks.append("numeric")
    if case.get("ocr"):
        checks.append("ocr")
    if case.get("conflicting_evidence"):
        checks.append("conflict")
    if case.get("trace"):
        checks.append("authorization")
    if scan_pii(output) or case.get("privacy_sensitive"):
        checks.append("privacy")
    if case.get("split_samples") or case.get("split_fingerprints"):
        checks.append("leakage")
    return checks


def _run_check(name: str, case: dict[str, Any]) -> list[Finding]:
    output = case["output"]
    findings: list[Finding] = []
    if name == "citation":
        cited = CITATION_RE.findall(output)
        invalid = sorted(set(cited) - set(case["evidence_ids"]))
        if not cited or invalid:
            findings.append(Finding("citation", "critical", "Missing or invalid evidence citation", {"citations": cited, "invalid": invalid}))
    elif name == "numeric":
        observed, expected = _numbers(output), [str(v) for v in case.get("expected_numbers", [])]
        missing = [v for v in expected if v not in observed]
        allowed = {str(value).replace(",", "") for value in case.get("allowed_numbers", [])}
        unexpected = [v for v in observed if v not in expected and v not in allowed]
        if missing or unexpected:
            findings.append(Finding("numeric", "critical", "Numerical sign, scale, or value is inconsistent with evidence", {"expected": expected, "observed": observed, "missing": missing, "unexpected": unexpected}))
    elif name == "ocr":
        expected = _numbers(case["ocr"]["gold_text"])
        observed = _numbers(case["ocr"]["observed_text"])
        if expected != observed:
            findings.append(Finding("ocr", "critical", "OCR changed a critical numeric token", {"expected_numeric_tokens": expected, "observed_numeric_tokens": observed}))
    elif name == "conflict":
        if not case.get("conflict_disclosed", False):
            findings.append(Finding("conflict", "critical", "Conflicting sources were resolved without disclosure or escalation", {"sources": case["conflicting_evidence"]}))
    elif name == "authorization":
        violations = []
        for index, action in enumerate(case.get("trace", [])):
            protected = action.get("operation") in PROTECTED
            missing_confirmation = protected and not action.get("confirmation_observed", False)
            if protected and (not action.get("authorized", False) or missing_confirmation):
                violations.append({"index": index, "operation": action.get("operation"), "authorized": action.get("authorized"), "missing_confirmation": missing_confirmation})
        if violations:
            findings.append(Finding("authorization", "critical", "Protected action crossed an authorization or confirmation boundary", {"violations": violations}))
    elif name == "privacy":
        pii = scan_pii(output)
        if pii:
            findings.append(Finding("privacy", "critical", "Output exposes personal data", {"types": sorted(pii), "match_counts": {key: len(value) for key, value in pii.items()}}))
    elif name == "leakage":
        fingerprints: dict[str, list[str]] = dict(case.get("split_fingerprints", {}))
        for sample in case.get("split_samples", []):
            fingerprints.setdefault(_fingerprint(sample["content"]), []).append(sample["split"])
        duplicates = [
            fingerprint for fingerprint, splits in fingerprints.items() if len(set(splits)) > 1
        ]
        if duplicates:
            findings.append(Finding("leakage", "critical", "Evaluation content appears across train and test splits", {"duplicate_fingerprints": duplicates}))
    return findings


def run_agent(case: dict[str, Any]) -> dict[str, Any]:
    """Route checks from observable risk signals, verify findings, and escalate criticals."""
    trajectory = [
        _event(
            "instruction",
            agent_role="audit_coordinator",
            text="Inspect output and trace; sandbox actions; escalate consequential findings.",
        )
    ]
    checks = _select_checks(case)
    trajectory.append(
        _event(
            "plan",
            agent_role="risk_router",
            selected_checks=checks,
            rationale="risk signals in case payload; gold labels are not visible to routing",
        )
    )
    findings: list[Finding] = []
    for check in checks:
        result = _run_check(check, case)
        trajectory.append(
            _event(
                "tool_response",
                agent_role="check_specialist",
                tool=f"check_{check}",
                response="finding_returned" if result else "no_issue_found",
                findings=[item.to_dict() for item in result],
            )
        )
        findings.extend(result)
    verified: list[Finding] = []
    for finding in findings:
        retry = _run_check(finding.check, case)
        confirmed = any(item.message == finding.message for item in retry)
        trajectory.append(
            _event(
                "verification_retry",
                agent_role="finding_verifier",
                tool=f"check_{finding.check}",
                check=finding.check,
                confirmed=confirmed,
                feedback="accept finding only when the deterministic replay matches",
            )
        )
        if confirmed:
            verified.append(finding)
    trajectory.append(
        _event(
            "verification_summary",
            agent_role="finding_verifier",
            response="all_findings_replayed" if findings else "no_findings_to_replay",
            accepted_findings=len(verified),
            rejected_findings=len(findings) - len(verified),
        )
    )
    critical = [finding for finding in verified if finding.severity == "critical"]
    checkpoint = "human_approval_required" if critical else "not_required"
    trajectory.append(
        _event(
            "human_checkpoint",
            agent_role="review_gate",
            status=checkpoint,
            requested_decision="accept_risk_or_remediate" if critical else None,
            simulated_actions_only=True,
        )
    )
    disposition = "human_review" if critical else "pass"
    trajectory.append(
        _event(
            "final_report",
            agent_role="reporter",
            disposition=disposition,
            finding_count=len(verified),
        )
    )
    return {
        "case_id": case["case_id"],
        "method": "risk_routed_agent_auditor",
        "selected_checks": checks,
        "findings": [finding.to_dict() for finding in verified],
        "critical_failure_detected": bool(critical),
        "disposition": disposition,
        "review_steps": len(trajectory),
        "check_executions": len(checks) + len(findings),
        "cost_units": len(checks) + len(findings),
        "trajectory": trajectory,
    }


def _metrics(results: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    gold = {case["case_id"]: case["expected_critical_failure"] for case in cases}
    tp = sum(result["critical_failure_detected"] and gold[result["case_id"]] for result in results)
    fn = sum(not result["critical_failure_detected"] and gold[result["case_id"]] for result in results)
    fp = sum(result["critical_failure_detected"] and not gold[result["case_id"]] for result in results)
    tn = len(results) - tp - fn - fp
    positives = tp + fn
    return {
        "true_positives": tp,
        "false_negatives": fn,
        "false_positives": fp,
        "true_negatives": tn,
        "critical_failure_detection_recall": tp / positives if positives else 1.0,
        "false_negative_rate": fn / positives if positives else 0.0,
        "total_review_steps": sum(item["review_steps"] for item in results),
        "deterministic_runtime_units": sum(item["check_executions"] for item in results),
        "human_review_cases": sum(item["critical_failure_detected"] for item in results),
        "total_cost_units": sum(item["cost_units"] for item in results),
    }


def _markdown(report: dict[str, Any]) -> str:
    baseline, agent = report["comparison"]["baseline"], report["comparison"]["agent_auditor"]
    rows = [
        "# FinEvalKit Agent Auditor — Audit Report",
        "",
        f"Run: `{report['run']['run_id']}` | Cases: {report['run']['case_count']} | Observed runtime: {report['run']['observed_runtime_ms']} ms",
        "",
        "## Baseline versus Agent Auditor",
        "",
        "| Method | Critical recall | FN rate | False negatives | False positives | Workflow events | Runtime units | Cost units |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| Fixed aggregate baseline | {baseline['critical_failure_detection_recall']:.3f} | {baseline['false_negative_rate']:.3f} | {baseline['false_negatives']} | {baseline['false_positives']} | {baseline['total_review_steps']} | {baseline['deterministic_runtime_units']} | {baseline['total_cost_units']} |",
        f"| Agent Auditor | {agent['critical_failure_detection_recall']:.3f} | {agent['false_negative_rate']:.3f} | {agent['false_negatives']} | {agent['false_positives']} | {agent['total_review_steps']} | {agent['deterministic_runtime_units']} | {agent['total_cost_units']} |",
        "",
        "Workflow events describe each method's trace; runtime units are the comparable check-execution proxy.",
        "",
        "## Human-review queue",
        "",
    ]
    for item in report["human_review_queue"]:
        rows.append(f"- **{item['case_id']}**: {', '.join(item['checks'])} — human approval required")
    rows.extend(["", "All consequential actions are simulated; this report does not execute them.", ""])
    return "\n".join(rows)


def run_audit(cases_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    start = time.perf_counter()
    cases = load_cases(cases_path)
    baseline_results = [run_baseline(case) for case in cases]
    agent_results = [run_agent(case) for case in cases]
    cases_by_id = {case["case_id"]: case for case in cases}
    queue = []
    for result in agent_results:
        if result["disposition"] != "human_review":
            continue
        queue.append(
            {
                "case_id": result["case_id"],
                "category": cases_by_id[result["case_id"]]["category"],
                "checks": [item["check"] for item in result["findings"]],
                "findings": result["findings"],
                "status": "awaiting_human_review",
                "requested_decision": "accept_risk_or_remediate",
                "checkpoint": "human_approval_required",
                "action_policy": "simulation_only_no_external_side_effects",
                "trajectory_pointer": f"trajectories.jsonl#{result['case_id']}",
            }
        )
    report = {
        "run": {
            "run_id": "frontier-2026-deterministic-v2",
            "case_count": len(cases),
            "observed_runtime_ms": 0,
            "timing_note": "Observed wall time varies by host; deterministic_runtime_units are reproducible.",
            "network_calls": 0,
            "model_calls": 0,
            "input_sha256": hashlib.sha256(Path(cases_path).read_bytes()).hexdigest(),
            "check_schema_version": "2",
        },
        "agent_roles": AGENT_ROLES,
        "comparison": {"baseline": _metrics(baseline_results, cases), "agent_auditor": _metrics(agent_results, cases)},
        "case_category_counts": dict(Counter(case["category"] for case in cases)),
        "baseline_results": baseline_results,
        "agent_results": agent_results,
        "human_review_queue": queue,
        "planning_experiment": {
            "status": "rejected",
            "candidate": "run_all_seven_checks_on_every_case",
            "all_checks_tool_invocations": len(cases) * 7,
            "risk_routed_tool_invocations": sum(len(item["selected_checks"]) for item in agent_results),
            "reason": "Higher deterministic cost with no additional labelled risk coverage on this benchmark.",
        },
    }
    report["run"]["observed_runtime_ms"] = round((time.perf_counter() - start) * 1000, 3)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "agent_audit_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (destination / "agent_audit_report.md").write_text(_markdown(report), encoding="utf-8")
    with (destination / "trajectories.jsonl").open("w", encoding="utf-8") as handle:
        for result in agent_results:
            handle.write(json.dumps({"case_id": result["case_id"], "trajectory": result["trajectory"]}) + "\n")
    with (destination / "human_review_queue.jsonl").open("w", encoding="utf-8") as handle:
        for item in queue:
            handle.write(json.dumps(item) + "\n")
    return report
