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

Wave-based execution loop. Batches independent tasks, runs them in parallel where safe, runs quality gates, enforces cost controls, and pauses for human checkpoints.

## Usage

```
/spec-loop [spec-name] [--dry-run] [--max-iterations N] [--no-parallel]
```

## Dry-Run Mode

If `--dry-run` is specified:

1. Read state.json and tasks.md
2. Parse the wave structure
3. Identify parallel groups (tasks with non-overlapping Files)
4. Estimate tokens per wave (task count * ~8000 tokens average per task)
5. Estimate cost (Sonnet pricing for implementation, Opus for review if team mode)
6. Present execution plan:

```
== Execution Plan (Dry Run) ==

Wave 0: T-1 (setup)                          ~8k tokens  [sequential]
Wave 1: T-2, T-3 (core)                      ~16k tokens [PARALLEL — no file overlap]
        T-4 (core, shares files with T-3)     ~8k tokens  [after T-2, T-3]
Wave 2: T-5, T-6 (integration)               ~16k tokens [PARALLEL — no file overlap]
Wave 3: T-7 (e2e testing)                     ~8k tokens  [sequential]
Wave 4: T-8 (polish)                          ~8k tokens  [sequential]

Parallel speedup: ~1.5x (3 parallel groups)
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

#### 2b: Pre-Parallel Setup

Before spawning parallel agents:

1. **Collect dependency additions**: If multiple tasks in the wave need new packages, install ALL dependencies first on the main branch (read task descriptions for `npm install`, `pip install`, etc.). This prevents lockfile conflicts.
2. **Validate no shared file overlap**: Check each task's Files against `state.json.parallel.shared_files`. If any task lists a shared file, move it to a sequential sub-batch.
3. **Validate import dependencies**: For each pair of tasks in the wave, check if task B's Files reference imports from task A's Files. If so, they CANNOT be parallel — sequentialize them.

#### 2c: Build Parallel Groups

Partition pending tasks into parallel groups based on file ownership:

1. Read the `files` field from each pending task in state.json (or parse from tasks.md)
2. Exclude tasks that touch shared files (from step 2b) — these run sequentially after all parallel groups
3. Build a file-conflict graph: two tasks conflict if they share any file in their Files lists
4. Tasks with NO file conflicts with each other form a **parallel group**
5. Cap parallel group size at `state.json.parallel.max_parallel_agents` (default: 3)
6. Tasks that conflict are placed in separate sequential sub-batches

**Example**: Wave 1 has T-2 (files: `src/auth.ts`), T-3 (files: `src/users.ts`), T-4 (files: `src/auth.ts, src/middleware.ts`)
- Parallel group 1: T-2, T-3 (no overlap)
- Sequential after group 1: T-4 (conflicts with T-2 on `src/auth.ts`)

If `--no-parallel` is specified, skip this step and process all tasks sequentially.

#### 2d: Execute Parallel Group

For each parallel group:

1. Update state.json: set `execution.current_batch` to the group's task IDs

2. **If group has 1 task** — spawn a single spec-implementer agent (no isolation needed)

3. **If group has 2+ tasks** — spawn parallel spec-implementer agents:
   - Launch each agent via the Agent tool with `isolation: "worktree"`
   - Each agent receives:
     - state.json summary (Layer 0: ~200 tokens)
     - ONLY its assigned task description from tasks.md (Layer 1)
     - Its assigned file boundaries: "You MUST only create/modify these files: [list]. Do NOT modify any other files. Do NOT refactor existing function signatures. Do NOT run formatters. Note any cross-boundary needs in your handoff file."
     - Full spec context on first iteration or after errors (Layer 2)
     - Relevant lessons from lessons.json
   - **All parallel agents are launched in a single message** (multiple Agent tool calls)
   - Wait for all agents to complete

4. **Atomic merge with fallback**: Record pre-merge HEAD SHA. Merge each worktree's changes back in task-ID order:
   - Exclude files in `state.json.parallel.generated_files` from merge
   - If ANY merge fails: reset to pre-merge SHA, fall back to sequential execution for the entire group
   - Shared file changes (noted in handoff files) are applied in a reconciliation step after all agent merges

5. **Post-merge regeneration**: Run commands from `state.json.parallel.post_merge_commands`:
   - Lock file regeneration (`npm install` / `pnpm install`)
   - Codegen (`npx prisma generate`, etc.)
   - Cache clean (`rm -rf .next dist node_modules/.cache`)
   - Do NOT run formatters yet

6. **Run quality gates** via Bash:
   - Lint (includes formatting) -> Type Check -> Regression Test -> Secret Scan
   - On failure: spawn spec-debugger (max 2 retries)
   - On persistent failure: task rollback, increment failures in state.json

7. **Update state.json**: mark completed tasks, record tokens, append audit log

7. **Commit** with descriptive message listing all task IDs in the batch

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

4. **Completion check**: Read state.json.tasks. If ALL tasks have status "completed" AND wired is "yes" or "n/a", break out of loop. Tasks with wired="pending" are NOT done.

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
Wired: 13 yes, 2 n/a
Iterations: 6 (3 parallel, 3 sequential)
Parallel groups: 4 (saved ~3 iterations)
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
