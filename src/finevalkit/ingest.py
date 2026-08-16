"""Document ingestion with provenance and OCR-quality awareness."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from pathlib import Path

from .models import Chunk


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _paragraph_chunks(text: str, max_chars: int = 900) -> list[str]:
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paragraphs = [p for p in paragraphs if p]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def ingest_text(path: str | Path, document_id: str | None = None) -> list[Chunk]:
    source = Path(path)
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    doc_id = document_id or source.stem
    digest = sha256_bytes(raw)
    return [
        Chunk(
            chunk_id=f"c{index:03d}",
            document_id=doc_id,
            text=content,
            page=None,
            modality="text",
            source_path=str(source),
            source_sha256=digest,
        )
        for index, content in enumerate(_paragraph_chunks(text), start=1)
    ]


def ingest_pdf(path: str | Path, document_id: str | None = None) -> list[Chunk]:
    """Extract a PDF while flagging pages that need OCR.

    Install the optional ``pdf`` extra to enable this path. Pages with fewer
    than 40 alphanumeric characters are retained with ``ocr_required`` status
    rather than silently treated as empty.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - optional integration
        raise RuntimeError("Install FinEvalKit with the 'pdf' extra to ingest PDFs") from exc

    source = Path(path)
    raw = source.read_bytes()
    digest = sha256_bytes(raw)
    doc_id = document_id or source.stem
    chunks: list[Chunk] = []
    for page_number, page in enumerate(PdfReader(source).pages, start=1):
        text = page.extract_text() or ""
        status = "native_text" if len(re.findall(r"[A-Za-z0-9]", text)) >= 40 else "ocr_required"
        page_chunks = _paragraph_chunks(text) or [""]
        for local_index, content in enumerate(page_chunks, start=1):
            chunks.append(
                Chunk(
                    chunk_id=f"p{page_number:03d}c{local_index:02d}",
                    document_id=doc_id,
                    text=content,
                    page=page_number,
                    modality="pdf",
                    source_path=str(source),
                    source_sha256=digest,
                    extraction_status=status,
                )
            )
    return chunks


def ingest_directory(path: str | Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for source in sorted(Path(path).iterdir()):
        if source.suffix.lower() == ".txt":
            chunks.extend(ingest_text(source))
        elif source.suffix.lower() == ".pdf":
            chunks.extend(ingest_pdf(source))
    return chunks


def provenance_manifest(chunks: Iterable[Chunk]) -> list[dict[str, object]]:
    unique: dict[tuple[str, str], dict[str, object]] = {}
    for chunk in chunks:
        key = (chunk.document_id, chunk.source_sha256)
        entry = unique.setdefault(
            key,
            {
                "document_id": chunk.document_id,
                "source_path": chunk.source_path,
                "source_sha256": chunk.source_sha256,
                "modalities": set(),
                "extraction_statuses": set(),
            },
        )
        entry["modalities"].add(chunk.modality)  # type: ignore[union-attr]
        entry["extraction_statuses"].add(chunk.extraction_status)  # type: ignore[union-attr]
    result = []
    for entry in unique.values():
        entry["modalities"] = sorted(entry["modalities"])  # type: ignore[arg-type]
        entry["extraction_statuses"] = sorted(entry["extraction_statuses"])  # type: ignore[arg-type]
        result.append(entry)
    return sorted(result, key=lambda item: str(item["document_id"]))
