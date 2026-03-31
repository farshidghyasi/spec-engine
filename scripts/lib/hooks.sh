#!/usr/bin/env bash
# lib/hooks.sh — Lifecycle hook runner
# Source this file; do not execute directly.
#
# Hooks are best-effort (non-blocking). Failures are logged but never halt execution.
# Hook commands receive event-specific arguments.
#
# Supported events:
#   wave_start    — called with: spec_name, wave_number
#   task_complete — called with: spec_name, task_id, status
#   spec_complete — called with: spec_name, final_status

# _load_hooks(init_sh_path)
# Sources init.sh and exports hook variables into the current shell.
_load_hooks() {
  local init_sh="$1"

  if [[ ! -f "$init_sh" ]]; then
    return 0
  fi

  # Source in current shell to set hook_on_* variables
  # shellcheck disable=SC1090
  source "$init_sh" 2>/dev/null || true
}

# run_hook(init_sh_path, event_name, args...)
# Executes the hook for the given event. Best-effort: captures stderr, never fails.
run_hook() {
  local init_sh="$1"
  local event="$2"
  shift 2

  _load_hooks "$init_sh"

  local hook_var="hook_on_${event}"
  local hook_cmd="${!hook_var:-}"

  if [[ -z "$hook_cmd" ]]; then
    return 0
  fi

  # Execute hook in background, capture stderr, timeout after 30s
  (
    timeout 30 bash -c "$hook_cmd" -- "$@" 2>/tmp/spec-hook-stderr.$$ || true
    local stderr
    stderr="$(cat /tmp/spec-hook-stderr.$$ 2>/dev/null)"
    rm -f /tmp/spec-hook-stderr.$$
    if [[ -n "$stderr" ]]; then
      echo "[hook:$event] stderr: $stderr" >&2
    fi
  ) &

  return 0
}

# run_hook_sync(init_sh_path, event_name, args...)
# Like run_hook but waits for completion. Still best-effort (never fails the caller).
run_hook_sync() {
  local init_sh="$1"
  local event="$2"
  shift 2

  _load_hooks "$init_sh"

  local hook_var="hook_on_${event}"
  local hook_cmd="${!hook_var:-}"

  if [[ -z "$hook_cmd" ]]; then
    return 0
  fi

  timeout 30 bash -c "$hook_cmd" -- "$@" 2>&1 || true
}
