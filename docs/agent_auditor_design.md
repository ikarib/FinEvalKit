# FinEvalKit Agent Auditor design

## User and bottleneck

The user is an AI/ML or risk team deploying a financial-document RAG system or a tool-using agent. They need to turn an evaluation target's answer, citations, OCR observations, and proposed tool trace into a reviewable decision. Manual inspection is slow, while an aggregate quality score can pass despite a material sign, scale, provenance, privacy, leakage, or authorization failure.

## Minimal workflow

1. A planner selects deterministic checks only from fields present in the target.
2. A sandboxed check executor inspects numeric tokens, required citations, OCR tokens, holdout markers, PII patterns, and action allowlists. It never calls an action in the target trace.
3. A verifier performs a second, independently derived pass over a separate list of source/value records for a conflict. It keeps a confirmed conflict instead of deciding it.
4. A reporter creates an audit decision and a human-review queue. Any remediation or external action needs human approval.

The roles are observable events rather than separately deployed models. The representative redacted trajectory is in `trajectories/agent_auditor_representative.json`.

## Baseline and evaluation splits

`data/agent_auditor/cases.jsonl` is the frozen ten-case development/regression set. `data/agent_auditor/heldout_cases.jsonl` is a separate ten-case held-out adversarial set. It includes clean negatives, negative and scale/unit variants, unusual valid citations, a PII lookalike explicitly marked as a safe synthetic identifier, OCR letter/number confusion, confirmed and resolved evidence conflicts, and authorization edges.

Every fixture carries human-authored `gold_critical_labels` and `gold_review_required`. These fields are the scoring oracle and are not read by planning or check routing. Routing uses only evidence fields such as `expected_numbers`, citations, trace actions, and conflict records.

The baseline is deliberately simple: it thresholds the supplied aggregate score at 0.80 and produces an untyped review alert. Both workflows receive every field in each fixture, but the baseline only uses the aggregate. It receives fair credit in **review-decision** scoring when it alerts on a case whose independent gold annotation requires review. It cannot claim a category-level detection, so its typed precision, recall, and per-category recall are reported as `null` rather than being forced to zero or expanded into invented labels.

The Auditor emits typed findings. Typed metrics score exact gold-label matches: overall and per-category recall, precision, false-positive count/rate, and false-negative count/rate. Review-decision metrics separately score review precision/recall and false-positive/negative counts/rates against `gold_review_required`; this means a non-critical evidence conflict can correctly enter the review queue. Both reports include queue count/rate plus deterministic step and check-unit proxies.

The difficult development OCR case, `AA-06-ocr-sign`, has `-50` in the expected field and `50` in OCR output. `AA-07-conflict` is intentionally non-critical but must enter human review because its filing and XBRL values disagree. Its verifier event is `independent_verification`, not a retry claim: it checks separately supplied source/value records and records whether they confirm the discrepancy.

Runtime and cost are deterministic proxies, not wall-clock claims: a runtime step is one routed check plus one verifier retry, and a cost unit is one executed check. Review-queue count measures structured cases awaiting human review, not minutes saved.
