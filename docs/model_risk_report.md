# Model Risk and Validation Note

## System under evaluation

FinEvalKit evaluates answers and tool traces produced by a financial-document assistant. It treats retrieval, answer generation, citation, and action execution as separate control points.

## Principal risks

| Risk | Measurement or control | Residual limitation |
|---|---|---|
| Unsupported claims | Citation validity, coverage, and lexical faithfulness | Lexical overlap is not semantic entailment |
| Numerical hallucination | Decimal-normalized source comparison | Derived calculations require task-specific formulas |
| Retrieval failure | Recall against labelled relevant chunks | Relevance labels may be incomplete |
| OCR corruption | Word error rate and OCR-required flags | Layout and table structure need additional metrics |
| Annotation subjectivity | Independent labels, Cohen's kappa, adjudication queue | Small samples produce unstable agreement estimates |
| Data leakage | Cross-split normalized fingerprints | Paraphrased duplicates may remain undetected |
| Unauthorized agent action | Allowlist, authorization, and confirmation checks | Real tool permissions must also be enforced outside the evaluator |
| Privacy exposure | PII scanning and synthetic-data policy | Regex controls do not identify every sensitive entity |

## Acceptance approach

Thresholds are versioned in `config/evaluation_policy.json`. A failed metric is evidence for review, not an automatic production decision. Any unsafe agent trace, unsupported high-risk financial claim, or privacy finding requires investigation regardless of the aggregate score.

## Monitoring proposal

Track metric distributions by document type, product, language, scan quality, and customer workflow. Maintain a frozen golden set for release regression, a rotating recent-data set for drift, and an adversarial set for rare but consequential failures. Document all threshold changes and residual risks.
