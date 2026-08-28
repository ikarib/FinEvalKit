# Improvement Changelog — FinEvalKit Agent Auditor

This challenge extension builds on the pre-existing FinEvalKit v0.3 deterministic demos for retrieval, citations, numerical consistency, OCR, privacy/leakage, judge calibration, monitoring, authorization, and reproducibility. It adds a narrow end-to-end audit router, a frozen ten-case comparison, audit artifacts, trajectories, and challenge documentation. Existing `demo`, `v2-demo`, and `v3-demo` commands are unchanged.

| Iteration | Hypothesis and change | Evidence | Decision |
|---|---|---|---|
| Baseline | An aggregate threshold is a fair simplest comparator. | It is deterministic and uses all ten frozen records, but attributes 0/9 critical labels; [final evidence](../challenge/evidence/final_results.json). | Keep as baseline only. |
| Routed checks | Selecting checks from supplied evidence will surface failures an aggregate hides. | Agent Auditor attributes 9/9 critical labels with 0 false negatives; baseline has 9. | Keep. |
| Conflict verifier | A retry before escalation prevents the auditor from silently choosing between conflicting evidence. | `AA-07-conflict` plans a conflict check, retries it, then enters review; [trajectory](../trajectories/agent_auditor_representative.json). | Keep. |
| Rejected: automatic evidence tie-breaker | Choose filing or XBRL value automatically after conflict detection. | It would make an unreviewed authoritative-source decision; the fixed conflict case has no label establishing a winner. | Removed; escalate instead. |

## Final comparison

| Workflow | Critical detection recall | False negatives | Review queue | Runtime steps | Check-cost units |
|---|---:|---:|---:|---:|---:|
| Fixed aggregate baseline | 0/9 (0.000) | 9 | 1 | 10 | 10 |
| Agent Auditor | 9/9 (1.000) | 0 | 9 | 27 | 26 |

The agent is more expensive under the explicit proxy and deliberately sends every finding to review. This is fixture evidence, not a production-performance claim.

## Main failure mode and hot take

The main failure mode is semantic coverage: rules catch only failure patterns represented by their fields and labels; novel wording, citations, formats, or OCR layouts can evade them. **Hot take:** in finance, an evaluator that knows when to stop and show conflicting evidence is more useful than a high aggregate score that confidently picks a winner.
