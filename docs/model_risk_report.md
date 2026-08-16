# Model Risk and Validation Note

## System under evaluation

FinEvalKit evaluates answers and tool traces produced by a financial-document assistant. It treats retrieval, answer generation, citation, and action execution as separate control points.

## Principal risks

| Risk | Measurement or control | Residual limitation |
|---|---|---|
| Unsupported claims | Citation validity, coverage, and lexical faithfulness | Lexical overlap is not semantic entailment |
| Numerical hallucination | Decimal-normalized source comparison | Derived calculations require task-specific formulas |
| Retrieval failure | Recall against labelled relevant chunks | Relevance labels may be incomplete |
| OCR corruption | Word error rate, critical numeric error rate, and OCR-required flags | The toolkit scores OCR output but does not run OCR inference |
| Filing/table extraction | XBRL reconciliation with period, unit, sign, scale, and cell provenance | Four facts from one issuer cannot establish generalization |
| Chart/VLM error | Numeric answer match plus visual source locator | The toolkit scores supplied outputs but does not run a VLM |
| Judge bias/error | Human-gold confusion matrix, macro-F1, kappa, and review routing | The included calibration set is intentionally small |
| Annotation subjectivity | Independent labels, Cohen's kappa, adjudication queue | Small samples produce unstable agreement estimates |
| Data leakage | Cross-split normalized fingerprints | Paraphrased duplicates may remain undetected |
| Unauthorized agent action | Allowlist, authorization, and confirmation checks | Real tool permissions must also be enforced outside the evaluator |
| Privacy exposure | PII scanning and synthetic-data policy | Regex controls do not identify every sensitive entity |

## Acceptance approach

Thresholds are versioned in `config/evaluation_policy.json`. A failed metric is evidence for review, not an automatic production decision. Any unsafe agent trace, unsupported high-risk financial claim, or privacy finding requires investigation regardless of the aggregate score.

## Monitoring proposal

Track metric distributions by document type, product, language, scan quality, and customer workflow. Maintain a frozen golden set for release regression, a rotating recent-data set for drift, and an adversarial set for rare but consequential failures. Document all threshold changes and residual risks.

FinEvalKit v0.2 implements modality/workflow slices, bootstrap intervals, categorical PSI, and dataset/model/prompt/code-versioned events. These improve auditability but do not by themselves constitute production observability or a fairness assessment.

## Residual limitations

The project does not validate a production model or perform OCR/VLM inference. XBRL, table, OCR-output, chart-output, hybrid-retrieval, and judge-calibration paths are demonstrated on small offline fixtures. Production adoption requires issuer-diverse data, independent validation, access controls, calibrated alert thresholds, ongoing drift review, and documented owner approval.
