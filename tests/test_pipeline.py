import tempfile
import unittest
from pathlib import Path

from finevalkit.pipeline import run_demo


class PipelineTests(unittest.TestCase):
    def test_end_to_end_demo(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = run_demo(root, output)
            self.assertEqual(report["run"]["case_count"], 3)
            self.assertTrue((output / "evaluation_report.json").exists())
            self.assertTrue((output / "evaluation_report.md").exists())
            self.assertEqual(len(report["annotation_quality"]["adjudication_queue"]), 1)


if __name__ == "__main__":
    unittest.main()
