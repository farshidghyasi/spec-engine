#!/bin/bash
set -euo pipefail

# spec-exec.sh — Single iteration with worktree isolation and checkpoint recovery
# Business logic lives in skills/spec-exec/SKILL.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_NAME=""
USE_WORKTREE=true
SKIP_PERMISSIONS=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --spec-name) SPEC_NAME="$2"; shift 2 ;;
    --no-worktree) USE_WORKTREE=false; shift ;;
    --yolo) SKIP_PERMISSIONS=true; shift ;;
    *) echo "Usage: spec-exec.sh [--spec-name <name>] [--no-worktree] [--yolo]"; exit 1 ;;
  esac
done

# auto-detect spec if not provided
if [[ -z "$SPEC_NAME" ]]; then
  if [[ ! -d ".claude/specs" ]]; then
    echo "Error: No .claude/specs directory found. Run /spec <name> first."
    exit 1
  fi
  SPECS=($(ls -d .claude/specs/*/ 2>/dev/null | xargs -I{} basename {}))
  if [[ ${#SPECS[@]} -eq 0 ]]; then
    echo "Error: No specs found in .claude/specs/"
    exit 1
  elif [[ ${#SPECS[@]} -eq 1 ]]; then
    SPEC_NAME="${SPECS[0]}"
    echo "Auto-detected spec: $SPEC_NAME"
  else
    echo "Error: Multiple specs found. Specify one with --spec-name:"
    printf "  %s\n" "${SPECS[@]}"
    exit 1
  fi
fi

if [[ ! "$SPEC_NAME" =~ ^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]?$ ]]; then
  echo "Error: Invalid spec name. Use lowercase alphanumeric, hyphens, dots, underscores."
  exit 1
fi

SPEC_DIR=".claude/specs/$SPEC_NAME"
if [[ ! -d "$SPEC_DIR" ]]; then
  echo "Error: Spec not found: $SPEC_DIR"
  exit 1
fi

# source shared libraries
source "$SCRIPT_DIR/lib/deps.sh"
source "$SCRIPT_DIR/lib/worktree.sh"
source "$SCRIPT_DIR/lib/checkpoint.sh"

# check cross-spec dependencies
check_dependencies "$SPEC_NAME"

# setup worktree
setup_worktree "$SPEC_NAME" "$USE_WORKTREE"
cd "$WORK_DIR"

# snapshot state.json before iteration
STATE_HASH_BEFORE=$(snapshot_state "$SPEC_DIR")

# create checkpoint
create_checkpoint 1 "$WORK_DIR"

CLAUDE_FLAGS="-p"
if [[ "$SKIP_PERMISSIONS" == "true" ]]; then
  CLAUDE_FLAGS="--dangerously-skip-permissions -p"
  echo "WARNING: Running with --dangerously-skip-permissions (--yolo mode)"
fi

echo "=== Running spec-exec for: $SPEC_NAME ==="

OUTPUT_FILE=$(mktemp)
trap "rm -f $OUTPUT_FILE" EXIT

set +e
claude $CLAUDE_FLAGS "Run /spec-exec for spec '$SPEC_NAME'." | tee "$OUTPUT_FILE"
CLAUDE_EXIT=${PIPESTATUS[0]}
set -e

# recover on failure
handle_checkpoint_recovery "$CLAUDE_EXIT" "$CHECKPOINT_SHA" 1 "$WORK_DIR"

# verify state.json was updated
verify_state_updated "$SPEC_DIR" "$STATE_HASH_BEFORE"

# check for completion
if [[ -f "$SPEC_DIR/state.json" ]]; then
  PENDING=$(python3 -c "
import json
with open('$SPEC_DIR/state.json') as f:
    state = json.load(f)
print(sum(1 for t in state.get('tasks',{}).values() if t.get('status') != 'completed'))
" 2>/dev/null || echo "?")
  if [[ "$PENDING" == "0" ]]; then
    echo ""
    echo "All tasks complete!"
    print_pr_suggestion "$SPEC_NAME"
  fi
fi
