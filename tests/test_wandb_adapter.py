import sys
from types import SimpleNamespace

from finevalkit.observability import RunContext, WandbTracker


class FakeRun:
    id = "offline-run-1"
    name = "test-run"
    url = None

    def __init__(self):
        self.logged = []
        self.finished = False

    def log(self, payload):
        self.logged.append(payload)

    def finish(self):
        self.finished = True


def test_wandb_tracker_passes_versioned_context_and_finishes(monkeypatch, tmp_path):
    fake_run = FakeRun()
    captured = {}

    def fake_init(**kwargs):
        captured.update(kwargs)
        return fake_run

    monkeypatch.setitem(sys.modules, "wandb", SimpleNamespace(init=fake_init))
    context = RunContext("run", "data", "model", "prompt", "code", "policy")
    tracker = WandbTracker("finevalkit", context, mode="offline", directory=tmp_path)
    tracker.log(context, "evaluation", {"score": 0.9})
    summary = tracker.finish()

    assert captured["mode"] == "offline"
    assert captured["config"]["dataset_version"] == "data"
    assert fake_run.logged == [{"event": "evaluation", "score": 0.9}]
    assert fake_run.finished is True
    assert summary["provider"] == "Weights & Biases"
