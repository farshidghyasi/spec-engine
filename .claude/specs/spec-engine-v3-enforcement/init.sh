#!/bin/bash
# init.sh - Project configuration for spec-engine execution
#
# This file tells spec-engine how to build, test, and lint your project.
# Uncomment and customize the relevant lines for your tech stack.
# These values are read into state.json and used by quality gates.

# ==============================================================================
# QUALITY GATES — NEW FORMAT (recommended)
# ==============================================================================
# Define gates as an array of "name:command" entries.
# Gates run in order after every implementation iteration.
# If a gate fails, the debugger agent attempts to fix the issue.
#
# gates=("lint:npm run lint" "typecheck:npx tsc --noEmit" "test:npm test")
# gates=("lint:ruff check ." "typecheck:mypy ." "test:pytest")
# gates=("lint:golangci-lint run" "test:go test ./...")

# ==============================================================================
# QUALITY GATES — LEGACY FORMAT (still supported)
# ==============================================================================
# If you prefer individual variables, these are auto-converted to the gates
# array format at runtime. Both formats work; if gates= is defined, it wins.
#
# lint_cmd="npm run lint"
# typecheck_cmd="npx tsc --noEmit"
# test_cmd="npm test"

# ==============================================================================
# DEVELOPMENT SERVER
# ==============================================================================
# dev_cmd="npm run dev"
# dev_cmd="python manage.py runserver"
# dev_cmd="go run ./cmd/server"

# ==============================================================================
# DEPENDENCY INSTALLATION
# ==============================================================================
# install_cmd="npm install"
# install_cmd="pip install -r requirements.txt"
# install_cmd="go mod download"

# ==============================================================================
# EXECUTION CONTROLS
# ==============================================================================
# Maximum token budget for autonomous execution (optional)
# budget_cap=500000

# Pause for human approval every N completed tasks (default: 5)
# human_checkpoint_interval=5

# ==============================================================================
# BASH ALLOWLIST
# ==============================================================================
# Commands that implementation agents are allowed to run.
# Only these commands (plus git, ls, cat, head, tail) are permitted.
# allowed_commands="npm,npx,node,python,pip,pytest,go,make,curl"

# ==============================================================================
# LIFECYCLE HOOKS (optional)
# ==============================================================================
# Shell commands executed at lifecycle events. Best-effort (non-blocking).
# Each hook receives event-specific arguments (see docs).
#
# hook_on_wave_start=""      # args: spec_name, wave_number
# hook_on_task_complete=""   # args: spec_name, task_id, status
# hook_on_spec_complete=""   # args: spec_name, final_status
#
# Example: hook_on_spec_complete="bash .claude/hooks/slack-notify.sh"
