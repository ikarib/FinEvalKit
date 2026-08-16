# Data Card: FinEvalKit Evaluation Data v2

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

## Provenance and privacy

The policy, RAG, annotation, and agent data are fictional. The public-filing fixture contains factual observations derived from Apple Inc.'s public 2025 Form 10-K and retains the filing URL and accession. Source hashes are produced during evaluation runs. No customer records, material non-public information, or real personally identifiable information are included.

## Splitting and leakage

Production extensions should split by source document, issuer, and filing period—not by chunk—so near-identical passages or restatements cannot cross train and evaluation partitions. FinEvalKit checks exact normalized duplicates across splits; semantic near-duplicate detection is a documented extension.

## Limitations

The sample is intentionally small and cannot establish model performance, fairness, or production safety. The filing, judge-calibration, and monitoring fixtures prove executable interfaces, not representativeness. They do not cover the full variation of issuer extensions, amended XBRL facts, scanned statements, handwriting, multilingual documents, charts, or regulatory regimes.
