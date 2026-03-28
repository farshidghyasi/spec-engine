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
---

# /spec-loop Command

Wave-based execution loop. Batches independent tasks, runs them in parallel where safe, runs quality gates, enforces cost controls, and auto-handles all decisions.

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

```

Do NOT execute anything in dry-run mode. Present the plan and stop.

## Autonomous Execution

**⚠️ spec-loop NEVER asks the user questions. NEVER call AskUserQuestion. All decisions are made autonomously.**

The loop runs fully autonomously with NO human pauses:

- **No questions**: NEVER call AskUserQuestion. Not once. Not for any reason. Make the best decision yourself and log it.
- **Stuck detection**: Automatically skip the task after 3 failures and continue. Log the skip in state.json audit log.
- **No human checkpoints**: Do NOT pause for progress checks. Execute continuously.
- **Budget cap**: Log a warning when exceeded but continue. The ONLY thing that stops execution is `--max-iterations` or all tasks completing.
- **Integrity mismatch**: Log a warning but proceed without prompting.
- **Error escalation**: Do NOT escalate to user. Auto-skip or auto-fix. Log the decision.
- **Merge conflicts**: Resolve automatically or fall back to sequential. Do NOT ask for help.
- **Ambiguous decisions**: Pick the most reasonable option, log your reasoning in the audit log, continue.

**Self-test**: Before every tool call, check: "Am I about to call AskUserQuestion?" If yes, STOP — replace it with an autonomous decision + audit log entry.

## Rationalization Prevention

Every step below is mandatory. You WILL be tempted to skip steps that seem unnecessary for "simple" waves. This table exists because every rationalization below has caused real production failures.

| You will think... | Reality |
|---|---|
| "Only 2 tasks in this wave, no import manifest needed" | 2 parallel tasks caused 5 field-name mismatches in a real project. Even 2 tasks can disagree on naming. |
| "These tasks don't share imports, skip cross-agent resolution" | You cannot know this without scanning. Agents import from previous waves, not just each other. |
| "The agent probably committed its work" | Agents routinely do not commit. Every wave in a real run required manual commits. Always auto-commit. |
| "This agent wouldn't modify shared files" | Agents modify app.ts, index.ts, and router files constantly. Always check, always revert. |
| "Quality gates passed, so the wave works" | 39/39 tasks passed quality gates. 3 critical bugs made the auth flow non-functional. Gates test code correctness, not integration. |
| "The agent said wired: yes, trust it" | 12 routes were marked wired: yes but weren't mounted in app.ts. Always verify with grep. |
| "Post-merge commands failed but it's probably fine" | A failed `pnpm install` means missing deps. A failed build means broken types. Never continue past a failed post-merge command. |
| "Pre-existing test failures, just ignore gate output" | Without baseline comparison, you cannot distinguish new failures from old ones. Always use diff mode. |
| "Integration test isn't configured, skip it" | Log a warning that no integration_cmd is set. Do not silently skip — the user needs to know this safety net is missing. |
| "This wave is sequential, skip the post-agent checks" | Shared file enforcement and wired verification apply to ALL execution modes, not just parallel. |
| "The audit log can wait, I'll write it at the end" | A real run produced 41 completed tasks with an empty audit log. Write entries as you go, not at the end. |
| "The agent said the file exists, I trust it" | 34 files were marked completed without existing on disk. Always stat. Never trust self-reports. |
| "Evidence isn't needed, gates passed" | Without evidence files, spec-accept has nothing to verify. Always persist gate output. |
| "The file is big but it works" | 1700-line screen files deviated completely from the design. Always check file size, auto-create extraction tasks. |
| "I should ask the user about this edge case" | You NEVER ask. Make the best call, log it, move on. The user is not here to answer. |
| "This error is unusual, better check with the user" | Auto-fix or auto-skip. Log everything. The user will review the audit log later. |

**The cost of running every check is minutes. The cost of skipping one is hours of manual debugging.**

## Execution Loop

### Step 1: Initialize

1. Locate spec directory, validate spec name
2. Read state.json
3. **Verify integrity manifest** — if spec files changed since last validation, log a warning and proceed
4. **Check budget** — if `total_tokens >= budget_cap`, log a warning and continue
5. **Check cross-spec dependencies** — verify dependent specs are complete
6. Record starting git SHA in `state.json.reproducibility.git_sha_start` (if not already set)
7. **Drift detection**: If `referenced_codebase_files` exists in state.json, run `git diff --name-only <git_sha_start>..HEAD -- <referenced_files>`. If any changed: auto-fix spec files by dispatching spec-validator + spec-debugger (codebase is source of truth — fix specs, never code), recompute integrity, update `git_sha_start`, log to audit log.
8. If quality gate commands are not yet in state.json, try to detect them:
   - Check package.json, pyproject.toml, Makefile, Cargo.toml, go.mod
   - Update state.json.quality_gates

### Step 2: Wave Loop

**AUTONOMY REMINDER: You must NEVER call AskUserQuestion during any part of this loop. At every decision point, make the best autonomous choice and log it.**

For each wave (starting from `state.json.execution.current_wave`):

#### 2a: Collect Pending Tasks
1. Record the current git SHA as `pre_wave_sha` (for wave rollback if needed)
2. **Append audit log entry**: `{ "event": "wave_started", "wave": N, "timestamp": "<ISO-8601>", "details": "Starting wave N with X pending tasks" }`
3. Read state.json.waves[current_wave].tasks. Filter to tasks with status "pending".

#### 2b: Pre-Parallel Setup

Before spawning parallel agents:

1. **Collect dependency additions**: If multiple tasks in the wave need new packages, install ALL dependencies first on the main branch (read task descriptions for `npm install`, `pip install`, etc.). This prevents lockfile conflicts.
2. **Validate no shared file overlap**: Check each task's Files against `state.json.parallel.shared_files`. If any task lists a shared file, move it to a sequential sub-batch.
3. **Validate import dependencies**: For each pair of tasks in the wave, check if task B's Files reference imports from task A's Files. If so, they CANNOT be parallel — sequentialize them.
4. **Generate import manifest**: Scan all files created/modified by completed tasks in previous waves. For each file, extract its exports (functions, classes, types, constants). Build a manifest like:

```
== Import Manifest (from completed waves) ==

apps/api/src/middleware/admin-jwt.middleware.ts
  → export function adminJwt(req, res, next)
  → export const requireAdminJwt = adminJwt
  → export type AdminPermission = 'read' | 'write' | 'admin'
  → export type AdminRole = 'super_admin' | 'admin'

packages/shared-types/src/admin.ts
  → export interface AdminUser { id: string; email: string; role: AdminRole }
  → export type CreateAdminInput = Omit<AdminUser, 'id'>
```

Use Grep/Read to extract export statements from completed task files. Include this manifest in every parallel agent's prompt for the current wave. This prevents agents from guessing import names.

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
     - **Import manifest from completed waves** (Layer 1.5): exact export names, function signatures, and file paths from all code completed in previous waves. "Use EXACTLY these imports — do not guess or assume names."
     - Full spec context on first iteration or after errors (Layer 2)
     - Relevant lessons from lessons.json
   - **All parallel agents are launched in a single message** (multiple Agent tool calls)
   - Wait for all agents to complete

<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>

4. **Post-agent verification** (for each worktree, before merge):

   a. **Auto-commit worktree**: The agent may not commit its work. After each agent completes:
      ```bash
      cd <worktree_path>
      git add <files from task's Files field>
      git commit -m "feat: T-{id} — {task subject}"
      ```
      Only add files listed in the task's Files array — do not `git add -A`.

      **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:

      - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
      - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
      - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.

   b. **Shared file enforcement**: Check if the agent modified any shared files:
      ```bash
      cd <worktree_path>
      git diff --name-only HEAD~1 | grep -f <shared_files_list>
      ```
      If any shared file was modified, revert those changes:
      ```bash
      git checkout HEAD~1 -- <shared_file>
      git commit --amend --no-edit
      ```
      Log a warning: "Agent for T-X modified shared file <name>, reverted."

   c. **Cross-agent import resolution**: After ALL agents in the group complete but before merging, scan each agent's output for imports from other agents' files. For every `import { X } from './Y'` in agent A's code, verify that agent B's code (which owns file Y) actually exports X. If mismatches are found:
      - Log all mismatches
      - Re-dispatch the mismatched agents sequentially (not in parallel) with the correct export names from the import manifest
      - If only 1-2 mismatches: fix them directly via Edit instead of re-dispatching

5. **Atomic merge with fallback**: Record pre-merge HEAD SHA. Merge each worktree's changes back in task-ID order:
   - Exclude files in `state.json.parallel.generated_files` from merge
   - If ANY merge fails: reset to pre-merge SHA, fall back to sequential execution for the entire group
   - Shared file changes (noted in handoff files) are applied in a reconciliation step after all agent merges

6. **Post-merge regeneration**: Run commands from `state.json.parallel.post_merge_commands`:
   - Lock file regeneration (`npm install` / `pnpm install`)
   - Codegen (`npx prisma generate`, etc.)
   - Cache clean (`rm -rf .next dist node_modules/.cache`)
   - Do NOT run formatters yet
   - **CRITICAL**: If any post-merge command fails, treat it as a blocking error. Halt the wave, report the error. In yolo mode, attempt an auto-fix (e.g., add missing dependency, fix tsconfig exclude) and retry once. If still failing, mark the wave as failed and skip.

7. **Run quality gates in diff mode** via Bash:
   - Capture the list of files changed in this batch: `git diff --name-only <pre-merge-SHA> HEAD`
   - **Lint**: Run linter only on changed files if the linter supports file arguments. Otherwise run full lint but compare error count against `state.json.quality_gates.baseline_errors` — fail only if count increases.
   - **Type Check**: Run full typecheck (incremental if supported). If pre-existing errors exist, compare against baseline — fail only on NEW errors in changed files.
   - **Regression Test**: Run the full test suite. Pre-existing failures should be baselined.
   - **Secret Scan**: Only scan changed files.
   - On failure: spawn spec-debugger (max 2 retries)
   - On persistent failure: task rollback, increment failures in state.json

8. **MANDATORY: File existence verification** (for each completed task in the batch):

   ```bash
   # For every file in the task's Files array:
   for file in <task.files>; do
     if [ ! -f "$file" ]; then
       echo "MISSING: $file declared by T-$ID"
       # Mark task as FAILED, not completed
     fi
   done
   ```

   - If ANY declared file is missing, set the task status to `"failed"` in state.json, increment its failure count, and log: `"T-X failed: missing declared file(s): [list]"`
   - Do NOT mark a task as completed based on the agent's self-report. Verify on disk.
   - This check is non-negotiable. An agent saying "done" is not evidence that files exist.

9. **MANDATORY: Max file size check** (for each file modified by tasks in the batch):

   ```bash
   for file in <batch_modified_files>; do
     lines=$(wc -l < "$file")
     if [ "$lines" -gt 500 ]; then
       echo "OVERSIZED: $file has $lines lines (limit: 500)"
     fi
   done
   ```

   - If any file exceeds 500 lines, log a warning in the audit log: `"WARNING: T-X produced oversized file <path> ($lines lines). Extraction task recommended."`
   - Add a new pending task in the next wave: `"Extract sub-components from <path>"` with the oversized file in its Files array.
   - Do NOT fail the task for this — it's a warning that auto-generates a follow-up extraction task.

10. **MANDATORY: Audit log append** — After EVERY task completion, failure, or skip, append to `state.json.audit_log`:

   ```json
   {
     "timestamp": "<ISO-8601>",
     "event": "task_completed|task_failed|task_skipped|wave_started|wave_completed|gate_passed|gate_failed",
     "task_id": "T-X",
     "wave": N,
     "details": "<what happened>"
   }
   ```

   - This is not optional. An empty audit log is a bug.
   - Append an entry for: task start, task completion, task failure, task skip, wave start, wave completion, quality gate pass, quality gate fail, budget warning, human checkpoint, wired downgrade, file size warning.
   - Use `Edit` tool to append to the audit_log array in state.json after each event.

11. **MANDATORY: Evidence persistence** — After quality gates run, persist their output:

   ```bash
   mkdir -p <spec_dir>/evidence/tests
   # After each gate, capture output:
   <lint_cmd> > <spec_dir>/evidence/tests/wave-${WAVE}-lint.txt 2>&1 || true
   <typecheck_cmd> > <spec_dir>/evidence/tests/wave-${WAVE}-typecheck.txt 2>&1 || true
   <test_cmd> > <spec_dir>/evidence/tests/wave-${WAVE}-tests.txt 2>&1 || true
   ```

   - Gate output MUST be written to evidence/tests/ — do not discard it.
   - If gates were already run and output was not captured, re-run them with output redirection.
   - The spec-acceptor needs this evidence. Without it, acceptance testing is blind.

12. **Update state.json**: mark completed tasks (only those that passed file existence check), record tokens

13. **Commit** with descriptive message listing all task IDs in the batch

#### 2e: Post-Wave Checks

After ALL parallel groups and sequential sub-batches in a wave complete:

1. **Integration smoke test**: If `state.json.quality_gates.integration_cmd` is configured, run it:
   - For API projects: start the server, hit key endpoints, verify they return expected status codes
   - For frontend projects: start the dev server, load main pages, verify no uncaught errors
   - Example: `node scripts/smoke-test.js` or `pnpm test:integration`
   - **On failure**: Roll back the ENTIRE wave (`git reset --hard <pre-wave-SHA>`), log the failure, and re-run the wave's tasks SEQUENTIALLY instead of in parallel. This catches incompatibilities that parallel execution introduced.
   - **On success**: Continue to next checks.

<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>

2. **MANDATORY: Grep-based wired verification** — This is the #1 failure mode in spec-engine. Agents routinely mark `wired: "yes"` on components that have zero imports. You MUST run these grep checks. Do NOT trust self-reported wired status.

   For EACH task in the wave marked `wired: "yes"` in state.json:

   a. **Identify the task's primary export**: Read the task's main output file and extract the exported name (function, component, class, constant).

   b. **Grep the entire codebase for imports of that export**:
   ```bash
   # Search for any import of the component/function
   grep -r "import.*ComponentName" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ | grep -v "node_modules" | grep -v "<the_defining_file_itself>"
   ```

   c. **Evaluate results**:
   - If **zero imports found outside the defining file**: Downgrade `wired` to `"pending"` in state.json. Append to audit log: `"WIRED DOWNGRADE: T-X export '<name>' has 0 imports in codebase. Downgraded from yes to pending."`
   - If imports found: Keep `wired: "yes"`. Log the verification: `"WIRED VERIFIED: T-X export '<name>' imported by [file list]"`

   d. **Specific patterns to check**:
   - **API routes**: `grep -r "import.*routeName\|require.*routeName" src/` AND check the app entry point for `.use()` or route registration
   - **React components**: `grep -r "import.*ComponentName\|<ComponentName" src/` AND check router/navigation config
   - **Services/utilities**: `grep -r "import.*serviceName" src/` — must have at least one call site outside the defining file
   - **Middleware**: `grep -r "\.use(.*middlewareName\|import.*middlewareName" src/`

   e. **This check is blocking**: A task with `wired: "pending"` is NOT complete. The completion check in step 2e.6 rejects it. Do not advance to the next wave if wired-pending tasks exist that should be wired.

   **Wiring Verification Red Flags** — if you catch yourself thinking any of these, STOP:

   - "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
   - "I already checked this in a previous wave" — Check again. Code changes between waves.
   - "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
   - "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
   - "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.

3. **Stuck detection**: If any task has `failures >= 3`:
   - Log "AUTO-SKIP: T-X after 3 failures" to state.json audit log, mark task as "skipped", continue to next task.

4. **Progress tracking**: If `tasks_since_checkpoint >= human_checkpoint_interval`:
   - Log progress summary to audit log. Reset counter. Continue execution without pausing.

5. **Budget check**: If `total_tokens >= budget_cap`:
   - Log warning "Budget cap exceeded, continuing" to audit log. Continue execution.

6. **Completion check**: Read state.json.tasks. If ALL tasks have status "completed" AND wired is "yes" or "n/a", break out of loop. Tasks with wired="pending" are NOT done.

7. **Wave advancement**: If all tasks in current wave are completed, increment `current_wave`.

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
3. **Wave Rollback**: git reset to pre-wave state. Triggered when:
   - Integration smoke test fails after parallel wave merge
   - 3+ tasks in wave fail quality gates
   - Post-merge commands fail after retry
   After rollback, re-run the wave sequentially instead of in parallel.
4. **Auto-Escalation**: Auto-skip the task, log "AUTO-ESCALATION-SKIP: T-X" to audit log, continue to next task. Do NOT ask the user.
