import unittest

from finevalkit.agent_eval import ToolAction, evaluate_trace
from finevalkit.governance import redact_pii, scan_pii


class GovernanceAgentTests(unittest.TestCase):
    def test_pii_scan_and_redaction(self):
        text = "Contact analyst@example.com or 403-555-0199."
        findings = scan_pii(text)
        redacted, counts = redact_pii(text)
        self.assertEqual(set(findings), {"email", "phone"})
        self.assertNotIn("analyst@example.com", redacted)
        self.assertEqual(counts, {"email": 1, "phone": 1})

    def test_unauthorized_transaction_fails_policy(self):
        report = evaluate_trace(
            [
                ToolAction(
                    tool="payment_system",
                    operation="transfer",
                    authorized=False,
                    required_confirmation=True,
                )
            ]
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["violation_count"], 1)


if __name__ == "__main__":
    unittest.main()
