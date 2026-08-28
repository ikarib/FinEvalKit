#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}/sessions"

RAW_DIR="$ROOT/trajectories/raw"
ATIF_DIR="$ROOT/trajectories/atif"

mkdir -p "$RAW_DIR" "$ATIF_DIR"

found=0
failed=0

while IFS= read -r -d '' session; do
    # Find the cwd from session_meta anywhere near the beginning.
    cwd="$(
        jq -r '
          select(.type == "session_meta")
          | .payload.cwd // empty
        ' "$session" 2>/dev/null | head -1
    )"

    [[ "$cwd" == "$ROOT" ]] || continue

    ((found += 1))

    name="$(basename "$session")"
    raw="$RAW_DIR/$name"
    atif="$ATIF_DIR/${name%.jsonl}.trajectory.json"

    echo
    echo "=== $name ==="

    # Preserve the original Codex source exactly.
    cp -p "$session" "$raw"

    raw_calls="$(
        jq -s '
          [
            .[]
            | select(
              .type == "response_item"
              and .payload.type == "custom_tool_call"
            )
          ] | length
        ' "$raw"
    )"

    raw_outputs="$(
        jq -s '
          [
            .[]
            | select(
              .type == "response_item"
              and .payload.type == "custom_tool_call_output"
            )
          ] | length
        ' "$raw"
    )"

    python "$ROOT/scripts/codex_to_atif.py" "$raw" "$atif"

    atif_calls="$(
        jq '
          [.steps[].tool_calls // [] | length] | add // 0
        ' "$atif"
    )"

    atif_outputs="$(
        jq '
          [.steps[].observation?.results[]?] | length
        ' "$atif"
    )"

    echo "raw calls:          $raw_calls"
    echo "raw outputs:        $raw_outputs"
    echo "ATIF calls:         $atif_calls"
    echo "ATIF observations:  $atif_outputs"

    if [[ "$raw_calls" != "$atif_calls" ||
          "$raw_outputs" != "$atif_outputs" ]]; then
        echo "ERROR: trajectory integrity mismatch" >&2
        ((failed += 1))
    else
        echo "OK"
    fi

done < <(
    find "$CODEX_ROOT" \
      -type f \
      -name 'rollout-*.jsonl' \
      -print0
)

echo
echo "================================"
echo "FinEvalKit sessions found: $found"
echo "Integrity failures:         $failed"

if [[ "$failed" -ne 0 ]]; then
    exit 1
fi

python "$ROOT/scripts/generate_trajectory_manifest.py"
