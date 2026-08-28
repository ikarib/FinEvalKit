# Five-minute demo video storyboard (draft; not recorded)

## 0:00–0:35 — The problem

Show the README and say: “FinEvalKit Agent Auditor is for the AI/ML or risk team shipping a
financial-document RAG or tool-using agent. Their bottleneck is not another average score. It is
finding the one sign, citation, privacy, leakage, or authorization failure that must stop release.”

## 0:35–1:10 — Fair baseline

Open `run_baseline` and the case file. Explain that both solutions see the same 12 cases. The baseline
always checks citation validity and an authorization Boolean, then thresholds their mean. Run the CLI
and point to its 0.222 recall and seven false negatives.

## 1:10–2:40 — One end-to-end difficult case

Open `ocr-sign-and-scale`: the gold scan says `(81.00)` while OCR produced `8100`, and the answer
reports a positive 8100 million. In the matching trajectory, show:

1. instruction and selected citation/numerical/OCR/authorization checks;
2. numerical and OCR tool responses;
3. deterministic verification retries;
4. the simulated human-approval checkpoint; and
5. the final human-review disposition.

Emphasize that no payment, filing, customer contact, or other consequential action can execute.

## 2:40–3:30 — Comparison and evidence

Open `agent_audit_report.md`. Highlight identical cases, 1.000 versus 0.222 critical recall, zero
versus seven false negatives, no false positives, and the explicit proxy tradeoff: 45 versus 24
deterministic runtime/cost units and 105 versus 24 method-specific workflow events. Say these are
checked local results, not generalized production
claims. Show the nine-record queue and one privacy-safe trajectory.

## 3:30–4:20 — Improvement changelog and removed experiment

Show the changelog. The initial aggregate hid seven failures. A proposed run-all design was rejected:
84 check calls versus 35 selected calls with the same labelled risk coverage. Risk routing cut that
work, then verification replay deliberately added cost where a critical finding justified it.

## 4:20–4:50 — Biggest contribution

Show the JSON report and trajectories together. Say: “The contribution is not a new metric. It is the
audit seam connecting risk-aware planning, inspectable checks, verification, and a human decision in
one deterministic artifact trail.”

## 4:50–5:00 — Close

State the limitation and hot take: the benchmark cannot expose unrepresented risks, so production
needs new human-labelled slices. “A replayable escalation is worth more than an aggregate score that
cannot tell you which unsafe answer to stop.”
