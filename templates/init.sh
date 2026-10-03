#!/bin/bash
# init.sh - Project configuration for spec-engine execution
#
# Read by `scripts/spec-state.py` (gates, run-gates, hook). Uncomment and
# customize for your stack. `spec-state detect-gates` fills this in
# automatically for Node, Python, Rust, Go and Makefile projects.

# ==============================================================================
# QUALITY GATES
# ==============================================================================
# Array of "name:command". Gates run in this order after every wave.
# A gate named "integration" only runs post-wave (smoke test), never per task.
#
# gates=("lint:npm run lint" "typecheck:npx tsc --noEmit" "test:npm test")
# gates=("lint:ruff check ." "typecheck:mypy ." "test:pytest")
# gates=("lint:golangci-lint run" "test:go test ./..." "integration:./scripts/smoke.sh")
#
# Legacy single variables are still accepted: lint_cmd, typecheck_cmd, test_cmd, integration_cmd

# ==============================================================================
# EXECUTION CONTROLS
# ==============================================================================
# Token budget enforced by scripts/spec-loop.sh (reads real usage from `claude -p`).
# Defaults to tasks x 50000 when unset; also stored in state.json.execution.budget_cap.
# budget_cap=500000

# ==============================================================================
# LIFECYCLE HOOKS (optional, best-effort, 30s timeout)
# ==============================================================================
# hook_on_wave_start=""      # args: spec_name, wave_number
# hook_on_task_complete=""   # args: spec_name, task_id, status
# hook_on_spec_complete=""   # args: spec_name, final_status
#
# Example: hook_on_spec_complete="bash .claude/hooks/slack.sh"
