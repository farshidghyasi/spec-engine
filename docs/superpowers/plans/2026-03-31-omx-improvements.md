# OMX Comparison Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 13 improvements from the OMX comparison analysis to close gaps in flexibility, observability, and extensibility.

**Architecture:** Layered approach — foundation changes (lib scripts, templates) land first, then new skills build on them. All state.json changes are additive (optional fields with defaults). All init.sh changes are backward-compatible.

**Tech Stack:** Bash (lib scripts), Markdown (SKILL.md files), JSON (state.json/plugin.json templates)

---

## File Map

### New Files
- `scripts/lib/gates.sh` — Backward-compatible quality gate reader
- `scripts/lib/hooks.sh` — Lifecycle hook runner
- `scripts/lib/progress.sh` — Structured event emitter for progress streaming
- `skills/spec-quick/SKILL.md` — Lightweight spec skill
- `skills/spec-session/SKILL.md` — Interactive guided session skill
- `templates/hooks/slack.sh` — Example Slack notification hook
- `templates/hooks/discord.sh` — Example Discord notification hook
- `templates/hooks/webhook.sh` — Example generic webhook hook

### Modified Files
- `templates/init.sh` — Add gates array, hooks section, project-type auto-detection comments
- `templates/state.json` — Add optional `quick_mode`, `gates`, `hooks`, `decomposed_from` fields
- `skills/spec/SKILL.md` — Add `--consensus` flag, codebase-aware template detection
- `skills/spec-loop/SKILL.md` — Add progress streaming, task decomposition on failure, per-wave escalation
- `skills/spec-team/SKILL.md` — Add progress streaming, task decomposition on failure, per-wave escalation
- `skills/spec-exec/SKILL.md` — Add progress streaming, lifecycle hook calls, custom gate support
- `skills/spec-validate/SKILL.md` — Add lessons-to-rules pipeline
- `skills/spec-dashboard/SKILL.md` — Add `--deps` flag for dependency graph
- `skills/spec-refine/SKILL.md` — Add diff-based output
- `.claude-plugin/plugin.json` — Bump version to 2.0.0

---

## Task 1: Create `scripts/lib/gates.sh` — Backward-Compatible Quality Gate Reader

**Files:**
- Create: `scripts/lib/gates.sh`

- [ ] **Step 1: Write the gates library**

```bash
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
  local has_new_format=false
  if grep -q '^gates=(' "$init_sh" 2>/dev/null; then
    has_new_format=true
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
```

- [ ] **Step 2: Verify the script is syntactically valid**

Run: `bash -n scripts/lib/gates.sh`
Expected: No output (clean syntax)

- [ ] **Step 3: Commit**

```bash
git add scripts/lib/gates.sh
git commit -m "feat: add backward-compatible quality gate reader (lib/gates.sh)"
```

---

## Task 2: Create `scripts/lib/hooks.sh` — Lifecycle Hook Runner

**Files:**
- Create: `scripts/lib/hooks.sh`

- [ ] **Step 1: Write the hooks library**

```bash
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
    timeout 30 bash -c "$hook_cmd $*" 2>/tmp/spec-hook-stderr.$$ || true
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

  timeout 30 bash -c "$hook_cmd $*" 2>&1 || true
}
```

- [ ] **Step 2: Verify syntax**

Run: `bash -n scripts/lib/hooks.sh`
Expected: No output (clean syntax)

- [ ] **Step 3: Commit**

```bash
git add scripts/lib/hooks.sh
git commit -m "feat: add lifecycle hook runner (lib/hooks.sh)"
```

---

## Task 3: Create `scripts/lib/progress.sh` — Structured Progress Emitter

**Files:**
- Create: `scripts/lib/progress.sh`

- [ ] **Step 1: Write the progress library**

```bash
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
```

- [ ] **Step 2: Verify syntax**

Run: `bash -n scripts/lib/progress.sh`
Expected: No output (clean syntax)

- [ ] **Step 3: Commit**

```bash
git add scripts/lib/progress.sh
git commit -m "feat: add structured progress event emitter (lib/progress.sh)"
```

---

## Task 4: Update `templates/init.sh` — Add Gates Array, Hooks, and Auto-Detection Comments

**Files:**
- Modify: `templates/init.sh`

- [ ] **Step 1: Rewrite the init.sh template**

Replace the full contents of `templates/init.sh` with:

```bash
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
```

- [ ] **Step 2: Commit**

```bash
git add templates/init.sh
git commit -m "feat: update init.sh template with gates array and lifecycle hooks"
```

---

## Task 5: Update `templates/state.json` — Add Optional Fields

**Files:**
- Modify: `templates/state.json`

- [ ] **Step 1: Update the state.json template**

Replace the full contents of `templates/state.json` with:

```json
{
  "version": 1,
  "spec_name": "{{SPEC_NAME}}",
  "created_at": "{{ISO_TIMESTAMP}}",
  "quick_mode": false,

  "integrity": {
    "requirements_sha256": "",
    "design_sha256": "",
    "tasks_sha256": "",
    "computed_at": ""
  },

  "tasks": {},

  "waves": [],

  "parallel": {
    "max_parallel_agents": 3,
    "shared_files": [],
    "generated_files": [],
    "post_merge_commands": []
  },

  "execution": {
    "current_wave": 0,
    "current_batch": [],
    "iteration": 0,
    "total_tokens": 0,
    "budget_cap": null,
    "started_at": null,
    "last_iteration_at": null,
    "human_checkpoint_interval": 5,
    "tasks_since_checkpoint": 0
  },

  "reproducibility": {
    "plugin_version": "1.0.0",
    "model_versions": {},
    "git_sha_start": null,
    "prompt_hashes": [],
    "referenced_codebase_files": []
  },

  "quality_gates": {
    "gates": [],
    "lint_cmd": null,
    "typecheck_cmd": null,
    "test_cmd": null,
    "dev_cmd": null,
    "integration_cmd": null,
    "baseline_errors": null,
    "allowed_commands": [],
    "last_regression_pass": null
  },

  "lessons_applied": [],

  "audit_log": []
}
```

- [ ] **Step 2: Commit**

```bash
git add templates/state.json
git commit -m "feat: add quick_mode and gates[] to state.json template"
```

---

## Task 6: Create Notification Hook Templates

**Files:**
- Create: `templates/hooks/slack.sh`
- Create: `templates/hooks/discord.sh`
- Create: `templates/hooks/webhook.sh`

- [ ] **Step 1: Create the templates/hooks directory and Slack hook**

```bash
#!/bin/bash
# slack.sh — Example Slack notification hook for spec-engine
# Usage: hook_on_spec_complete="bash .claude/hooks/slack.sh"
#
# Args: spec_name, final_status
# Requires: SLACK_WEBHOOK_URL environment variable

SPEC_NAME="${1:-unknown}"
STATUS="${2:-unknown}"

WEBHOOK="${SLACK_WEBHOOK_URL:?Set SLACK_WEBHOOK_URL to your Slack incoming webhook URL}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"spec-engine: *${SPEC_NAME}* completed with status: ${STATUS}\"}" \
  > /dev/null 2>&1
```

- [ ] **Step 2: Create Discord hook**

```bash
#!/bin/bash
# discord.sh — Example Discord notification hook for spec-engine
# Usage: hook_on_spec_complete="bash .claude/hooks/discord.sh"
#
# Args: spec_name, final_status
# Requires: DISCORD_WEBHOOK_URL environment variable

SPEC_NAME="${1:-unknown}"
STATUS="${2:-unknown}"

WEBHOOK="${DISCORD_WEBHOOK_URL:?Set DISCORD_WEBHOOK_URL to your Discord webhook URL}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "{\"content\": \"spec-engine: **${SPEC_NAME}** completed with status: ${STATUS}\"}" \
  > /dev/null 2>&1
```

- [ ] **Step 3: Create generic webhook hook**

```bash
#!/bin/bash
# webhook.sh — Example generic webhook notification hook for spec-engine
# Usage: hook_on_task_complete="bash .claude/hooks/webhook.sh"
#
# Args vary by event:
#   wave_start:    spec_name, wave_number
#   task_complete: spec_name, task_id, status
#   spec_complete: spec_name, final_status
# Requires: WEBHOOK_URL environment variable

WEBHOOK="${WEBHOOK_URL:?Set WEBHOOK_URL to your webhook endpoint}"

# Send all arguments as JSON
payload="{\"event\": \"spec-engine\", \"args\": [$(printf '"%s",' "$@" | sed 's/,$//')]}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  > /dev/null 2>&1
```

- [ ] **Step 4: Commit**

```bash
git add templates/hooks/
git commit -m "feat: add notification hook templates (Slack, Discord, webhook)"
```

---

## Task 7: Create `/spec-quick` Skill

**Files:**
- Create: `skills/spec-quick/SKILL.md`

- [ ] **Step 1: Write the spec-quick skill**

```markdown
---
name: spec-quick
description: Quick spec mode — skip requirements/design for small tasks
argument-hint: "<description>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-quick Command

Lightweight spec mode for small tasks that don't need full EARS requirements, design docs, or formal validation. Creates a minimal spec and immediately executes.

## Usage

```
/spec-quick <description>
```

**Examples:**
- `/spec-quick "fix the login button alignment on mobile"`
- `/spec-quick "add created_at timestamp to user model"`
- `/spec-quick "update the footer copyright year"`

## When to Use

Use `/spec-quick` instead of `/spec` when:
- The task is small (1-3 files, <1 hour of work)
- The solution is obvious — no architectural decisions needed
- There's no need for formal requirements or design review
- You just want spec-engine's quality gates and wiring verification

Use `/spec` instead when:
- Multiple components need to interact
- There are architectural trade-offs to evaluate
- The feature needs formal acceptance criteria
- Multiple waves of tasks are expected

## Workflow

### Step 1: Validate and Initialize

1. Generate a spec name from the description: slugify the first 4-5 words (lowercase, hyphens). Example: `"fix login button alignment"` → `fix-login-button`
2. Check if `.claude/specs/<name>/` exists. If so, append a numeric suffix: `fix-login-button-2`
3. Create the spec directory: `.claude/specs/<name>/`
4. Create subdirectories: `evidence/tests/`, `handoffs/`

### Step 2: Auto-Detect Project Configuration

Detect the project type and configure quality gates automatically:

1. Check for project manifests in priority order:
   - `package.json` → Node.js project
   - `pyproject.toml` or `setup.py` → Python project
   - `Cargo.toml` → Rust project
   - `go.mod` → Go project
   - `Makefile` → Generic make-based project

2. For detected project type, generate init.sh with appropriate gates:

   **Node.js** (from package.json scripts):
   ```bash
   # Read package.json scripts to find lint/test commands
   lint_cmd="npm run lint"        # if "lint" script exists
   typecheck_cmd="npx tsc --noEmit"  # if tsconfig.json exists
   test_cmd="npm test"            # if "test" script exists
   ```

   **Python**:
   ```bash
   lint_cmd="ruff check ."        # or "flake8" if ruff not in deps
   typecheck_cmd="mypy ."         # if mypy in deps
   test_cmd="pytest"              # if pytest in deps
   ```

   **Rust**:
   ```bash
   lint_cmd="cargo clippy -- -D warnings"
   typecheck_cmd="cargo check"
   test_cmd="cargo test"
   ```

   **Go**:
   ```bash
   lint_cmd="golangci-lint run"
   typecheck_cmd="go vet ./..."
   test_cmd="go test ./..."
   ```

3. Write the detected init.sh to the spec directory
4. Show the user what was detected: `"Detected Node.js project. Gates: lint (npm run lint), typecheck (tsc), test (npm test)"`

### Step 3: Analyze Task Scope

Read relevant codebase context:

1. Use Grep/Glob to find files related to the description
2. Read the most relevant files (max 5) to understand current state
3. Determine what files need to be created or modified

### Step 4: Generate Minimal Tasks

Create `tasks.md` with 1-3 tasks directly (no planner agent needed):

```markdown
# Tasks: <name>

> Generated by spec-engine v2.0.0 (quick mode)

## Implementation

### T-1: <primary task title>

- **Status**: pending
- **Wave**: 0
- **Wired**: pending
- **Dependencies**: none
- **Covers**: quick-mode
- **Files**: <detected files>
- **Description**: <description derived from user input + codebase analysis>
- **Acceptance Criteria**:
  1. <happy path criterion>
  2. <error path criterion>
```

Add T-2, T-3 only if the task genuinely requires multiple steps (e.g., create model + create API route + wire into app). Most quick tasks should be 1 task.

### Step 5: Create Minimal state.json

Write state.json with `quick_mode: true`:

```json
{
  "version": 1,
  "spec_name": "<name>",
  "created_at": "<ISO-8601>",
  "quick_mode": true,
  "integrity": {
    "requirements_sha256": null,
    "design_sha256": null,
    "tasks_sha256": "<SHA256 of tasks.md>",
    "computed_at": "<ISO-8601>"
  },
  "tasks": {
    "T-1": {
      "status": "pending",
      "wave": 0,
      "wired": "pending",
      "dependencies": [],
      "covers": ["quick-mode"],
      "files": ["<file list>"],
      "description": "<description>",
      "failures": 0
    }
  },
  "waves": [{"wave": 0, "tasks": ["T-1"]}],
  "parallel": {
    "max_parallel_agents": 3,
    "shared_files": [],
    "generated_files": [],
    "post_merge_commands": []
  },
  "execution": {
    "current_wave": 0,
    "current_batch": [],
    "iteration": 0,
    "total_tokens": 0,
    "budget_cap": null,
    "started_at": null,
    "last_iteration_at": null,
    "human_checkpoint_interval": 5,
    "tasks_since_checkpoint": 0
  },
  "reproducibility": {
    "plugin_version": "2.0.0",
    "model_versions": {},
    "git_sha_start": "<current HEAD>",
    "prompt_hashes": [],
    "referenced_codebase_files": ["<detected files>"]
  },
  "quality_gates": {
    "gates": [],
    "lint_cmd": null,
    "typecheck_cmd": null,
    "test_cmd": null,
    "dev_cmd": null,
    "integration_cmd": null,
    "baseline_errors": null,
    "allowed_commands": [],
    "last_regression_pass": null
  },
  "lessons_applied": [],
  "audit_log": []
}
```

Parse init.sh and populate quality_gates in state.json.

### Step 6: Execute Immediately

Run the spec-exec workflow inline (same as `/spec-exec` but without drift detection or cross-spec dependency checks):

1. Dispatch spec-implementer agent for T-1
2. Auto-commit after agent completes
3. Run quality gates
4. If gates fail: dispatch spec-debugger (max 2 retries)
5. Verify wiring with grep
6. Update state.json

Repeat for T-2, T-3 if they exist.

### Step 7: Completion

Present summary:
```
== Quick Spec Complete: <name> ==

Tasks: 1/1 completed
Wired: 1 yes
Quality Gates: lint ✓, typecheck ✓, test ✓
Tokens: ~8,000

Files changed:
  - src/components/LoginButton.tsx (modified)
  - src/components/__tests__/LoginButton.test.tsx (created)
```

Do NOT suggest `/spec-accept` or `/spec-docs` for quick specs — they're overkill. Just suggest committing.
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-quick/SKILL.md
git commit -m "feat: add /spec-quick skill for lightweight task execution"
```

---

## Task 8: Add Consensus Planning to `/spec` Skill

**Files:**
- Modify: `skills/spec/SKILL.md`

- [ ] **Step 1: Add the --consensus flag to the Usage section**

In `skills/spec/SKILL.md`, after the `## Arguments` section (line 20), add:

```markdown
## Options

- `--consensus`: Enable consensus planning. After the planner writes the initial draft, an Architect and Critic review it before finalization. Adds ~2x tokens to the planning phase but catches more design issues.
```

- [ ] **Step 2: Add Step 5.5 for consensus deliberation**

After Step 5 (Requirements + Design Writing) and before Step 6 (MANDATORY HUMAN GATE), insert a new step:

```markdown
### Step 5.5: Consensus Deliberation (only if --consensus)

If `--consensus` flag was provided:

1. **Architect Review**: Dispatch spec-consultant agent with:
   - Role: "Software Architect"
   - Question: "Review this requirements.md and design.md. Evaluate: component boundaries, scalability, integration patterns, and technical debt risk. List specific concerns and improvement suggestions."
   - Context: The full requirements.md and design.md content

2. **Critic Review**: Dispatch spec-consultant agent (in parallel with Architect) with:
   - Role: "Critical Analyst"
   - Question: "Review this requirements.md and design.md as a devil's advocate. Find: missing edge cases, unstated assumptions, scope creep risks, and requirements that are untestable. Be specific — cite the exact requirement or design section."
   - Context: The full requirements.md and design.md content

3. **Revision**: After both consultants respond, dispatch spec-planner agent again with:
   - The original requirements.md and design.md
   - Architect feedback
   - Critic feedback
   - Instruction: "Revise requirements.md and design.md to address the feedback. Do NOT ask questions — make the best judgment call for each concern. Add an `## Architect Review Notes` and `## Critic Review Notes` appendix to design.md summarizing what was addressed."

The output is the same requirements.md + design.md — downstream contracts are unchanged. The human gate in Step 6 still applies.
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec/SKILL.md
git commit -m "feat: add --consensus flag for deliberation loop in /spec"
```

---

## Task 9: Add Codebase-Aware Template Detection to `/spec` Skill

**Files:**
- Modify: `skills/spec/SKILL.md`

- [ ] **Step 1: Add auto-detection logic to Step 9 (Parse init.sh)**

Replace Step 9 in `skills/spec/SKILL.md` with:

```markdown
### Step 9: Auto-Detect and Parse init.sh

1. **Auto-detect project type** (if init.sh has no gates configured):

   Check for project manifests and populate init.sh quality gates automatically:

   | Manifest | Project Type | Default Gates |
   |----------|-------------|---------------|
   | `package.json` | Node.js | lint: `npm run lint` (if script exists), typecheck: `npx tsc --noEmit` (if tsconfig.json exists), test: `npm test` (if script exists) |
   | `pyproject.toml` / `setup.py` | Python | lint: `ruff check .` or `flake8`, typecheck: `mypy .` (if in deps), test: `pytest` (if in deps) |
   | `Cargo.toml` | Rust | lint: `cargo clippy -- -D warnings`, typecheck: `cargo check`, test: `cargo test` |
   | `go.mod` | Go | lint: `golangci-lint run` (if installed), typecheck: `go vet ./...`, test: `go test ./...` |

   For Node.js projects, read `package.json` `scripts` object to verify which scripts actually exist before setting gates.

   Show the user what was detected:
   ```
   Detected Node.js project (from package.json).
   Auto-configured quality gates:
     lint: npm run lint
     typecheck: npx tsc --noEmit
     test: npm test

   Edit .claude/specs/<name>/init.sh to customize.
   ```

2. **Parse init.sh**: Read quality gate commands (supporting both `gates=()` array and legacy individual variables). Update state.json `quality_gates` section.

3. **Read budget_cap and human_checkpoint_interval** if defined.
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec/SKILL.md
git commit -m "feat: add codebase-aware template auto-detection to /spec"
```

---

## Task 10: Add Task Decomposition on Failure to `/spec-loop`

**Files:**
- Modify: `skills/spec-loop/SKILL.md`

- [ ] **Step 1: Replace the stuck detection in Step 2e.3**

Find the stuck detection section in Step 2e (Post-Wave Checks, item 3). Replace:

```markdown
3. **Stuck detection**: If any task has `failures >= 3`:
   - Log "AUTO-SKIP: T-X after 3 failures" to state.json audit log, mark task as "skipped", continue to next task.
```

With:

```markdown
3. **Stuck detection with decomposition**: If any task has `failures >= 3`:

   a. **Check if already decomposed**: If `state.json.tasks[T-X].decomposed` is true, this task was already split once. Skip it:
      - Mark task as `"skipped"` in state.json
      - Log: `"AUTO-SKIP: T-X after 3 failures (already decomposed once, no further splits)"`
      - Continue to next task

   b. **Attempt decomposition**: Dispatch spec-tasker agent with:
      - The failed task's description, acceptance criteria, and error history from audit_log
      - Instruction: "This task failed 3 times. Analyze the failure pattern and split it into 2-3 smaller, more focused tasks. Use new task IDs starting from T-{max_existing + 1}. Each sub-task must have non-overlapping Files. Mark the sub-tasks with `decomposed_from: T-X`."

   c. **Apply decomposition**:
      - Mark original task as `status: "decomposed"` in state.json
      - Set `decomposed: true` on the original task
      - Add new tasks to state.json with:
        - `wave`: original task's wave + 1
        - `dependencies`: same as original task's dependencies
        - `decomposed_from`: original task ID
      - Add new tasks to the appropriate wave in `state.json.waves`
      - If the wave doesn't exist yet, create it
      - Recompute integrity hash for tasks.md
      - Log: `"DECOMPOSED: T-X split into T-Y, T-Z after 3 failures"`

   d. **Decomposition limit**: Max 1 decomposition per original task. If a decomposed sub-task also fails 3 times, it gets skipped (step 3a).
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-loop/SKILL.md
git commit -m "feat: add task decomposition on failure to /spec-loop"
```

---

## Task 11: Add Task Decomposition on Failure to `/spec-team`

**Files:**
- Modify: `skills/spec-team/SKILL.md`

- [ ] **Step 1: Update the Escalation section**

Replace the `## Escalation` section in `skills/spec-team/SKILL.md` with:

```markdown
## Escalation

If Debugger fails twice on the same issue:
- Mark task as failed in state.json (increment failures count)
- If failures >= 3:

  a. **Check if already decomposed**: If `state.json.tasks[T-X].decomposed` is true, skip it:
     - Mark as `"skipped"`, log `"AUTO-SKIP: T-X after 3 failures (already decomposed)"`

  b. **Attempt decomposition**: Dispatch spec-tasker agent with:
     - Failed task description, acceptance criteria, error history
     - Instruction: "Split into 2-3 smaller tasks with new IDs starting from T-{max + 1}. Each sub-task must have non-overlapping Files. Set `decomposed_from: T-X`."

  c. **Apply**: Mark original as `status: "decomposed"`, `decomposed: true`. Add new tasks at wave + 1. Recompute integrity. Log decomposition.

  d. **Limit**: Max 1 decomposition per original task. Sub-task failures → skip.

- Otherwise: move to next task, come back later
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-team/SKILL.md
git commit -m "feat: add task decomposition on failure to /spec-team"
```

---

## Task 12: Add Live Progress Streaming to `/spec-loop`

**Files:**
- Modify: `skills/spec-loop/SKILL.md`

- [ ] **Step 1: Add progress emission instructions to the execution loop**

In `skills/spec-loop/SKILL.md`, add a new section after `## Autonomous Execution` and before `## Execution Loop`:

```markdown
## Live Progress Streaming

During execution, emit structured progress lines to keep the user informed of real-time status. These lines appear in the terminal output between agent dispatches.

**Format:** `[HH:MM:SS] ▸ EVENT │ details`

**Required emission points:**
- Before each wave: `[12:34:56] ▸ Wave 2/4 │ 3 pending tasks`
- Before each task dispatch: `[12:34:57] ▸ T-5 implementing │ auth-middleware.ts`
- After each task completes: `[12:35:12] ▸ T-5 completed │ 5/8 tasks done`
- After each quality gate: `[12:35:15] ▸ lint ✓ │ typecheck ✓ │ test ✓`
- After each wave: `[12:35:20] ▸ Wave 2/4 complete`
- On completion: `[12:40:00] ▸ COMPLETE │ 8/8 tasks │ ~64k tokens`

Also append each progress line to `.claude/specs/<name>/progress.log` for later review.

Emit these lines as plain text output between tool calls — they are displayed directly to the user.
```

- [ ] **Step 2: Add lifecycle hook calls to the wave loop**

In `skills/spec-loop/SKILL.md`, in Step 2a (Collect Pending Tasks), after the audit log append, add:

```markdown
4. **Run lifecycle hook**: If `hook_on_wave_start` is configured in init.sh, execute it with args: `<spec_name> <wave_number>`. Best-effort — log any errors but do not halt execution.
```

In Step 2d, item 12 (Update state.json), after marking completed tasks, add:

```markdown
13.5 **Run lifecycle hook**: For each completed task, if `hook_on_task_complete` is configured in init.sh, execute it with args: `<spec_name> <task_id> <status>`. Best-effort.
```

In Step 4 (Completion), after presenting the summary, add:

```markdown
4. **Run lifecycle hook**: If `hook_on_spec_complete` is configured in init.sh, execute it with args: `<spec_name> <final_status>`. This one runs synchronously (wait for completion) since it's the last action.
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec-loop/SKILL.md
git commit -m "feat: add live progress streaming and lifecycle hooks to /spec-loop"
```

---

## Task 13: Add Live Progress Streaming to `/spec-team`

**Files:**
- Modify: `skills/spec-team/SKILL.md`

- [ ] **Step 1: Add progress streaming section**

In `skills/spec-team/SKILL.md`, add after `## Handoff File Protocol` and before `## Team Workflow`:

```markdown
## Live Progress Streaming

During execution, emit structured progress lines for real-time visibility:

**Format:** `[HH:MM:SS] ▸ EVENT │ details`

**Required emission points:**
- Before each wave: `[12:34:56] ▸ Wave 2/4 │ 3 pending tasks`
- Before each phase: `[12:34:57] ▸ Phase 1: Implementing │ T-5, T-6 (parallel)`
- After each task: `[12:35:12] ▸ T-5 implemented │ 5/8 tasks done`
- After testing: `[12:35:30] ▸ T-5 tested ✓`
- After review: `[12:36:00] ▸ Wave 2 reviewed ✓`
- After each quality gate: `[12:35:15] ▸ lint ✓ │ typecheck ✓ │ test ✓`
- On completion: `[12:40:00] ▸ COMPLETE │ 8/8 tasks │ ~64k tokens`

Append each line to `.claude/specs/<name>/progress.log`.
```

- [ ] **Step 2: Add lifecycle hook calls**

In Phase 0 (Pre-Wave Setup), after item 4, add:

```markdown
5. **Run lifecycle hook**: Execute `hook_on_wave_start` with args: `<spec_name> <wave_number>`. Best-effort.
```

In Phase 5 (Commit), after item 12, add:

```markdown
12.5 **Run lifecycle hooks**: For each completed task in the wave, execute `hook_on_task_complete` with args: `<spec_name> <task_id> completed`. Best-effort.
```

In `## Completion`, after the summary, add:

```markdown
- **Run lifecycle hook**: Execute `hook_on_spec_complete` with args: `<spec_name> <final_status>`. Synchronous (wait for completion).
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec-team/SKILL.md
git commit -m "feat: add live progress streaming and lifecycle hooks to /spec-team"
```

---

## Task 14: Add Progress and Hooks to `/spec-exec`

**Files:**
- Modify: `skills/spec-exec/SKILL.md`

- [ ] **Step 1: Add progress emission points**

In `skills/spec-exec/SKILL.md`, add after `## Rationalization Prevention` and before `## Workflow`:

```markdown
## Progress Streaming

Emit structured progress lines during execution:

- Before task dispatch: `[HH:MM:SS] ▸ T-X implementing │ <files>`
- After task completes: `[HH:MM:SS] ▸ T-X completed │ N/M tasks done`
- After quality gates: `[HH:MM:SS] ▸ lint ✓ │ typecheck ✓ │ test ✓`
- On wiring check: `[HH:MM:SS] ▸ T-X wired ✓` or `[HH:MM:SS] ▸ T-X wired ✗ (downgraded)`

Append each line to `.claude/specs/<name>/progress.log`.
```

- [ ] **Step 2: Add lifecycle hook calls to Step 6 and Step 8**

In Step 6 (Update State), after item 7, add:

```markdown
8. **Run lifecycle hook**: For each completed task, execute `hook_on_task_complete` if configured. Best-effort.
```

In Step 8 (Completion Check), at the end after suggesting next steps, add:

```markdown
5. If all tasks complete, run `hook_on_spec_complete` synchronously.
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec-exec/SKILL.md
git commit -m "feat: add progress streaming and lifecycle hooks to /spec-exec"
```

---

## Task 15: Add Lessons-to-Validation-Rules to `/spec-validate`

**Files:**
- Modify: `skills/spec-validate/SKILL.md`

- [ ] **Step 1: Add a new Step 3.5 for lessons-derived rules**

In `skills/spec-validate/SKILL.md`, after Step 3 (Validation fingerprint check) and before Step 4 (Delegate to spec-validator), insert:

```markdown
### Step 3.5: Derive Validation Rules from Lessons

If `.claude/specs/lessons.json` exists:

1. Read lessons.json and extract entries with `category: "pattern"` or `category: "failure"`
2. For each relevant lesson, generate a WARNING-level validation rule:

   **Lesson → Rule mapping:**
   - Lesson about missing error handling → WARNING if any acceptance criterion lacks an error-path counterpart
   - Lesson about auth requirements → WARNING if design.md has API routes without auth mention
   - Lesson about file size limits → WARNING if any task's Files list has >5 files
   - Lesson about wiring failures → WARNING if tasks marked `Wired: n/a` exceed 30% of total

3. Include derived rules in the validator agent prompt:
   ```
   ## Lessons-Derived Rules (WARNING severity)
   These rules were automatically derived from lessons.json.
   Report them as WARNING, not ERROR.

   - WARN-L1: [rule description] (from lesson: "[lesson text]")
   - WARN-L2: [rule description] (from lesson: "[lesson text]")
   ```

4. If `--strict-lessons` flag is provided, promote lesson-derived rules to ERROR severity.

**Note:** Lesson-derived rules are pattern-matched text checks, not arbitrary code execution. Each rule checks for the presence or absence of specific patterns in spec file content.
```

- [ ] **Step 2: Add `--strict-lessons` to the Options section**

After `--no-fix` in the Options section, add:

```markdown
- `--strict-lessons`: Promote lessons-derived validation rules from WARNING to ERROR severity. Use when you want lesson patterns to block execution.
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec-validate/SKILL.md
git commit -m "feat: add lessons-to-validation-rules pipeline to /spec-validate"
```

---

## Task 16: Add Per-Wave Sequential/Parallel Escalation to `/spec-loop`

**Files:**
- Modify: `skills/spec-loop/SKILL.md`

- [ ] **Step 1: Update Step 2c (Build Parallel Groups) with per-wave escalation**

In `skills/spec-loop/SKILL.md`, at the end of Step 2c (Build Parallel Groups), add:

```markdown
#### Per-Wave Escalation Heuristic

Even when `--no-parallel` is NOT specified, automatically downgrade a wave to sequential if:

1. **Dependency overlap**: Any two tasks in the wave share a dependency target (e.g., both depend on T-1's output) AND either task modifies the dependency's files
2. **High failure history**: Any task in the wave has `failures >= 1` from a previous iteration (indicates complexity that benefits from sequential execution with full context)
3. **Shared import patterns**: Both tasks import from the same file that was created in a previous wave AND both tasks will add new exports/modifications to it

When downgrading, log: `"SEQUENTIAL ESCALATION: Wave N downgraded to sequential — [reason]"` in the audit log.

This check runs per-wave, not once globally. Wave 1 can be parallel while Wave 2 is sequential.
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-loop/SKILL.md
git commit -m "feat: add per-wave sequential/parallel escalation heuristic to /spec-loop"
```

---

## Task 17: Add Cross-Spec Dependency Visualization to `/spec-dashboard`

**Files:**
- Modify: `skills/spec-dashboard/SKILL.md`

- [ ] **Step 1: Add --deps flag to Usage section**

In `skills/spec-dashboard/SKILL.md`, update the Usage section:

```markdown
## Usage

```
/spec-dashboard [--deep] [--deps]
```

- **Default**: Fast file-based verification of all specs
- **`--deep`**: Additionally runs spec-validator per spec for semantic validation
- **`--deps`**: Show cross-spec dependency graph
```

- [ ] **Step 2: Add Step 5.5 for dependency visualization**

After Step 5 (--deep mode) and before Step 6 (Suggest next actions), add:

```markdown
### Step 5.5: Dependency Graph (only if --deps)

If `--deps` is specified:

1. For each spec, read its `requirements.md` and parse the `## Depends On` section for dependency names
2. Build a dependency map: `{ spec_name: [dependency_names] }`
3. Render an ASCII dependency graph:

```
🔗 Dependency Graph

auth-system (10/10 ✅)
├── payment-flow (6/12 🔄) ── depends on: auth-system
│   └── notification-svc (0/0 📋) ── depends on: payment-flow
└── user-dashboard (0/5 📋) ── depends on: auth-system

search-feature (0/0 📋) ── no dependencies

Legend: ✅ complete  🔄 in progress  📋 not started  🚫 blocked
```

4. Highlight blocked specs: specs whose dependencies are not complete should show `🚫 BLOCKED` with the incomplete dependency name
5. Detect and warn about circular dependencies using DFS (same algorithm as `lib/deps.sh`)
```

- [ ] **Step 3: Commit**

```bash
git add skills/spec-dashboard/SKILL.md
git commit -m "feat: add --deps flag for cross-spec dependency visualization"
```

---

## Task 18: Add Diff-Based Output to `/spec-refine`

**Files:**
- Modify: `skills/spec-refine/SKILL.md`

- [ ] **Step 1: Add a new Step 4.5 for diff display**

In `skills/spec-refine/SKILL.md`, after Step 4 (Update Integrity Manifest) and before Step 5 (Add Change Log Entry), insert:

```markdown
### Step 4.5: Show Spec Diff

After changes are applied and before the change log:

1. Run `git diff -- .claude/specs/<name>/requirements.md .claude/specs/<name>/design.md .claude/specs/<name>/tasks.md` to capture what changed
2. Present the diff to the user in a code block:

```
## Spec Changes

\`\`\`diff
--- a/.claude/specs/auth-system/requirements.md
+++ b/.claude/specs/auth-system/requirements.md
@@ -45,6 +45,12 @@
 ### US-3: User profile editing
+
+#### Acceptance Criteria (EARS Notation)
+
+1. WHEN user submits profile update with valid phone number
+   THE SYSTEM SHALL save the phone number and send verification SMS
\`\`\`

This makes it easy to see exactly what the refine operation changed, especially when multiple requirements and design components are affected.

**Note:** If git is not available or the spec files aren't tracked, skip this step silently.
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-refine/SKILL.md
git commit -m "feat: add diff-based output to /spec-refine"
```

---

## Task 19: Create `/spec-session` Skill

**Files:**
- Create: `skills/spec-session/SKILL.md`

- [ ] **Step 1: Write the spec-session skill**

```markdown
---
name: spec-session
description: Interactive guided session for step-by-step spec execution
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# /spec-session Command

Interactive guided mode for step-by-step spec execution. Shows current state and asks what to do next.

## Usage

```
/spec-session [spec-name]
```

## Workflow

### Step 1: Load and Display State

1. Locate spec directory, validate spec name (auto-detect if only one spec)
2. Read state.json
3. Present a concise status summary:

```
== Session: auth-system ==

Progress: 7/15 tasks (47%) │ Wave 2 of 4
Current wave: T-5 (pending), T-6 (pending), T-7 (completed)
Quality gates: lint ✓, typecheck ✓, test ✓
Wiring: 6 verified, 1 pending
Last activity: 2h ago (T-7 completed)
```

### Step 2: Present Options

Use AskUserQuestion with the most relevant options based on current state:

**If tasks are pending in current wave:**
- **Execute next wave** — Run `/spec-exec` for the current wave
- **Execute all remaining** — Run `/spec-loop` to completion
- **Skip a task** — Mark a specific task as skipped
- **View task details** — Show full description and AC for a task
- **Validate spec** — Run `/spec-validate`
- **Refine spec** — Run `/spec-refine`
- **Exit session** — Return to normal mode

**If all tasks are complete:**
- **Run acceptance testing** — Run `/spec-accept`
- **Generate docs** — Run `/spec-docs`
- **Create PR** — Suggest `gh pr create` command
- **Run retrospective** — Run `/spec-retro`
- **Exit session** — Return to normal mode

**If no tasks exist yet:**
- **Start execution** — Run `/spec-exec`
- **Validate first** — Run `/spec-validate`
- **Refine requirements** — Run `/spec-refine`
- **Exit session** — Return to normal mode

### Step 3: Execute Choice

Based on user selection:
- For execution actions: tell the user to run the corresponding command (e.g., "Run `/spec-exec auth-system` to execute the next wave")
- For view actions: read and display the requested information inline
- For skip actions: update state.json directly (mark task as skipped, log in audit_log)

### Step 4: Loop

After each action completes, go back to Step 1 (reload state and present updated options). Continue until the user selects "Exit session".

## Design Principles

- **Read-only on state** except for skip actions — all real mutations happen through existing skills
- **No autonomous execution** — every action requires user choice
- **Minimal context** — show just enough state to make a decision, not the full spec
- **Escape hatch** — user can exit at any time
```

- [ ] **Step 2: Commit**

```bash
git add skills/spec-session/SKILL.md
git commit -m "feat: add /spec-session skill for interactive guided execution"
```

---

## Task 20: Bump Plugin Version and Update plugin.json

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Update version and keywords**

Replace the contents of `.claude-plugin/plugin.json` with:

```json
{
  "name": "spec-engine",
  "version": "2.0.0",
  "description": "Spec-driven development engine: structured requirements (EARS), architecture design, wave-based parallel task execution, quality gates, and full SDLC lifecycle. Includes quick mode, lifecycle hooks, consensus planning, and live progress streaming.",
  "author": {
    "name": "farshidghyasi"
  },
  "keywords": ["specs", "requirements", "design", "planning", "workflow", "EARS", "execution", "quality-gates", "wave-batching", "parallel-agents", "model-routing", "lifecycle-hooks", "quick-mode", "consensus-planning"]
}
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 2.0.0"
```

---

## Summary: Task → Improvement Mapping

| Task | Improvement # | Description |
|------|--------------|-------------|
| 1 | #2 | Custom quality gates reader (lib/gates.sh) |
| 2 | #3 | Lifecycle hooks runner (lib/hooks.sh) |
| 3 | #4 | Progress event emitter (lib/progress.sh) |
| 4 | #2, #3 | Updated init.sh template |
| 5 | #2 | Updated state.json template |
| 6 | #13 | Notification hook templates |
| 7 | #1, #8 | /spec-quick skill (includes auto-detection) |
| 8 | #6 | Consensus planning in /spec |
| 9 | #8 | Codebase-aware templates in /spec |
| 10 | #5 | Task decomposition in /spec-loop |
| 11 | #5 | Task decomposition in /spec-team |
| 12 | #4, #3 | Progress streaming + hooks in /spec-loop |
| 13 | #4, #3 | Progress streaming + hooks in /spec-team |
| 14 | #4, #3 | Progress streaming + hooks in /spec-exec |
| 15 | #7 | Lessons-to-rules in /spec-validate |
| 16 | #9 | Per-wave escalation in /spec-loop |
| 17 | #10 | Dependency graph in /spec-dashboard |
| 18 | #12 | Diff-based output in /spec-refine |
| 19 | #11 | /spec-session skill |
| 20 | — | Version bump |
