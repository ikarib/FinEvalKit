import json
from pathlib import Path

from finevalkit.observability import JsonlTracker, RunContext
from finevalkit.v2_pipeline import run_v2_demo

ROOT = Path(__file__).resolve().parents[1]


def test_jsonl_tracker_records_all_version_dimensions(tmp_path):
    path = tmp_path / "events.jsonl"
    context = RunContext("run-1", "data-v1", "model-v1", "prompt-v1", "commit-1")
    JsonlTracker(path).log(context, "completed", {"score": 0.9})

    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["dataset_version"] == "data-v1"
    assert record["code_version"] == "commit-1"
    assert record["payload"]["score"] == 0.9


def test_v2_demo_runs_offline(tmp_path):
    report = run_v2_demo(ROOT, tmp_path)

    assert report["public_filing"]["table_evaluation"]["exact_accuracy"] == 1.0
    assert report["public_filing"]["multimodal_evaluation"]["pass_rate"] == 1.0
    assert (tmp_path / "v2_evaluation_report.json").exists()
    assert (tmp_path / "experiment_events.jsonl").exists()
