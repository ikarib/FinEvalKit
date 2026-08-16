import unittest

from finevalkit.evaluation import (
    bootstrap_mean_ci,
    citation_coverage,
    citation_validity,
    numeric_consistency,
    word_error_rate,
)
from finevalkit.models import Chunk


def sample_chunk() -> Chunk:
    return Chunk(
        chunk_id="c001",
        document_id="report",
        text="Revenue was CAD 125.4 million and margin was 18.2%.",
        page=1,
        modality="pdf",
        source_path="report.pdf",
        source_sha256="abc",
    )


class EvaluationTests(unittest.TestCase):
    def test_citations_and_numbers_pass_when_grounded(self):
        answer = "Revenue was CAD 125.4 million and margin was 18.2% [report#c001]."
        chunk = sample_chunk()
        self.assertTrue(citation_validity(answer, [chunk]).passed)
        self.assertTrue(citation_coverage(answer).passed)
        self.assertTrue(numeric_consistency(answer, [chunk]).passed)

    def test_unsupported_number_fails(self):
        result = numeric_consistency(
            "Revenue was CAD 130.0 million [report#c001].", [sample_chunk()]
        )
        self.assertFalse(result.passed)
        self.assertIn("130.0", result.details["unsupported"])

    def test_word_error_rate_and_bootstrap_are_deterministic(self):
        self.assertEqual(word_error_rate("a b c d", "a b x d"), 0.25)
        self.assertEqual(
            bootstrap_mean_ci([0.2, 0.4, 0.8]), bootstrap_mean_ci([0.2, 0.4, 0.8])
        )


if __name__ == "__main__":
    unittest.main()
