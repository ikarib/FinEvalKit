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
    """Optional adapter; importing the package is deferred until use."""

    def __init__(self, project: str, context: RunContext):
        try:
            import wandb
        except ImportError as error:  # pragma: no cover - optional dependency
            raise RuntimeError("install FinEvalKit with the 'tracking' extra") from error
        self.run = wandb.init(project=project, config=asdict(context))

    def log(self, context: RunContext, event: str, payload: dict[str, Any]) -> None:
        del context
        self.run.log({"event": event, **payload})
