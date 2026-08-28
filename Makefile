.PHONY: test demo agent-audit lint

test:
	PYTHONPATH=src python -m pytest

demo:
	PYTHONPATH=src python -m finevalkit.cli demo --output-dir artifacts

agent-audit:
	PYTHONPATH=src python -m finevalkit.cli agent-audit --output-dir artifacts-agent-auditor

lint:
	python -m ruff check src tests
