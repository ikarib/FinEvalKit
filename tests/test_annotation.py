import unittest

from finevalkit.annotation import Annotation, agreement_report, cohen_kappa


class AnnotationTests(unittest.TestCase):
    def test_perfect_kappa(self):
        self.assertEqual(cohen_kappa(["pass", "major_error"], ["pass", "major_error"]), 1.0)

    def test_disagreement_enters_adjudication_queue(self):
        annotations = [
            Annotation("c1", "a", "pass", "ok", ()),
            Annotation("c1", "b", "minor_error", "omission", ()),
        ]
        report = agreement_report(annotations)
        self.assertEqual(report["percent_agreement"], 0.0)
        self.assertEqual(report["adjudication_queue"][0]["case_id"], "c1")


if __name__ == "__main__":
    unittest.main()
