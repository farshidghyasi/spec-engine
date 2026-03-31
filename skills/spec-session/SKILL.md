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
