.PHONY: test demo lint

test:
	PYTHONPATH=src python -m pytest

demo:
	PYTHONPATH=src python -m finevalkit.cli demo --output-dir artifacts

lint:
	python -m ruff check src tests
