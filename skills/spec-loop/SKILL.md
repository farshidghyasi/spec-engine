---
name: spec-loop
description: Loop spec execution with wave-based batching until all tasks complete
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-loop Command

Wave-based execution loop. Batches independent tasks, runs quality gates, enforces cost controls, and pauses for human checkpoints.

## Usage

```
/spec-loop [spec-name] [--dry-run] [--max-iterations N]
```

## Dry-Run Mode

If `--dry-run` is specified:

1. Read state.json and tasks.md
2. Parse the wave structure
3. Estimate tokens per wave (task count * ~8000 tokens average per task)
4. Estimate cost (Sonnet pricing for implementation, Opus for review if team mode)
5. Present execution plan:

```
== Execution Plan (Dry Run) ==

Wave 0: T-1 (setup)                    ~8k tokens
Wave 1: T-2, T-3, T-4 (core)          ~24k tokens (batch: 2+1)
Wave 2: T-5, T-6 (integration)        ~16k tokens
Wave 3: T-7 (e2e testing)             ~8k tokens
Wave 4: T-8 (polish)                  ~8k tokens

Estimated total: ~64k tokens
Estimated cost: ~$0.32 (Sonnet)
Iterations: ~4 (wave-based batching)
Budget cap: 500,000 tokens
Human checkpoint: every 5 tasks

Proceed? [Yes / Adjust budget / Cancel]
```

Do NOT execute anything in dry-run mode.

## Execution Loop

### Step 1: Initialize

1. Locate spec directory, validate spec name
2. Read state.json
3. **Verify integrity manifest** — if spec files changed since last validation, prompt user
4. **Check budget** — if `total_tokens >= budget_cap`, refuse to start
5. **Check cross-spec dependencies** — verify dependent specs are complete
6. Record starting git SHA in `state.json.reproducibility.git_sha_start` (if not already set)
7. If quality gate commands are not yet in state.json, try to detect them:
   - Check package.json, pyproject.toml, Makefile, Cargo.toml, go.mod
   - Update state.json.quality_gates

### Step 2: Wave Loop

For each wave (starting from `state.json.execution.current_wave`):

#### 2a: Collect Pending Tasks
Read state.json.waves[current_wave].tasks. Filter to tasks with status "pending".

#### 2b: Batch Tasks
Group pending tasks in the current wave into batches of 2-3. If only 1 task remains, batch size is 1.

#### 2c: Execute Batch
For each batch:

1. Update state.json: set `execution.current_batch` to the batch task IDs
2. **Spawn spec-implementer agent** via Agent tool with:
   - state.json summary (Layer 0: ~200 tokens)
   - Batch task descriptions from tasks.md (Layer 1: ~500 tokens)
   - Full spec context only on first iteration or after errors (Layer 2)
   - Relevant lessons from lessons.json
3. After implementation, **run quality gates** via Bash:
   - Lint → Type Check → Regression Test → Secret Scan
   - On failure: spawn spec-debugger (max 2 retries)
   - On persistent failure: task rollback, increment failures in state.json
4. **Update state.json**: mark completed tasks, record tokens, append audit log
5. **Commit** with descriptive message

#### 2d: Post-Batch Checks

1. **Stuck detection**: If any task has `failures >= 3`:
   - Pause execution
   - Present failure history to user via AskUserQuestion
   - Options: "Skip this task" / "Retry with different approach" / "Abort"

2. **Human checkpoint**: If `tasks_since_checkpoint >= human_checkpoint_interval`:
   - Present progress summary
   - Ask user via AskUserQuestion: "Continue?" / "Pause" / "Abort"
   - Reset `tasks_since_checkpoint` to 0

3. **Budget check**: If `total_tokens >= budget_cap`:
   - Pause execution
   - Show cost summary
   - Ask user: "Increase budget" / "Abort"

4. **Completion check**: Read state.json.tasks. If ALL tasks completed, break out of loop.

5. **Wave advancement**: If all tasks in current wave are completed, increment `current_wave`.

### Step 3: Max Iterations

If `--max-iterations` was specified and iterations exceed it, stop.
Default max iterations: 50.

### Step 4: Completion

When all tasks are complete:

1. Update state.json: set all wave statuses to "completed"
2. Append final audit log entry
3. Present summary:

```
== Spec Complete: [feature-name] ==

Tasks: 15/15 completed
Iterations: 6
Total tokens: 127,430
Cost: ~$0.64
Duration: [start time] to [end time]

Quality Gate Results:
  Lint passes: 6/6
  Type check passes: 6/6
  Regression passes: 6/6
  Secrets blocked: 0

Next steps:
  /spec-accept  — Run user acceptance testing
  /spec-docs    — Generate documentation
  gh pr create --head spec/<name> --title "<name>"
```

## Interrupt/Resume

If the session is interrupted (user exits, timeout, etc.):
- state.json preserves: current_wave, current_batch, all task statuses, token counts
- Next `/spec-loop` invocation reads state.json and resumes from where it left off
- No re-orientation needed — state.json has all context

## Error Recovery Tiers

1. **Retry**: Debugger fixes, re-run gates (2 attempts)
2. **Task Rollback**: git checkout changed files, mark task failed
3. **Wave Rollback**: git reset to pre-wave state (if 3+ tasks in wave fail)
4. **Human Escalation**: Pause, present details, await user decision
