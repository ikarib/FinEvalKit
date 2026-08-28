# Reproduction guide — FinEvalKit Agent Auditor

Requirements: Python 3.10+ (the checked-in run used Python 3.14.4, pytest 9.1.1, and Ruff 0.16.4), no network, API key, private document, or external service. The package version is 0.3.0. All ten cases are synthetic and checked in at `data/agent_auditor/cases.jsonl`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest tests/test_agent_auditor.py
fineval agent-auditor-demo --output-dir artifacts/agent_auditor
python -m ruff check src tests
```

Expected command output includes `critical recall=1.000 (9/9)`. The command writes `comparison.json` and full synthetic trajectories under the chosen output directory. Compare its stable summary to `challenge/evidence/final_results.json`; the checked-in run reports baseline 0/9 and Agent Auditor 9/9 critical labels, 10 vs. 27 runtime-proxy steps, and 10 vs. 26 check-cost units. A timed local run took 0.14 seconds; hardware-dependent wall time is not used as a metric. No model/API cost is incurred, and the check-unit proxy is supplied for fair deterministic comparison.

For the original compatible project regressions, run `pytest`, `fineval demo --output-dir artifacts`, `fineval v2-demo --output-dir artifacts-v2`, and `fineval v3-demo --output-dir artifacts-v3`. The v3 command additionally needs local Tesseract as documented in the main README.

Do not treat the synthetic fixtures or their results as validation for real financial decisions. The workflow only inspects submitted artifacts; humans must approve remediation and any external action.
