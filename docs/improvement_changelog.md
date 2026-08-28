# Improvement Changelog — FinEvalKit Agent Auditor

This challenge extension builds on the pre-existing FinEvalKit v0.3 deterministic demos for retrieval, citations, numerical consistency, OCR, privacy/leakage, judge calibration, monitoring, authorization, and reproducibility. It adds a narrow end-to-end audit router, a frozen development set, a held-out adversarial set, audit artifacts, trajectories, and challenge documentation. Existing `demo`, `v2-demo`, and `v3-demo` commands are unchanged.

| Iteration | Hypothesis and change | Evidence | Decision |
|---|---|---|---|
| Baseline scoring correction | An aggregate alert is a case-level signal, not an empty typed label set. | The baseline now receives review-decision credit when its alert matches independently annotated review need; typed metrics are `null` because it cannot emit categories. | Keep this split scoring. |
| Held-out adversarial evaluation | Label-aligned development cases overstate robustness. | A distinct held-out set adds clean negatives, sign/scale, unusual citation, PII-lookalike, OCR, conflict, and authorization variants; gold labels are not routing inputs. | Keep both splits separate. |
| Conflict verification | A claimed retry needs distinct evidence. | `AA-07-conflict` now records `independent_verification` over separately supplied source/value records before human escalation. | Keep. |
| Rejected: automatic evidence tie-breaker | Choose filing or XBRL value automatically after conflict detection. | It would make an unreviewed authoritative-source decision; the fixed conflict case has no label establishing a winner. | Removed; escalate instead. |

## Current evidence

Run `fineval agent-auditor-demo --output-dir challenge/evidence/agent_auditor` to regenerate the checked-in [comparison](../challenge/evidence/agent_auditor/comparison.json). It reports both splits without a combined headline, all required classification measures, per-category recall, review burden, and deterministic proxies. This is fixture evidence, not a production-performance claim.

## Main failure mode and hot take

The main failure mode is semantic coverage: rules catch only failure patterns represented by their fields and labels; novel wording, citations, formats, or OCR layouts can evade them. **Hot take:** in finance, an evaluator that knows when to stop and show conflicting evidence is more useful than a high aggregate score that confidently picks a winner.
