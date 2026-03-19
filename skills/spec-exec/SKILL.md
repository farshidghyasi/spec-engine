---
name: spec-exec
description: Execute one spec task iteration with quality gates
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-exec Command

Execute a single iteration of spec-driven implementation with quality gates, structural completion detection, and tiered failure recovery.

## Usage

```
/spec-exec [spec-name]
```

## Workflow

### Step 1: Load State

1. Locate spec directory, validate spec name
2. Read `state.json`
3. **Verify integrity manifest**: Compute SHA256 of requirements.md, design.md, tasks.md. Compare against `state.json.integrity`. If mismatch:
   - Show which files changed
   - Ask user: "Accept changes and update manifest" / "Cancel execution"

### Step 2: Check Preconditions

1. **Cross-spec dependencies**: If requirements.md has `## Depends On`, verify those specs are complete
2. **Budget cap**: If `state.json.execution.budget_cap` is set and `total_tokens` exceeds it, refuse to execute
3. **Stuck detection**: If any pending task has `failures >= 3`, pause and present the failure history to the user

### Step 3: Select Task Batch

1. Read `state.json.waves` to find the current wave
2. Collect pending tasks in the current wave
3. Batch up to 2-3 tasks if they are independent (no shared file conflicts)
4. Update `state.json.execution.current_batch` with the selected task IDs

### Step 4: Implementation

Spawn the **spec-implementer** agent via Agent tool with:

- **Layer 0**: state.json summary (~200 tokens) — current wave, batch, completed tasks, last issue
- **Layer 1**: The batch task descriptions extracted from tasks.md (~500 tokens)
- **Layer 2** (first iteration or after errors): Full requirements.md and design.md
- **Context from lessons.json**: If relevant lessons exist, include top 3

Tell the implementer:
- Complete all tasks in the batch
- Write persistent test files
- Follow the project's coding conventions
- Wire everything into the application
- Report files changed and test file locations

### Step 5: Quality Gates

After the implementer completes, run quality gates sequentially:

1. **Lint** (if configured): Run `state.json.quality_gates.lint_cmd` via Bash
2. **Type Check** (if configured): Run `state.json.quality_gates.typecheck_cmd` via Bash
3. **Regression Test** (if configured): Run `state.json.quality_gates.test_cmd` via Bash
4. **Secret Scan**: Check staged files for sensitive patterns (.env, *.pem, *.key, credentials)

If any gate fails:
- Spawn **spec-debugger** agent to fix the issue (max 2 retries per task)
- Re-run the failing gate after each fix
- If 2 retries exhausted: **Task Rollback** — `git checkout` the changed files, increment `tasks[id].failures` in state.json

### Step 6: Update State

After successful quality gates:

1. Update each completed task in `state.json.tasks`: status = "completed", record tokens_used
2. Increment `state.json.execution.iteration`
3. Update `state.json.execution.total_tokens`
4. Update `state.json.execution.last_iteration_at`
5. Increment `state.json.execution.tasks_since_checkpoint`
6. Append audit log entry: task_completed event with git SHA, tokens, quality gate results
7. Record model version in `state.json.reproducibility.model_versions` if not already present

### Step 7: Commit

1. Stage changed files (excluding secrets detected in Step 5)
2. Commit with descriptive message referencing task IDs

### Step 8: Completion Check

1. **Structural detection**: Read state.json.tasks. If ALL tasks have status "completed", report completion.
2. If current wave is complete, advance `state.json.execution.current_wave`
3. Report status: "Completed T-X, T-Y. Wave 1: 4/4 done. Advancing to Wave 2. 7/15 tasks total."

## Dry-Run Mode

If the user says "dry run" or "--dry-run":

1. Parse the task DAG from state.json
2. Show the execution plan: waves, batches, estimated tokens, estimated cost
3. Do NOT execute anything
