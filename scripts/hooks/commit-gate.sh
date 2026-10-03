#!/usr/bin/env bash
# PreToolUse(Bash) hook.
#  1. Auto-allows calls to our own spec-state CLI so state writes never prompt.
#  2. While a spec is executing, denies `git commit` if that spec's state.json has
#     unstaged changes — state must land in the same commit as the code it describes.
# Fails open: any error exits 0 with no decision.
set -u
input="$(cat)"
cmd="$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null)" || exit 0

emit() { # $1 = allow|deny, $2 = reason
  python3 -c 'import json,sys
print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":sys.argv[1],"permissionDecisionReason":sys.argv[2]}}))' "$1" "$2"
}

case "$cmd" in
  *spec-state.py*) emit allow "spec-engine state CLI"; exit 0 ;;
esac
case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

for marker in .claude/specs/*/.executing; do
  [[ -f "$marker" ]] || continue
  spec="$(basename "$(dirname "$marker")")"
  state=".claude/specs/$spec/state.json"
  if ! git diff --quiet -- "$state" 2>/dev/null; then
    emit deny "spec-engine: $state has unstaged changes. Stage it with the task's files (git add $state) so state and code land in the same commit."
    exit 0
  fi
done
exit 0
