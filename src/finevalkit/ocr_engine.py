"""Execute OCR engines and retain replayable provenance."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .evaluation import word_error_rate
from .table_eval import ocr_numeric_error_rate


@dataclass(frozen=True)
class OCRResult:
    engine: str
    engine_version: str
    image_sha256: str
    language: str
    page_segmentation_mode: int
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class TesseractOCR:
    def __init__(self, executable: str | None = None):
        resolved = executable or shutil.which("tesseract")
        if not resolved:
            raise RuntimeError("Tesseract is required; install the tesseract-ocr system package")
        self.executable = resolved

    def version(self) -> str:
        completed = subprocess.run(
            [self.executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return completed.stdout.splitlines()[0].strip()

    def extract(
        self,
        image_path: str | Path,
        *,
        language: str = "eng",
        page_segmentation_mode: int = 6,
    ) -> OCRResult:
        image = Path(image_path)
        if not image.is_file():
            raise FileNotFoundError(image)
        completed = subprocess.run(
            [
                self.executable,
                str(image),
                "stdout",
                "-l",
                language,
                "--psm",
                str(page_segmentation_mode),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return OCRResult(
            engine="tesseract",
            engine_version=self.version(),
            image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
            language=language,
            page_segmentation_mode=page_segmentation_mode,
            text=completed.stdout.strip(),
        )


def evaluate_ocr_result(result: OCRResult, reference: str) -> dict[str, object]:
    return {
        "engine": result.to_dict(),
        "word_error_rate": word_error_rate(reference, result.text),
        "numeric": ocr_numeric_error_rate(reference, result.text),
    }
