# Model Risk and Validation Note

## System under evaluation

FinEvalKit evaluates answers and tool traces produced by a financial-document assistant. It treats retrieval, answer generation, citation, and action execution as separate control points.

## Principal risks

| Risk | Measurement or control | Residual limitation |
|---|---|---|
| Unsupported claims | Citation validity, coverage, and lexical faithfulness | Lexical overlap is not semantic entailment |
| Numerical hallucination | Decimal-normalized source comparison | Derived calculations require task-specific formulas |
| Retrieval failure | Recall against labelled relevant chunks | Relevance labels may be incomplete |
| OCR corruption | Real Tesseract inference, engine/version/hash evidence, word error rate, critical numeric error rate, and OCR-required flags | One generated scan cannot establish robustness to real filing artifacts |
| Filing/table extraction | US-GAAP and IFRS XBRL reconciliation with period, unit, sign, scale, and cell provenance | Seven facts from two issuers cannot establish generalization |
| Chart/VLM error | Numeric answer match plus visual source locator | The toolkit scores supplied outputs but does not run a VLM |
| Judge bias/error | Human-gold confusion matrix, macro-F1, kappa, and review routing | The included calibration set is intentionally small |
| Annotation subjectivity | Independent labels, Cohen's kappa, adjudication queue | Small samples produce unstable agreement estimates |
| Data leakage | Cross-split normalized fingerprints | Paraphrased duplicates may remain undetected |
| Unauthorized agent action | Allowlist, authorization, and confirmation checks | Real tool permissions must also be enforced outside the evaluator |
| Payment-message misuse | pacs.008 namespace/profile checks plus value-based authorization and confirmation controls | Structural checks are not full XSD or scheme-rule validation |
| Privacy exposure | PII scanning and synthetic-data policy | Regex controls do not identify every sensitive entity |

## Acceptance approach

Thresholds are versioned in `config/evaluation_policy.json`. A failed metric is evidence for review, not an automatic production decision. Any unsafe agent trace, unsupported high-risk financial claim, or privacy finding requires investigation regardless of the aggregate score.

## Monitoring proposal

Track metric distributions by document type, product, language, scan quality, and customer workflow. Maintain a frozen golden set for release regression, a rotating recent-data set for drift, and an adversarial set for rare but consequential failures. Document all threshold changes and residual risks.

FinEvalKit v0.3 implements modality/workflow slices, bootstrap intervals, categorical PSI, dataset/model/prompt/code-versioned events, and an optional W&B adapter supporting offline replay or authenticated online runs. These improve auditability but do not by themselves constitute production observability or a fairness assessment.

## Residual limitations

The project does not validate a production model or perform VLM inference. XBRL, table, OCR, ISO 20022, chart-output, hybrid-retrieval, and judge-calibration paths are demonstrated on small fixtures. The Hugging Face and W&B commands require their optional dependencies; a public W&B run additionally requires account credentials. Production adoption requires issuer-diverse data, independent validation, official message-schema and market-practice validation, access controls, calibrated alert thresholds, ongoing drift review, and documented owner approval.
