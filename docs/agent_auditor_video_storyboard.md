# Five-minute demo storyboard (draft; no video recorded)

| Time | Screen / narration |
|---|---|
| 0:00–0:35 | State the user: an AI/ML or risk team reviewing financial RAG/agent outputs. Explain why a 0.94 aggregate can still hide a scale or authorization failure. |
| 0:35–1:00 | Open `data/agent_auditor/cases.jsonl`; show the fixed aggregate baseline and that both workflows receive these same ten synthetic records. |
| 1:00–2:30 | Run `fineval agent-auditor-demo --output-dir artifacts/agent_auditor`. Open `AA-07-conflict`: planner selects checks, executor reports tool responses, verifier retries the filing/XBRL conflict, reporter stops at human escalation. Emphasize that no action runs. |
| 2:30–3:20 | Show `AA-06-ocr-sign` and `AA-10-confirmation`: the sign loss and absent confirmation are independently flagged. |
| 3:20–4:10 | Open `challenge/evidence/final_results.json` and compare 0/9 baseline attribution with 9/9 Agent Auditor attribution. Explain check-cost/runtime proxies and the larger review queue. |
| 4:10–4:40 | Open the Improvement Changelog. Call out the largest contribution: evidence-aware check routing with verification. Call out the removed automatic tie-breaker. |
| 4:40–5:00 | State the main limitation and hot take: rules have bounded coverage; preserve conflict and ask a human rather than invent an authoritative answer. Point to reproduction guide and trajectories. |
