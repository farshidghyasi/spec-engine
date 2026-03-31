#!/usr/bin/env bash
# lib/gates.sh — Backward-compatible quality gate reader
# Source this file; do not execute directly.
#
# Supports two formats:
#   NEW: gates=("lint:npm run lint" "typecheck:npx tsc --noEmit" "test:npm test")
#   OLD: lint_cmd="npm run lint"  typecheck_cmd="npx tsc --noEmit"  test_cmd="npm test"
#
# get_gates() reads init.sh and outputs one "name:command" per line.
# Consumers iterate lines instead of reading individual variables.

# get_gates(init_sh_path)
# Reads init.sh and outputs normalized gate entries, one per line: "name:command"
get_gates() {
  local init_sh="$1"

  if [[ ! -f "$init_sh" ]]; then
    return 0
  fi

  # Try new format first: gates=("name:cmd" ...)
  if grep -q '^gates=(' "$init_sh" 2>/dev/null; then
    # Source the file in a subshell to extract the array
    (
      # shellcheck disable=SC1090
      source "$init_sh" 2>/dev/null
      for entry in "${gates[@]}"; do
        echo "$entry"
      done
    )
    return 0
  fi

  # Fall back to old format: lint_cmd, typecheck_cmd, test_cmd, integration_cmd
  (
    # shellcheck disable=SC1090
    source "$init_sh" 2>/dev/null
    [[ -n "${lint_cmd:-}" ]] && echo "lint:$lint_cmd"
    [[ -n "${typecheck_cmd:-}" ]] && echo "typecheck:$typecheck_cmd"
    [[ -n "${test_cmd:-}" ]] && echo "test:$test_cmd"
    [[ -n "${integration_cmd:-}" ]] && echo "integration:$integration_cmd"
  )
}

# get_gate_cmd(init_sh_path, gate_name)
# Returns the command for a specific gate, or empty string if not found.
get_gate_cmd() {
  local init_sh="$1"
  local gate_name="$2"

  get_gates "$init_sh" | while IFS=: read -r name cmd; do
    if [[ "$name" == "$gate_name" ]]; then
      echo "$cmd"
      return 0
    fi
  done
}

# get_gates_from_state(state_json_path)
# Reads quality gates from state.json. Supports both new gates[] array and old individual fields.
get_gates_from_state() {
  local state_json="$1"

  if [[ ! -f "$state_json" ]]; then
    return 0
  fi

  python3 -c "
import json, sys
with open('$state_json') as f:
    state = json.load(f)
qg = state.get('quality_gates', {})

# Try new format first
gates = qg.get('gates', [])
if gates:
    for entry in gates:
        print(entry)
    sys.exit(0)

# Fall back to old format
for name in ['lint', 'typecheck', 'test', 'integration']:
    cmd = qg.get(f'{name}_cmd')
    if cmd:
        print(f'{name}:{cmd}')
" 2>/dev/null
}
