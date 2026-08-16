import shutil
from pathlib import Path

import pytest

from finevalkit.v3_pipeline import run_v3_demo

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_v3_demo_runs_real_ocr_ifrs_and_iso_controls(tmp_path):
    report = run_v3_demo(ROOT, tmp_path)

    assert report["ocr"]["word_error_rate"] == 0.0
    assert report["ifrs_xbrl"]["table_evaluation"]["exact_accuracy"] == 1.0
    assert report["iso20022"]["authorized_trace"]["passed"] is True
    assert report["iso20022"]["blocked_trace"]["passed"] is False
    assert (tmp_path / "v3_evaluation_report.json").exists()
