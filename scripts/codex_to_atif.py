#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def text_content(content: Any) -> str:
    """Extract text from Codex message/output content arrays."""
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return ""

    parts: list[str] = []

    for item in content:
        if not isinstance(item, dict):
            continue

        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)

    return "".join(parts)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []

    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"{path}:{lineno}: invalid JSON: {exc}"
                ) from exc

    return records


def convert(path: Path) -> dict[str, Any]:
    records = load_jsonl(path)

    session_meta: dict[str, Any] = {}
    steps: list[dict[str, Any]] = []

    # call_id -> ATIF step containing the tool call
    pending_calls: dict[str, dict[str, Any]] = {}

    step_id = 0

    def next_step_id() -> int:
        nonlocal step_id
        step_id += 1
        return step_id

    for record in records:
        record_type = record.get("type")
        payload = record.get("payload") or {}
        timestamp = record.get("timestamp")

        if record_type == "session_meta":
            session_meta = payload
            continue

        if record_type != "response_item":
            continue

        subtype = payload.get("type")

        if subtype == "message":
            role = payload.get("role")

            # ATIF represents conversational user/agent steps.
            # Developer/system messages are metadata/instructions, not user turns.
            if role not in {"user", "assistant"}:
                continue

            message = text_content(payload.get("content"))

            if not message:
                continue

            step = {
                "step_id": next_step_id(),
                "source": "user" if role == "user" else "agent",
                "message": message,
            }

            if timestamp:
                step["timestamp"] = timestamp

            steps.append(step)

        elif subtype == "custom_tool_call":
            call_id = payload.get("call_id")

            if not call_id:
                continue

            tool_call = {
                "tool_call_id": call_id,
                "function_name": payload.get("name", "unknown"),
                "arguments": {
                    "raw_input": payload.get("input", "")
                },
            }

            step = {
                "step_id": next_step_id(),
                "source": "agent",
                "tool_calls": [tool_call],
            }

            if timestamp:
                step["timestamp"] = timestamp

            steps.append(step)
            pending_calls[call_id] = step

        elif subtype == "custom_tool_call_output":
            call_id = payload.get("call_id")

            if not call_id:
                continue

            output_text = text_content(payload.get("output"))

            result = {
                "source_call_id": call_id,
                "content": output_text,
            }

            call_step = pending_calls.get(call_id)

            if call_step is not None:
                observation = call_step.setdefault(
                    "observation",
                    {"results": []},
                )
                observation["results"].append(result)

            else:
                # Preserve orphan output rather than silently losing it.
                step = {
                    "step_id": next_step_id(),
                    "source": "agent",
                    "observation": {
                        "results": [result]
                    },
                }

                if timestamp:
                    step["timestamp"] = timestamp

                steps.append(step)

        elif subtype == "reasoning":
            # Codex 0.150.1 may store encrypted reasoning with no plaintext
            # summary. Do not export encrypted_content as reasoning text.
            summary = payload.get("summary")

            if isinstance(summary, list):
                summary_text = text_content(summary)

                if summary_text:
                    step = {
                        "step_id": next_step_id(),
                        "source": "agent",
                        "reasoning_content": summary_text,
                    }

                    if timestamp:
                        step["timestamp"] = timestamp

                    steps.append(step)

    session_id = (
        session_meta.get("id")
        or session_meta.get("session_id")
        or path.stem
    )

    trajectory = {
        "schema_version": "ATIF-v1.7",
        "session_id": str(session_id),
        "agent": {
            "name": "Codex CLI",
            "version": session_meta.get("cli_version", "0.150.1"),
        },
        "steps": steps,
        "extra": {
            "source_format": "codex-cli-jsonl",
            "source_file": path.name,
            "cwd": session_meta.get("cwd"),
            "originator": session_meta.get("originator"),
        },
    }

    return trajectory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")

    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    trajectory = convert(src)

    dst.parent.mkdir(parents=True, exist_ok=True)

    dst.write_text(
        json.dumps(trajectory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    tool_calls = sum(
        len(step.get("tool_calls", []))
        for step in trajectory["steps"]
    )

    observations = sum(
        len(step.get("observation", {}).get("results", []))
        for step in trajectory["steps"]
    )

    users = sum(
        step["source"] == "user"
        for step in trajectory["steps"]
    )

    print(f"Wrote {dst}")
    print(f"steps:        {len(trajectory['steps'])}")
    print(f"user steps:   {users}")
    print(f"tool calls:   {tool_calls}")
    print(f"observations: {observations}")


if __name__ == "__main__":
    main()
