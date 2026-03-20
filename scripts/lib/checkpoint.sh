#!/usr/bin/env bash
# lib/checkpoint.sh — Checkpoint commit creation and rollback for crash recovery
# Source this file; do not execute directly.

# create_checkpoint(iteration, work_dir)
# Stages all changes and creates a checkpoint commit before an iteration.
# Sets CHECKPOINT_SHA to the commit hash, or empty string if no changes existed.
create_checkpoint() {
  local iteration="$1"
  local work_dir="$2"

  CHECKPOINT_SHA=""

  if [[ -z "$(git -C "$work_dir" status --porcelain)" ]]; then
    return 0
  fi

  git -C "$work_dir" add -A
  if git -C "$work_dir" commit -m "checkpoint: pre-iteration $iteration" >/dev/null 2>&1; then
    CHECKPOINT_SHA="$(git -C "$work_dir" rev-parse HEAD)"
    echo "Created checkpoint: pre-iteration $iteration ($CHECKPOINT_SHA)"
  else
    echo "Warning: checkpoint commit failed for iteration $iteration, continuing without checkpoint" >&2
  fi
}

# handle_checkpoint_recovery(exit_code, checkpoint_sha, iteration, work_dir)
# Rolls back to checkpoint if Claude exited non-zero and a checkpoint exists.
handle_checkpoint_recovery() {
  local exit_code="$1"
  local checkpoint_sha="$2"
  local iteration="$3"
  local work_dir="$4"

  if [[ "$exit_code" -eq 0 ]] || [[ -z "$checkpoint_sha" ]]; then
    return 0
  fi

  if git -C "$work_dir" reset --hard "$checkpoint_sha" >/dev/null 2>&1; then
    echo "Rolled back to checkpoint: pre-iteration $iteration" >&2
  else
    echo "CRITICAL: git reset --hard failed. Manually inspect branch in: $work_dir" >&2
  fi
}

# verify_state_updated(spec_dir, hash_before)
# Checks if state.json was updated during the iteration.
# If not, appends a fallback audit log entry.
verify_state_updated() {
  local spec_dir="$1"
  local hash_before="$2"
  local state_file="$spec_dir/state.json"

  if [[ ! -f "$state_file" ]]; then
    return 0
  fi

  local hash_after
  hash_after=$(md5 -q "$state_file" 2>/dev/null || md5sum "$state_file" 2>/dev/null | cut -d' ' -f1)

  if [[ "$hash_before" == "$hash_after" ]]; then
    echo "WARNING: state.json was not updated this iteration — appending fallback audit entry."
    # Use python3 to safely append to the audit_log array
    python3 -c "
import json, datetime
with open('$state_file', 'r') as f:
    state = json.load(f)
state.setdefault('audit_log', []).append({
    'event': 'fallback_log',
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'note': 'state.json was not updated by this iteration — possible agent crash or timeout'
})
with open('$state_file', 'w') as f:
    json.dump(state, f, indent=2)
" 2>/dev/null || echo "Warning: could not append fallback audit entry" >&2
  fi
}

# snapshot_state(spec_dir)
# Captures a hash of state.json before an iteration. Prints the hash to stdout.
snapshot_state() {
  local spec_dir="$1"
  local state_file="$spec_dir/state.json"

  if [[ -f "$state_file" ]]; then
    md5 -q "$state_file" 2>/dev/null || md5sum "$state_file" 2>/dev/null | cut -d' ' -f1
  fi
}
