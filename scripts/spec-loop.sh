#!/bin/bash
set -euo pipefail

# spec-loop.sh — Wave-based execution loop with checkpoints and crash recovery
# Business logic lives in skills/spec-loop/SKILL.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_NAME=""
USE_WORKTREE=true
MAX_ITERATIONS=50
SKIP_PERMISSIONS=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --spec-name) SPEC_NAME="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --no-worktree) USE_WORKTREE=false; shift ;;
    --yolo) shift ;; # backward compat — autonomous is now the default
    --no-skip-permissions) SKIP_PERMISSIONS=false; shift ;;
    *) echo "Usage: spec-loop.sh [--spec-name <name>] [--max-iterations N] [--no-worktree] [--no-skip-permissions]"; exit 1 ;;
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

OUTPUT_FILE=$(mktemp)
trap "rm -f $OUTPUT_FILE" EXIT

CLAUDE_FLAGS="-p"
if [[ "$SKIP_PERMISSIONS" == "true" ]]; then
  CLAUDE_FLAGS="--dangerously-skip-permissions -p"
fi

echo "=== Starting spec-loop for: $SPEC_NAME (max $MAX_ITERATIONS iterations) ==="

claude $CLAUDE_FLAGS "Run /spec-loop for spec '$SPEC_NAME' with max iterations $MAX_ITERATIONS."

echo ""
echo "=== spec-loop session ended ==="

# check final state
if [[ -f "$SPEC_DIR/state.json" ]]; then
  PENDING=$(python3 -c "
import json
with open('$SPEC_DIR/state.json') as f:
    state = json.load(f)
tasks = state.get('tasks', {})
total = len(tasks)
completed = sum(1 for t in tasks.values() if t.get('status') == 'completed')
print(f'{completed}/{total}')
" 2>/dev/null || echo "?/?")
  echo "Tasks completed: $PENDING"
  print_pr_suggestion "$SPEC_NAME"
fi
