import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from finevalkit.agent_auditor import (
    AGENT_ROLES,
    _metrics,
    _numbers,
    load_cases,
    run_agent,
    run_audit,
    run_baseline,
)
from finevalkit.cli import main

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "data/agent_auditor_cases.jsonl"


class AgentAuditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(CASES_PATH)
        cls.by_id = {case["case_id"]: case for case in cls.cases}

    def test_routing_and_finding_detection_for_every_critical_risk(self):
        expectations = {
            "invalid-citation": "citation",
            "sign-error": "numeric",
            "scale-error": "numeric",
            "ocr-sign-and-scale": "ocr",
            "conflicting-evidence-silenced": "conflict",
            "unauthorized-transfer": "authorization",
            "missing-transfer-confirmation": "authorization",
            "pii-disclosure": "privacy",
            "train-test-leakage": "leakage",
        }
        for case_id, expected_check in expectations.items():
            with self.subTest(case_id=case_id):
                result = run_agent(self.by_id[case_id])
                self.assertIn(expected_check, result["selected_checks"])
                self.assertIn(expected_check, {item["check"] for item in result["findings"]})
                self.assertTrue(result["critical_failure_detected"])
                self.assertEqual(result["disposition"], "human_review")

    def test_baseline_misses_sign_error_that_agent_escalates(self):
        case = self.by_id["sign-error"]
        self.assertFalse(run_baseline(case)["critical_failure_detected"])
        result = run_agent(case)
        checkpoint = next(
            event for event in result["trajectory"] if event["step"] == "human_checkpoint"
        )
        self.assertEqual(checkpoint["status"], "human_approval_required")
        self.assertTrue(checkpoint["simulated_actions_only"])

    def test_role_labelled_trajectory_covers_every_agent_role(self):
        result = run_agent(self.by_id["ocr-sign-and-scale"])
        observed_roles = {event["agent_role"] for event in result["trajectory"]}
        self.assertEqual(observed_roles, set(AGENT_ROLES))
        retries = [event for event in result["trajectory"] if event["step"] == "verification_retry"]
        self.assertTrue(retries)
        self.assertTrue(all(event["confirmed"] for event in retries))

    def test_safe_cases_do_not_escalate(self):
        for case in (item for item in self.cases if not item["expected_critical_failure"]):
            with self.subTest(case_id=case["case_id"]):
                result = run_agent(case)
                self.assertEqual(result["disposition"], "pass")
                self.assertFalse(result["findings"])
                checkpoint = next(
                    event for event in result["trajectory"] if event["step"] == "human_checkpoint"
                )
                self.assertEqual(checkpoint["status"], "not_required")

    def test_accounting_parentheses_and_allowed_numbers_are_normalized(self):
        self.assertEqual(_numbers("Operating loss (81.00)"), ["-81.00"])
        case = dict(self.by_id["safe-calculation"])
        case["output"] = "The ratio is 18.2% for 2025 [filing#margin]."
        case["allowed_numbers"] = [2025]
        self.assertFalse(run_agent(case)["findings"])

    def test_metric_computation_includes_false_positive_and_zero_positive_edge(self):
        cases = [
            {"case_id": "safe-a", "expected_critical_failure": False},
            {"case_id": "safe-b", "expected_critical_failure": False},
        ]
        results = [
            {
                "case_id": "safe-a",
                "critical_failure_detected": True,
                "review_steps": 2,
                "check_executions": 1,
                "cost_units": 1,
            },
            {
                "case_id": "safe-b",
                "critical_failure_detected": False,
                "review_steps": 2,
                "check_executions": 1,
                "cost_units": 1,
            },
        ]
        metrics = _metrics(results, cases)
        self.assertEqual(metrics["false_positives"], 1)
        self.assertEqual(metrics["true_negatives"], 1)
        self.assertEqual(metrics["critical_failure_detection_recall"], 1.0)
        self.assertEqual(metrics["false_negative_rate"], 0.0)

    def test_full_audit_is_reproducible_and_writes_audit_ready_evidence(self):
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            report_one = run_audit(CASES_PATH, first)
            report_two = run_audit(CASES_PATH, second)
            report_one["run"].pop("observed_runtime_ms")
            report_two["run"].pop("observed_runtime_ms")
            self.assertEqual(report_one, report_two)
            self.assertEqual(report_one["run"]["case_count"], 12)
            self.assertEqual(report_one["comparison"]["baseline"]["false_negatives"], 7)
            self.assertEqual(report_one["comparison"]["agent_auditor"]["false_negatives"], 0)
            self.assertEqual(
                report_one["comparison"]["agent_auditor"]["deterministic_runtime_units"], 45
            )
            self.assertEqual(len(report_one["human_review_queue"]), 9)
            self.assertTrue(all(item["findings"] for item in report_one["human_review_queue"]))
            for filename in ("trajectories.jsonl", "human_review_queue.jsonl"):
                self.assertEqual(
                    (Path(first) / filename).read_bytes(), (Path(second) / filename).read_bytes()
                )

    def test_cli_command_writes_expected_files_and_summary(self):
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                status = main(
                    ["agent-audit", "--cases", str(CASES_PATH), "--output-dir", directory]
                )
            self.assertEqual(status, 0)
            self.assertIn("baseline recall=0.222; agent recall=1.000", output.getvalue())
            self.assertEqual(
                {path.name for path in Path(directory).iterdir()},
                {
                    "agent_audit_report.json",
                    "agent_audit_report.md",
                    "human_review_queue.jsonl",
                    "trajectories.jsonl",
                },
            )
            report = json.loads(
                (Path(directory) / "agent_audit_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["run"]["network_calls"], 0)
            self.assertEqual(report["run"]["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
