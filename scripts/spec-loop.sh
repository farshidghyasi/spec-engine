#!/usr/bin/env bash
set -euo pipefail

# spec-loop.sh — headless execution loop: one fresh `claude -p` per iteration.
#
# Each iteration runs one wave batch via /spec-exec (or /spec-team with --team),
# then this script records real token usage, enforces the budget cap, detects
# crashes and stalls, and stops when spec-state reports completion.
# Business logic lives in references/execution-core.md; this file only loops.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SS="python3 $SCRIPT_DIR/spec-state.py"
SPEC_NAME=""
MAX_ITERATIONS=50
USE_WORKTREE=true
SKIP_PERMISSIONS=true
TEAM=false
ALLOW_DIRTY=false

usage() {
  echo "Usage: spec-loop.sh [--spec-name <name>] [--max-iterations N] [--team] [--no-worktree] [--no-skip-permissions] [--allow-dirty]"
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --spec-name) SPEC_NAME="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --team) TEAM=true; shift ;;
    --no-worktree) USE_WORKTREE=false; shift ;;
    --no-skip-permissions) SKIP_PERMISSIONS=false; shift ;;
    --allow-dirty) ALLOW_DIRTY=true; shift ;;
    --yolo) shift ;; # backward compat — autonomous is the default
    -h|--help) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac
done

command -v claude >/dev/null || { echo "Error: 'claude' CLI not found in PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Error: python3 is required" >&2; exit 1; }

# resolve spec (auto-detect when exactly one exists)
SPEC_NAME="$($SS get ${SPEC_NAME:+"$SPEC_NAME"} spec_name)" || exit 1
SPEC_DIR=".claude/specs/$SPEC_NAME"

# single-runner lock per spec
LOCK="$SPEC_DIR/.lock"
if [[ -f "$LOCK" ]]; then
  OLD_PID="$(cat "$LOCK" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Error: spec-loop already running for '$SPEC_NAME' (PID $OLD_PID)" >&2
    exit 1
  fi
fi
echo $$ > "$LOCK"

# shellcheck source=scripts/lib/worktree.sh
source "$SCRIPT_DIR/lib/worktree.sh"
setup_worktree "$SPEC_NAME" "$USE_WORKTREE"
cd "$WORK_DIR"
# the lock lives in the original checkout; keep its path absolute for cleanup
LOCK="$(cd "$(dirname "$OLDPWD/$LOCK")" 2>/dev/null && pwd)/$(basename "$LOCK")" || true

OUT="$(mktemp)"
cleanup() {
  rm -f "$OUT" "$LOCK"
  $SS exec-end "$SPEC_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [[ "$ALLOW_DIRTY" != "true" && -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "Error: working tree has uncommitted changes. Commit or stash them, or pass --allow-dirty." >&2
  echo "       (crash recovery resets to the pre-iteration commit; uncommitted work would be lost)" >&2
  exit 1
fi

$SS deps "$SPEC_NAME"
$SS phase-gate "$SPEC_NAME" validated
if [[ "$($SS get "$SPEC_NAME" quality_gates.baseline_errors)" == "{}" ]]; then
  echo "Recording quality-gate baseline..."
  $SS run-gates "$SPEC_NAME" --baseline || true
fi
$SS exec-start "$SPEC_NAME"

CLAUDE_FLAGS=(-p --output-format json)
[[ "$SKIP_PERMISSIONS" == "true" ]] && CLAUDE_FLAGS+=(--dangerously-skip-permissions)
if [[ "$TEAM" == "true" ]]; then
  PROMPT="Run /spec-team for spec '$SPEC_NAME'. Execute exactly one wave batch, then stop."
else
  PROMPT="Run /spec-exec for spec '$SPEC_NAME'."
fi

echo "=== spec-loop: $SPEC_NAME (max $MAX_ITERATIONS iterations, team=$TEAM) ==="
CRASHES=0
STALLS=0
DONE=false
for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  if $SS complete "$SPEC_NAME" >/dev/null 2>&1; then DONE=true; break; fi
  $SS budget-ok "$SPEC_NAME" || { echo "Stopping: budget cap reached."; break; }

  HEAD_BEFORE="$(git rev-parse HEAD)"
  HASH_BEFORE="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$SPEC_DIR/state.json")"
  echo ""
  echo "=== iteration $i/$MAX_ITERATIONS ==="

  set +e
  claude "${CLAUDE_FLAGS[@]}" "$PROMPT" > "$OUT"
  RC=$?
  set -e

  # surface the assistant's final text and account real token usage
  TOKENS="$(python3 - "$OUT" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print(0); sys.exit()
u = d.get("usage") or {}
print(int(u.get("input_tokens", 0)) + int(u.get("output_tokens", 0)) + int(u.get("cache_read_input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)))
r = d.get("result")
if r:
    print("\n--- assistant ---\n" + str(r)[-4000:] + "\n-----------------", file=sys.stderr)
if d.get("is_error"):
    print("claude reported is_error=true", file=sys.stderr)
PY
)"
  $SS tokens-add "$SPEC_NAME" "${TOKENS:-0}" --iteration >/dev/null

  if [[ $RC -ne 0 ]]; then
    CRASHES=$((CRASHES + 1))
    echo "Iteration $i failed (exit $RC). Rolling back to $HEAD_BEFORE." >&2
    # keep the audit log and token accounting across the rollback
    STATE_BACKUP="$(mktemp)"; cp "$SPEC_DIR/state.json" "$STATE_BACKUP"
    git reset -q --hard "$HEAD_BEFORE"
    cp "$STATE_BACKUP" "$SPEC_DIR/state.json"; rm -f "$STATE_BACKUP"
    $SS log "$SPEC_NAME" iteration_failed --details "exit $RC, rolled back to $HEAD_BEFORE" || true
    [[ $CRASHES -ge 2 ]] && { echo "Stopping: 2 consecutive crashes." >&2; break; }
    continue
  fi
  CRASHES=0

  HASH_AFTER="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$SPEC_DIR/state.json")"
  # tokens-add always rewrites state.json, so compare task statuses instead
  if [[ "$(git diff --quiet HEAD "$HEAD_BEFORE" -- . ':!'"$SPEC_DIR" 2>/dev/null; echo $?)" == "0" && "$HASH_BEFORE" == "$HASH_AFTER" ]]; then
    STALLS=$((STALLS + 1))
    $SS log "$SPEC_NAME" fallback_log --details "iteration $i produced no code changes and no state change" || true
    [[ $STALLS -ge 2 ]] && { echo "Stopping: 2 iterations without progress." >&2; break; }
  else
    STALLS=0
  fi
done

echo ""
$SS status "$SPEC_NAME" | head -4
if [[ "$DONE" == "true" ]] || $SS complete "$SPEC_NAME" >/dev/null 2>&1; then
  echo "All tasks complete."
  print_pr_suggestion "$SPEC_NAME"
else
  echo "Loop ended before completion. Re-run to resume; state.json carries the position."
fi
