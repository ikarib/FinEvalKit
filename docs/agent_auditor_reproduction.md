# Reproduction guide — FinEvalKit Agent Auditor

Requirements: Python 3.10+, no network, API key, private document, or external service. The package version is 0.3.0. The synthetic development set is `data/agent_auditor/cases.jsonl`; the separately scored held-out adversarial set is `data/agent_auditor/heldout_cases.jsonl`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest tests/test_agent_auditor.py
fineval agent-auditor-demo --output-dir challenge/evidence/agent_auditor
python -m ruff check src tests
```

The command writes `comparison.json` and full held-out synthetic trajectories under the chosen output directory. Its summary is the held-out typed recall; inspect the JSON for the development and held-out reports, per-case outcomes, category recall, precision, false-positive/negative counts and rates, review burden, and proxies. Do not combine the development and held-out scores or present the development result as a headline. Wall-clock time is intentionally not a metric; no model/API cost is incurred, and the check-unit proxy is deterministic.

For the original compatible project regressions, run `pytest`, `fineval demo --output-dir artifacts`, `fineval v2-demo --output-dir artifacts-v2`, and `fineval v3-demo --output-dir artifacts-v3`. The v3 command additionally needs local Tesseract as documented in the main README.

Do not treat the synthetic fixtures or their results as validation for real financial decisions. The workflow only inspects submitted artifacts; humans must approve remediation and any external action.
