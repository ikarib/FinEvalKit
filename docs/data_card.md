# Data Card: Synthetic Financial Documents v1

## Intended use

The dataset demonstrates evaluation mechanics for financial question answering, credit-policy reasoning, AML uncertainty, and tool-use boundaries. It is suitable for software tests, portfolio demonstrations, and evaluator calibration.

## Composition

- One synthetic annual-report extract
- One synthetic retail-credit policy
- One synthetic AML investigation procedure
- Three source-grounded evaluation cases
- Eight annotations covering four cases and two annotators
- Two agent traces: one compliant and one intentionally non-compliant

## Provenance and privacy

All names, figures, policies, and entities are fictional. Source hashes are produced during each evaluation run. No customer records, material non-public information, or real personally identifiable information are included.

## Splitting and leakage

Production extensions should split by source document or issuer, not by chunk, so near-identical passages cannot cross train and evaluation partitions. FinEvalKit checks exact normalized duplicates across splits; semantic near-duplicate detection is a documented extension.

## Limitations

The sample is intentionally small and cannot establish model performance, fairness, or production safety. It does not represent the full variation of XBRL filings, scanned statements, handwriting, multilingual documents, tables, charts, or regulatory regimes.
