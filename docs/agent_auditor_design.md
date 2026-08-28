# FinEvalKit Agent Auditor design

## User and bottleneck

The user is an AI/ML or risk team deploying a financial-document RAG system or a tool-using agent. They need to turn an evaluation target's answer, citations, OCR observations, and proposed tool trace into a reviewable decision. Manual inspection is slow, while an aggregate quality score can pass despite a material sign, scale, provenance, privacy, leakage, or authorization failure.

## Minimal workflow

1. A planner selects deterministic checks only from fields present in the target.
2. A sandboxed check executor inspects numeric tokens, required citations, OCR tokens, holdout markers, PII patterns, and action allowlists. It never calls an action in the target trace.
3. A verifier retries conflicting evidence against the complete supplied evidence set and keeps the conflict instead of deciding it.
4. A reporter creates an audit decision and a human-review queue. Any remediation or external action needs human approval.

The roles are observable events rather than separately deployed models. The representative redacted trajectory is in `trajectories/agent_auditor_representative.json`.

## Baseline and fixed evaluation

The baseline is deliberately simple: it thresholds the provided aggregate score at 0.80. It receives exactly the same ten `data/agent_auditor/cases.jsonl` records, but it does not inspect their individual evidence fields. The Agent Auditor is evaluated against the same frozen `critical_labels` rubric. Critical recall counts correctly attributed labels divided by the nine labeled critical failures; an untyped aggregate alert does not count as a detection.

The difficult OCR case, `AA-06-ocr-sign`, has `-50` in the expected field and `50` in OCR output. `AA-07-conflict` is intentionally non-critical but must enter human review because its filing and XBRL values disagree.

Runtime and cost are deterministic proxies, not wall-clock claims: a runtime step is one routed check plus one verifier retry, and a cost unit is one executed check. Review-queue count measures structured cases awaiting human review, not minutes saved.
