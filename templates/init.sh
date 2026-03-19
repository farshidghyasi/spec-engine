#!/bin/bash
# init.sh - Project configuration for spec-engine execution
#
# This file tells spec-engine how to build, test, and lint your project.
# Uncomment and customize the relevant lines for your tech stack.
# These values are read into state.json and used by quality gates.

# ==============================================================================
# QUALITY GATES (used by spec-exec and spec-loop)
# ==============================================================================
# These commands run automatically after every implementation iteration.
# If a gate fails, the debugger agent attempts to fix the issue.

# Lint command (catches style violations, unused vars, etc.)
# lint_cmd="npm run lint"
# lint_cmd="npx eslint . --ext .ts,.tsx"
# lint_cmd="ruff check ."
# lint_cmd="golangci-lint run"

# Type check command (catches type errors, hallucinated imports)
# typecheck_cmd="npx tsc --noEmit"
# typecheck_cmd="mypy ."
# typecheck_cmd="pyright"

# Test command (runs FULL test suite for regression detection)
# test_cmd="npm test"
# test_cmd="npx vitest run"
# test_cmd="pytest"
# test_cmd="go test ./..."

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
