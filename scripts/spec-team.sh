#!/bin/bash
set -euo pipefail

# spec-team.sh — 4-agent team execution with duplicate prevention and checkpoint recovery
# Business logic lives in skills/spec-team/SKILL.md

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
    *) echo "Usage: spec-team.sh [--spec-name <name>] [--max-iterations N] [--no-worktree] [--no-skip-permissions]"; exit 1 ;;
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

# --- Duplicate team prevention ---
PROJECT_HASH=$(echo -n "$(pwd)" | shasum -a 256 | cut -c1-8)
TIMESTAMP=$(date +%s)
TEAM_META_DIR="$HOME/.claude/team-meta"
mkdir -p "$TEAM_META_DIR"

LOCK_PATTERN="${PROJECT_HASH}-${SPEC_NAME}"
for meta_file in "$TEAM_META_DIR/$LOCK_PATTERN"-*.json; do
  [ -f "$meta_file" ] || continue
  OLD_PID=$(python3 -c "import json; print(json.load(open('$meta_file')).get('pid',''))" 2>/dev/null || true)
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Error: Another spec-team is already running for this project+spec (PID $OLD_PID)"
    echo "Run 'kill $OLD_PID' to stop it first."
    exit 1
  elif [ -n "$OLD_PID" ]; then
    rm -f "$meta_file"
  fi
done

TEAM_META_FILE="$TEAM_META_DIR/${LOCK_PATTERN}-${TIMESTAMP}.json"
cat > "$TEAM_META_FILE" << METAEOF
{"pid": $$, "project": "$(pwd)", "spec": "$SPEC_NAME", "started": "$TIMESTAMP"}
METAEOF

cleanup() {
  rm -f "$TEAM_META_FILE"
}
trap cleanup EXIT

# --- Setup ---
source "$SCRIPT_DIR/lib/deps.sh"
source "$SCRIPT_DIR/lib/worktree.sh"
source "$SCRIPT_DIR/lib/checkpoint.sh"

check_dependencies "$SPEC_NAME"
setup_worktree "$SPEC_NAME" "$USE_WORKTREE"
cd "$WORK_DIR"

create_checkpoint 1 "$WORK_DIR"

CLAUDE_FLAGS="-p"
if [[ "$SKIP_PERMISSIONS" == "true" ]]; then
  CLAUDE_FLAGS="--dangerously-skip-permissions -p"
fi

echo "=== Starting Spec Team for: $SPEC_NAME ==="
echo "Project: $(pwd)"
echo "Team: Implementer + Tester + Reviewer + Debugger"
echo ""

claude $CLAUDE_FLAGS "Run /spec-team for spec '$SPEC_NAME' with max iterations $MAX_ITERATIONS."

echo ""
echo "=== spec-team session ended ==="

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
