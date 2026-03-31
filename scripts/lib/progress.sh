#!/usr/bin/env bash
# lib/progress.sh — Structured progress event emitter
# Source this file; do not execute directly.
#
# Emits formatted progress lines to stdout and optionally writes to a log file.
# Events: WAVE_START, TASK_START, TASK_COMPLETE, GATE_PASS, GATE_FAIL, WAVE_COMPLETE, SPEC_COMPLETE

# _progress_timestamp()
# Returns HH:MM:SS formatted timestamp.
_progress_timestamp() {
  date +"%H:%M:%S"
}

# emit_progress(spec_dir, event, details...)
# Writes a structured progress line to stdout and appends to progress.log.
emit_progress() {
  local spec_dir="$1"
  local event="$2"
  shift 2
  local details="$*"

  local ts
  ts="$(_progress_timestamp)"
  local line="[$ts] ▸ $event │ $details"

  echo "$line"

  # Append to progress.log if spec_dir is provided
  if [[ -n "$spec_dir" && -d "$spec_dir" ]]; then
    echo "$line" >> "$spec_dir/progress.log"
  fi
}

# emit_wave_start(spec_dir, wave_num, total_waves, pending_tasks)
emit_wave_start() {
  local spec_dir="$1"
  local wave="$2"
  local total="$3"
  local tasks="$4"
  emit_progress "$spec_dir" "WAVE_START" "Wave $wave/$total │ $tasks pending tasks"
}

# emit_task_start(spec_dir, task_id, description, file_list)
emit_task_start() {
  local spec_dir="$1"
  local task_id="$2"
  local desc="$3"
  local files="$4"
  emit_progress "$spec_dir" "TASK_START" "$task_id $desc ($files)"
}

# emit_task_complete(spec_dir, task_id, status, completed_count, total_count)
emit_task_complete() {
  local spec_dir="$1"
  local task_id="$2"
  local status="$3"
  local done="$4"
  local total="$5"
  emit_progress "$spec_dir" "TASK_COMPLETE" "$task_id $status │ $done/$total tasks done"
}

# emit_gate_result(spec_dir, gate_name, result)
emit_gate_result() {
  local spec_dir="$1"
  local gate="$2"
  local result="$3"
  if [[ "$result" == "pass" ]]; then
    emit_progress "$spec_dir" "GATE_PASS" "$gate ✓"
  else
    emit_progress "$spec_dir" "GATE_FAIL" "$gate ✗"
  fi
}

# emit_wave_complete(spec_dir, wave_num, total_waves)
emit_wave_complete() {
  local spec_dir="$1"
  local wave="$2"
  local total="$3"
  emit_progress "$spec_dir" "WAVE_COMPLETE" "Wave $wave/$total done"
}

# emit_spec_complete(spec_dir, spec_name, total_tasks, total_tokens)
emit_spec_complete() {
  local spec_dir="$1"
  local name="$2"
  local tasks="$3"
  local tokens="$4"
  emit_progress "$spec_dir" "SPEC_COMPLETE" "$name │ $tasks tasks │ $tokens tokens"
}
