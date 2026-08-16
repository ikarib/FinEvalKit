"""Versioned experiment events with an optional W&B adapter."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class RunContext:
    run_id: str
    dataset_version: str
    model_version: str
    prompt_version: str
    code_version: str
    policy_version: str = "unversioned"


class Tracker(Protocol):
    def log(self, context: RunContext, event: str, payload: dict[str, Any]) -> None: ...


class JsonlTracker:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, context: RunContext, event: str, payload: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **asdict(context),
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")


class WandbTracker:
    """W&B adapter supporting authenticated online or replayable offline runs."""

    def __init__(
        self,
        project: str,
        context: RunContext,
        *,
        mode: str = "offline",
        entity: str | None = None,
        run_name: str | None = None,
        directory: str | Path = "artifacts/wandb",
        tags: tuple[str, ...] = ("financial-ai", "evaluation"),
    ):
        if mode not in {"online", "offline", "disabled"}:
            raise ValueError("W&B mode must be online, offline, or disabled")
        try:
            import wandb
        except ImportError as error:  # pragma: no cover - optional dependency
            raise RuntimeError("install FinEvalKit with the 'tracking' extra") from error
        run_directory = Path(directory)
        run_directory.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.project = project
        self.run = wandb.init(
            project=project,
            entity=entity,
            name=run_name or context.run_id,
            config=asdict(context),
            mode=mode,
            dir=str(run_directory),
            tags=list(tags),
            reinit=True,
        )

    def log(self, context: RunContext, event: str, payload: dict[str, Any]) -> None:
        del context
        self.run.log({"event": event, **payload})

    def finish(self) -> dict[str, object]:
        summary = {
            "provider": "Weights & Biases",
            "project": self.project,
            "run_id": self.run.id,
            "run_name": self.run.name,
            "mode": self.mode,
            "url": self.run.url if self.mode == "online" else None,
            "sync_command": "wandb sync <offline-run-directory>"
            if self.mode == "offline"
            else None,
        }
        self.run.finish()
        return summary


def log_benchmark_to_wandb(
    report_path: str | Path,
    summary_path: str | Path,
    *,
    project: str = "finevalkit",
    mode: str = "offline",
    entity: str | None = None,
    directory: str | Path = "artifacts/wandb",
) -> dict[str, object]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    model = report["model"]
    context = RunContext(
        run_id="hf-retrieval-benchmark-v1",
        dataset_version=str(report["dataset"]),
        model_version=f"{model['model_name']}@{model['revision']}",
        prompt_version="not-applicable",
        code_version="finevalkit-v0.3.0",
        policy_version="3.0",
    )
    tracker = WandbTracker(
        project,
        context,
        mode=mode,
        entity=entity,
        directory=directory,
        run_name="hf-retrieval-benchmark-v1",
    )
    metrics = {
        f"{retriever}/{metric}": value
        for retriever, values in report["results"].items()
        for metric, value in values.items()
    }
    tracker.log(context, "retrieval_benchmark", metrics)
    summary = tracker.finish()
    output = Path(summary_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
