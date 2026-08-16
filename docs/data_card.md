# Data Card: FinEvalKit Evaluation Data v3

## Intended use

The data demonstrates evaluation mechanics for financial question answering, credit-policy reasoning, AML uncertainty, public-filing extraction, and tool-use boundaries. It is suitable for software tests, portfolio demonstrations, and evaluator calibration.

## Composition

- One synthetic annual-report extract
- One synthetic retail-credit policy
- One synthetic AML investigation procedure
- Three source-grounded evaluation cases
- Eight annotations covering four cases and two annotators
- Two agent traces: one compliant and one intentionally non-compliant
- Four public Apple 2025 Form 10-K observations in a reduced SEC-compatible XBRL fixture
- Four statement-table cells plus two chart-QA cases derived from the same filing
- Twelve human/automated-judge comparison labels and twelve monitoring observations
- Three public Infosys 2025 Form 20-F observations using `ifrs-full` concepts
- One reproducibly generated scanned-table PNG, its gold transcription, and source manifest
- Two synthetic ISO 20022 pacs.008.001.14 payment messages/traces: authorized and blocked
- Eight labelled retrieval documents and eight queries for BM25/dense/hybrid comparison

## Provenance and privacy

The policy, RAG, annotation, payment, and agent data are fictional. The public-filing fixtures contain factual observations derived from Apple Inc.'s public 2025 Form 10-K and Infosys Limited's public 2025 Form 20-F; both retain filing URLs and accessions. The OCR image is generated locally from the attributed Infosys values rather than copied from a filing page. Source hashes are produced during evaluation runs. No customer records, material non-public information, or real personally identifiable information are included.

## Splitting and leakage

Production extensions should split by source document, issuer, and filing period—not by chunk—so near-identical passages or restatements cannot cross train and evaluation partitions. FinEvalKit checks exact normalized duplicates across splits; semantic near-duplicate detection is a documented extension.

## Limitations

The sample is intentionally small and cannot establish model performance, fairness, or production safety. The filing, OCR, payment, retrieval, judge-calibration, and monitoring fixtures prove executable interfaces, not representativeness. They do not cover the full variation of issuer extensions, amended XBRL facts, original full-page scans, handwriting, multilingual documents, charts, or regulatory regimes. The ISO 20022 path validates a constrained pacs.008 structural profile and business controls, not the official XSD or complete market-practice rules.
