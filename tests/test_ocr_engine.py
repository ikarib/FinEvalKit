import shutil
from pathlib import Path

import pytest

from finevalkit.ocr_engine import TesseractOCR, evaluate_ocr_result

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "ocr_fixture"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_tesseract_executes_on_filing_derived_raster():
    reference = (FIXTURE / "filing_table_gold.txt").read_text(encoding="utf-8").strip()
    result = TesseractOCR().extract(FIXTURE / "filing_table_scan.png")
    report = evaluate_ocr_result(result, reference)

    assert result.engine == "tesseract"
    assert len(result.image_sha256) == 64
    assert report["word_error_rate"] == 0.0
    assert report["numeric"]["numeric_error_rate"] == 0.0
