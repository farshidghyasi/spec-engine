#!/usr/bin/env bash
# Stop hook. While a spec is executing (marker .claude/specs/<name>/.executing),
# refuse to end the turn if tasks in the current batch are in_progress or
# completed-but-unwired. The orchestrator must finish verification or abort with
# `spec-state exec-end`. Fails open on any error. Ignores markers older than 6h.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
input="$(cat)"
printf '%s' "$input" | grep -q '"stop_hook_active": *true' && exit 0

for marker in .claude/specs/*/.executing; do
  [[ -f "$marker" ]] || continue
  [[ -n "$(find "$marker" -mmin +360 2>/dev/null)" ]] && continue
  spec="$(basename "$(dirname "$marker")")"
  open="$(python3 "$ROOT/scripts/spec-state.py" open-batch "$spec" 2>/dev/null)" && continue
  python3 -c 'import json,sys
print(json.dumps({"decision":"block","reason":sys.argv[1]}))' \
    "spec-engine: spec '$spec' is mid-execution with unfinished batch tasks: $open. Run verify-wired --apply / set-task to finalize them, or 'spec-state exec-end $spec' to abort."
  exit 0
done
exit 0
