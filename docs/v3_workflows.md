# FinEvalKit v0.3 workflows

## OCR and IFRS/XBRL

`fineval v3-demo` runs Tesseract on `data/ocr_fixture/filing_table_scan.png`, records the engine version and source hash, and computes both word error rate and numeric-token error rate. It independently reconciles the displayed statement values to three `ifrs-full` facts derived from Infosys Limited's 2025 Form 20-F.

The image is generated reproducibly from a financial-table specification with `scripts/generate_ocr_fixture.py`. It is a controlled regression fixture, not a claim of accuracy on arbitrary scans.

## ISO 20022 agent controls

The same command parses a synthetic `pacs.008.001.14` FI-to-FI customer credit transfer. Its parties and account identifiers are conspicuously marked non-routable test values. The parser rejects DTD/entity declarations, verifies the expected namespace and required identifiers, and extracts amount, currency, BICs, and IBANs. A payment above the configured threshold must show both authorization and confirmation in its agent trace.

This is structural-profile validation. Production use must additionally validate against the official ISO 20022 XSD and applicable scheme or market-practice rules.

## Hugging Face retrieval benchmark

Install the semantic extra and run:

```bash
fineval embedding-benchmark --revision 1c82ace116a2629de82404c4be48c0e5d4cf08be
```

The benchmark loads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face on CPU and compares BM25, dense, and reciprocal-rank-fusion hybrid retrieval using recall@3, mean reciprocal rank, and mean query latency. The checked-in dataset contains eight documents and eight labelled queries, so the results are regression evidence rather than a general performance claim.

## Weights & Biases tracking

Install the tracking extra after creating a benchmark report:

```bash
fineval wandb-run --mode offline
wandb sync <offline-run-directory>
```

The run config records dataset, model, prompt, code, and policy versions. Metrics are logged under retriever-specific keys. Use `--mode online --entity <entity>` with an authenticated W&B account to create a hosted run. FinEvalKit never treats an offline run as public evidence.

## Primary specifications

- SEC EDGAR APIs: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>
- Infosys 2025 Form 20-F: <https://www.sec.gov/Archives/edgar/data/1067491/000095017025091925/infy-20250331.htm>
- ISO 20022 message catalogue: <https://www.iso20022.org/catalogue-messages>
- Hugging Face model card: <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2>
- W&B offline mode: <https://docs.wandb.ai/support/models/articles/is-it-possible-to-save-metrics-offline-a>
