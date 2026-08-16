import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_published_hugging_face_benchmark_and_wandb_lineage():
    benchmark = json.loads(
        (ROOT / "benchmarks" / "results" / "minilm_retrieval.json").read_text(
            encoding="utf-8"
        )
    )
    run = json.loads(
        (ROOT / "benchmarks" / "results" / "wandb_run.json").read_text(encoding="utf-8")
    )

    assert benchmark["case_count"] == benchmark["document_count"] == 8
    assert benchmark["model"]["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert benchmark["results"]["dense"]["recall_at_3"] == 1.0
    assert benchmark["results"]["dense"]["mean_reciprocal_rank"] == 0.9375
    assert run["mode"] == "online"
    assert run["run_id"] == "egtj3vi4"
    assert run["url"].endswith("/isk/FinEvalKit/runs/egtj3vi4")
