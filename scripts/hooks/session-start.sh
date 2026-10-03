#!/usr/bin/env bash
# SessionStart hook: if the project has specs, put a one-screen dashboard into context so the
# session knows what is in flight without being asked. Silent when there are no specs.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
[[ -d .claude/specs ]] || exit 0
ls -d .claude/specs/*/ >/dev/null 2>&1 || exit 0
echo "spec-engine: specs in this project (python3 ${ROOT}/scripts/spec-state.py status <name> for detail):"
python3 "$ROOT/scripts/spec-state.py" dashboard 2>/dev/null | head -20
exit 0
