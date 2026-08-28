#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "trajectories" / "raw"
ATIF_DIR = ROOT / "trajectories" / "atif"
OUTPUT = ROOT / "trajectories" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_first_human_prompt(trajectory: dict) -> str | None:
    for step in trajectory.get("steps", []):
        if step.get("source") != "user":
            continue

        message = step.get("message", "")

        # Skip Codex-injected AGENTS/environment context.
        if message.startswith("# AGENTS.md instructions"):
            continue

        return message

    return None


def main() -> None:
    entries = []

    for atif_path in sorted(ATIF_DIR.glob("*.trajectory.json")):
        raw_name = atif_path.name.replace(".trajectory.json", ".jsonl")
        raw_path = RAW_DIR / raw_name

        if not raw_path.exists():
            raise RuntimeError(
                f"Missing raw source for {atif_path.name}: {raw_path}"
            )

        trajectory = json.loads(atif_path.read_text(encoding="utf-8"))

        steps = trajectory.get("steps", [])

        tool_calls = sum(
            len(step.get("tool_calls", []))
            for step in steps
        )

        observations = sum(
            len(
                step.get("observation", {})
                .get("results", [])
            )
            for step in steps
        )

        user_steps = sum(
            step.get("source") == "user"
            for step in steps
        )

        agent_steps = sum(
            step.get("source") == "agent"
            for step in steps
        )

        timestamps = [
            step.get("timestamp")
            for step in steps
            if step.get("timestamp")
        ]

        entries.append(
            {
                "session_id": trajectory.get("session_id"),
                "schema_version": trajectory.get("schema_version"),
                "raw_file": str(raw_path.relative_to(ROOT)),
                "atif_file": str(atif_path.relative_to(ROOT)),
                "raw_sha256": sha256(raw_path),
                "atif_sha256": sha256(atif_path),
                "step_count": len(steps),
                "user_steps": user_steps,
                "agent_steps": agent_steps,
                "tool_calls": tool_calls,
                "observations": observations,
                "start_timestamp": min(timestamps) if timestamps else None,
                "end_timestamp": max(timestamps) if timestamps else None,
                "human_prompt": extract_first_human_prompt(trajectory),
            }
        )

    manifest = {
        "format": "FinEvalKit trajectory manifest",
        "source": "Codex CLI complete session histories",
        "session_count": len(entries),
        "sessions": entries,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"sessions: {len(entries)}")


if __name__ == "__main__":
    main()
