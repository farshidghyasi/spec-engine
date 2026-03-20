#!/usr/bin/env bash
# lib/deps.sh — Cross-spec dependency checking with cycle detection
# Source this file; do not execute directly.

# _parse_depends_on(spec_name)
# Parses the "## Depends On" section from requirements.md.
# Outputs one dependency name per line.
_parse_depends_on() {
  local spec_name="$1"
  local req_file=".claude/specs/$spec_name/requirements.md"

  if [[ ! -f "$req_file" ]]; then
    return 0
  fi

  local in_section=false
  while IFS= read -r line; do
    if [[ "$line" == "## Depends On" ]]; then
      in_section=true
      continue
    fi
    if $in_section && [[ "$line" =~ ^## ]]; then
      break
    fi
    if $in_section && [[ "$line" =~ ^-\ +(.+)$ ]]; then
      local dep="${BASH_REMATCH[1]}"
      dep="$(echo "$dep" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      # skip comments
      [[ "$dep" =~ ^!-- ]] && continue
      [[ -n "$dep" ]] && echo "$dep"
    fi
  done < "$req_file"
}

# _check_spec_complete(spec_name)
# Returns 0 if all tasks in the spec are complete. Outputs "completed:total".
_check_spec_complete() {
  local spec_name="$1"
  local state_file=".claude/specs/$spec_name/state.json"

  # prefer state.json (spec-engine native)
  if [[ -f "$state_file" ]]; then
    python3 -c "
import json, sys
with open('$state_file') as f:
    state = json.load(f)
tasks = state.get('tasks', {})
total = len(tasks)
completed = sum(1 for t in tasks.values() if t.get('status') == 'completed')
print(f'{completed}:{total}')
sys.exit(0 if total > 0 and completed == total else 1)
" 2>/dev/null
    return $?
  fi

  # fallback: parse tasks.md (compatibility with spec-driven v3)
  local tasks_file=".claude/specs/$spec_name/tasks.md"
  if [[ ! -f "$tasks_file" ]]; then
    echo "0:0"
    return 1
  fi

  local total=0 completed=0 current_status=""
  while IFS= read -r line; do
    if [[ "$line" =~ ^###\ T-[0-9]+ ]]; then
      if [[ -n "$current_status" ]]; then
        total=$((total + 1))
        [[ "$current_status" == "completed" ]] && completed=$((completed + 1))
      fi
      current_status=""
    elif [[ "$line" =~ ^\-\ \*\*Status\*\*:\ (.+)$ ]]; then
      current_status="${BASH_REMATCH[1]}"
    fi
  done < "$tasks_file"
  # handle last task
  if [[ -n "$current_status" ]]; then
    total=$((total + 1))
    [[ "$current_status" == "completed" ]] && completed=$((completed + 1))
  fi

  echo "$completed:$total"
  [[ "$total" -gt 0 && "$completed" -eq "$total" ]] && return 0 || return 1
}

# _detect_cycle(spec_name, visited_dir, path_dir, chain)
# DFS-based circular dependency detection.
_detect_cycle() {
  local spec_name="$1"
  local visited_dir="$2"
  local path_dir="$3"
  local chain="$4"

  if [[ -f "$path_dir/$spec_name" ]]; then
    echo "Error: Circular dependency detected: $chain -> $spec_name" >&2
    return 1
  fi

  if [[ -f "$visited_dir/$spec_name" ]]; then
    return 0
  fi

  touch "$path_dir/$spec_name"
  touch "$visited_dir/$spec_name"

  local deps
  deps="$(_parse_depends_on "$spec_name")"
  if [[ -n "$deps" ]]; then
    while IFS= read -r dep; do
      [[ -n "$dep" ]] && _detect_cycle "$dep" "$visited_dir" "$path_dir" "$chain -> $spec_name" || return 1
    done <<< "$deps"
  fi

  rm -f "$path_dir/$spec_name"
  return 0
}

# check_dependencies(spec_name)
# Checks all dependencies are met. Exits 1 if not.
check_dependencies() {
  local spec_name="$1"
  local deps
  deps="$(_parse_depends_on "$spec_name")"

  [[ -z "$deps" ]] && return 0

  # cycle detection
  local tmp_visited tmp_path
  tmp_visited="$(mktemp -d)"
  tmp_path="$(mktemp -d)"
  trap "rm -rf '$tmp_visited' '$tmp_path'" RETURN

  touch "$tmp_path/$spec_name"
  touch "$tmp_visited/$spec_name"

  while IFS= read -r dep; do
    [[ -z "$dep" ]] && continue
    _detect_cycle "$dep" "$tmp_visited" "$tmp_path" "$spec_name" || exit 1
  done <<< "$deps"

  rm -rf "$tmp_visited" "$tmp_path"
  trap - RETURN

  # check completeness
  local has_failure=false
  while IFS= read -r dep; do
    [[ -z "$dep" ]] && continue

    if [[ ! -d ".claude/specs/$dep" ]]; then
      echo "Error: Dependency spec not found: $dep" >&2
      exit 1
    fi

    local counts
    counts="$(_check_spec_complete "$dep")" || true
    local completed="${counts%%:*}"
    local total="${counts##*:}"

    if [[ "$total" -eq 0 ]] || [[ "$completed" -ne "$total" ]]; then
      echo "Error: Dependency incomplete: $dep ($completed/$total tasks completed)" >&2
      has_failure=true
    fi
  done <<< "$deps"

  if $has_failure; then
    exit 1
  fi
}

# get_dependency_status(spec_name)
# Outputs one line per dependency: dep_name:status:completed:total
get_dependency_status() {
  local spec_name="$1"
  local deps
  deps="$(_parse_depends_on "$spec_name")"

  [[ -z "$deps" ]] && return 0

  while IFS= read -r dep; do
    [[ -z "$dep" ]] && continue

    if [[ ! -d ".claude/specs/$dep" ]]; then
      echo "$dep:not_found:0:0"
      continue
    fi

    local counts
    counts="$(_check_spec_complete "$dep")" || true
    local completed="${counts%%:*}"
    local total="${counts##*:}"

    if [[ "$total" -gt 0 && "$completed" -eq "$total" ]]; then
      echo "$dep:complete:$completed:$total"
    else
      echo "$dep:incomplete:$completed:$total"
    fi
  done <<< "$deps"
}
