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

Execute a single iteration of spec-driven implementation with quality gates, parallel execution for independent tasks, structural completion detection, and tiered failure recovery.

## Usage

```
/spec-exec [spec-name] [--no-parallel]
```

## Rationalization Prevention

Every step below is mandatory. You WILL be tempted to skip steps that seem unnecessary. This table exists because every rationalization below has caused real failures.

| You will think... | Reality |
|---|---|
| "Only 1 parallel group, skip import manifest" | Even sequential tasks need the manifest — they import from previous waves. |
| "The agent committed its work" | Agents routinely do not commit. Always auto-commit after agent completes. |
| "This agent wouldn't touch shared files" | Always check. Agents modify routers, entry points, and config files unprompted. |
| "Quality gates passed, task is done" | Gates test syntax, not integration. Always run integration test if configured. |
| "Agent said wired: yes" | Verify with grep. Self-reported wired status is wrong ~30% of the time. |
| "Post-merge build failed but it's unrelated" | It's never unrelated. A failed build means the merge broke something. Stop and fix. |
| "Pre-existing errors, ignore gate output" | Use diff mode. Compare against baseline. You cannot distinguish new from old without it. |

## Progress Streaming

Emit structured progress lines during execution:

- Before task dispatch: `[HH:MM:SS] ▸ T-X implementing │ <files>`
- After task completes: `[HH:MM:SS] ▸ T-X completed │ N/M tasks done`
- After quality gates: `[HH:MM:SS] ▸ lint ✓ │ typecheck ✓ │ test ✓`
- On wiring check: `[HH:MM:SS] ▸ T-X wired ✓` or `[HH:MM:SS] ▸ T-X wired ✗ (downgraded)`

Append each line to `.claude/specs/<name>/progress.log`.

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"validated"`
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-exec requires phase 'validated' to be complete. Current phase: '<CURRENT>'. Run /spec-validate first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.

## Dependency Gate

Read `requirements.md` for a `## Depends On` section. For each listed dependency spec name:
1. Validate the spec name contains only alphanumeric characters, hyphens, and underscores.
   If it contains path separators (`/`, `\`) or `..` sequences: log a warning and skip it.
2. Read `.claude/specs/<dep-name>/state.json`
3. Check `state.json.phase` is at phase order >= 4 (`"accepted"` or `"audited"` or later).
   If `phase` is absent, treat as not accepted.
4. If any dependency is not accepted, display:
   "Dependency gate: spec '<dep-name>' is at phase '<phase>', requires 'accepted'. Run /spec-accept <dep-name> first."
   Stop execution.
5. If the dependency directory does not exist: display
   "Dependency gate: spec '<dep-name>' not found in .claude/specs/."
   Stop execution.
6. If no `## Depends On` section exists or it is empty: skip this check and proceed.

## Workflow

### Step 1: Load State

1. Locate spec directory, validate spec name
2. Read `state.json`
3. **Verify integrity manifest**: Compute SHA256 of requirements.md, design.md, tasks.md. Compare against `state.json.integrity`. If mismatch:
   - Log which files changed to audit log
   - Update the manifest and proceed — do NOT ask the user

### Step 1.5: Drift Detection

Check if the codebase changed under this spec since it was written:

1. Read `state.json.reproducibility.git_sha_start` and `state.json.reproducibility.referenced_codebase_files`
2. If both exist, run: `git diff --name-only <git_sha_start>..HEAD -- <referenced_files>`
3. If any files changed:
   - Log to audit log: `"DRIFT DETECTED: N referenced files changed since spec was written"`
   - **Auto-fix**: Run the spec-validator then spec-debugger to update spec files to match the current codebase (same as `/spec-validate` auto-fix). The codebase is the source of truth — the spec must be updated, never the codebase.
   - Recompute integrity manifest after fixes
   - Update `git_sha_start` to current HEAD
   - Present a summary of what drifted and what was fixed

### Step 1.7: Fresh Validation

Run inline structural checks (do NOT dispatch the validator agent):
1. Read state.json and count task IDs in `state.json.tasks`
2. Read tasks.md and count `### T-` headings
3. Verify every task ID in state.json exists as a `### T-X` heading in tasks.md (and vice versa)
4. Verify wave assignments: for each task, `state.json.tasks[T-X].wave` matches the `Wave:` field in tasks.md
5. Verify all `Dependencies` values in tasks.md reference valid task IDs (no dangling references)
6. Verify no circular dependencies: BFS from each task; if any task appears in its own dependency chain, report a circular dependency error
7. If any check fails: display the specific error, dispatch spec-debugger to fix, and stop execution if the fix fails
8. If all checks pass: log "Fresh validation passed: N tasks, M waves, 0 structural errors" to the audit log

### Step 2: Check Preconditions

1. **Cross-spec dependencies**: If requirements.md has `## Depends On`, verify those specs are complete
2. **Budget cap**: If `state.json.execution.budget_cap` is set and `total_tokens` exceeds it, log a warning and continue
3. **Stuck detection**: If any pending task has `failures >= 3`, log "AUTO-SKIP: T-X after 3 failures" to audit log, mark as "skipped", continue to next task

### Step 3: Select Task Batch and Build Parallel Groups

1. Record the current git SHA as `pre_wave_sha` (for wave rollback if needed)
2. Read `state.json.waves` to find the current wave
3. Collect pending tasks in the current wave
4. **Shared File Hard Gate**: Before building parallel groups for this wave:
   1. Read `state.json.parallel.shared_files`
   2. For each task in the wave, compare its `Files` array against `shared_files`
   3. If ANY file matches: move that task to a sequential sub-batch
   4. Log "SHARED FILE ISOLATION: T-X moved to sequential -- owns shared file <path>"
   5. After the wave completes, run barrel reconciliation: for each file in `shared_files`
      modified by any task (detected via `git diff`), consolidate all modifications into a
      single coherent version. If reconciliation cannot auto-resolve a conflict, log it and
      dispatch spec-debugger.

5. **Build parallel groups** from file ownership:
   - Read `files` field from each task in state.json
   - Tasks with non-overlapping files form a parallel group
   - Tasks with file conflicts go into sequential sub-batches
6. Update `state.json.execution.current_batch` with the first parallel group's task IDs
7. **Generate import manifest**: Scan all files created/modified by completed tasks in previous waves. For each file, extract its exports (functions, classes, types, constants). Build a manifest of exact export names, function signatures, and file paths. This prevents agents from guessing import names.

### Step 4: Implementation

**If parallel group has 1 task** — spawn a single spec-implementer agent.

**If parallel group has 2+ tasks** — spawn parallel spec-implementer agents:
- Launch each via the Agent tool with `isolation: "worktree"`
- Each agent receives:
  - **Layer 0**: state.json summary (~200 tokens) — current wave, batch, completed tasks
  - **Layer 1**: ONLY its assigned task description from tasks.md
  - **File boundaries**: "You MUST only create/modify these files: [list from Files field]"
  - **Layer 1.5**: Import manifest from completed waves — exact export names, function signatures, and file paths. "Use EXACTLY these imports — do not guess or assume names."
  - **Layer 2** (first iteration or after errors): Full requirements.md and design.md
  - **Context from lessons.json**: If relevant lessons exist, include top 3
- **All parallel agents are launched in a single message** (multiple Agent tool calls)
- Wait for all agents to complete

<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>

- **Post-agent verification** (for each worktree, before merge):
  a. **Auto-commit**: `git add <task Files>` then `git commit -m "feat: T-{id} — {subject}"` in the worktree
     **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:
     - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
     - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
     - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
  b. **Shared file enforcement**: `git diff --name-only HEAD~1` — if any shared file was modified, revert it and log a warning
  c. **Cross-agent import resolution**: Scan each agent's imports of other agents' files. If mismatches found, fix directly via Edit or re-dispatch sequentially
- Merge worktree changes back sequentially

Tell each implementer:
- Complete your assigned task
- Write persistent test files
- Follow the project's coding conventions
- Wire everything into the application
- **Only create/modify your assigned files** — do not touch files owned by other tasks
- Report files changed and test file locations

### Step 4.5: Post-Merge Regeneration

Run commands from `state.json.parallel.post_merge_commands` (lock file regen, codegen, cache clean). **If any command fails, treat it as a blocking error** — halt, attempt auto-fix, skip wave if still failing.

### Step 4.7: Auto-Format Changed Files

After merge and before quality gates:
1. If the changed file list is empty: skip this step.
2. Detect formatter from project root config files:
   - If `biome.json` exists: command = `npx biome check --write <changed_files>`
   - Else if `.prettierrc` or `.prettierrc.*` or `prettier.config.*` exists: command = `npx prettier --write <changed_files>`
   - Else if `.eslintrc` or `.eslintrc.*` or `eslint.config.*` exists: command = `npx eslint --fix <changed_files>`
   - Else: log "No formatter detected, skipping auto-format" to audit log and skip
3. Do NOT pass `--unsafe` flag for `.tsx` or `.jsx` files under any circumstances.
4. Execute ONLY the predefined formatter command above. Do NOT execute arbitrary commands from config file contents.
5. If the formatter command exits non-zero: log the failure details to the audit log and proceed (auto-format is best-effort, not blocking).

### Step 5: Quality Gates (Diff Mode)

After all implementers complete (and worktrees are merged), run quality gates in **diff mode**:

1. Capture changed files: `git diff --name-only <pre_wave_sha> HEAD`
2. **Resolve gate commands**: Check `state.json.quality_gates.gates[]` first (new format: array of `"name:command"` entries). If empty or missing, fall back to legacy fields (`lint_cmd`, `typecheck_cmd`, `test_cmd`). Run each gate in order.
3. **Lint** (if configured): Run linter on changed files only if supported, otherwise run full lint and compare error count against `state.json.quality_gates.baseline_errors` — fail only if count increases
4. **Type Check** (if configured): Run typecheck command. If pre-existing errors exist, compare against baseline — fail only on NEW errors in changed files
5. **Regression Test** (if configured): Run test command — pre-existing failures should be baselined
6. **Secret Scan**: Only scan changed files for sensitive patterns

If any gate fails:
- Spawn **spec-debugger** agent to fix the issue (max 2 retries per task)
- Re-run the failing gate after each fix
- If 2 retries exhausted: **Task Rollback** — `git checkout` the changed files, increment `tasks[id].failures` in state.json

### Step 5.5: Integration Smoke Test

If `state.json.quality_gates.integration_cmd` is configured, run it after quality gates pass. On failure: roll back the wave to `pre_wave_sha` and re-run sequentially.

### Step 5.6: Wired Status Verification

<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>

For EACH task marked `wired: "yes"` in state.json:

1. **Identify the task's primary export**: Read the task's main output file and extract the exported name (function, component, class, constant).

2. **Grep the entire codebase for imports of that export**:
   ```bash
   grep -r "import.*ExportName" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ | grep -v "node_modules" | grep -v "<the_defining_file_itself>"
   ```

3. **Evaluate results**:
   - If **zero imports found outside the defining file**: Downgrade `wired` to `"pending"` in state.json. Append to audit log: `"WIRED DOWNGRADE: T-X export '<name>' has 0 imports in codebase."`
   - If imports found: Keep `wired: "yes"`. Log: `"WIRED VERIFIED: T-X export '<name>' imported by [file list]"`

4. **Pattern-specific checks**:
   - **API routes**: grep for import AND check app entry point for `.use()` or route registration
   - **React components**: grep for import AND check router/navigation config
   - **Services/utilities**: must have at least one call site outside the defining file
   - **Middleware**: grep for `.use()` pattern or imports

5. **This check is blocking**: A task with `wired: "pending"` is NOT complete. Do not advance to the next wave if wired-pending tasks exist that should be wired.

**Wiring Verification Red Flags** — if you catch yourself thinking any of these, STOP:

- "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
- "I already checked this in a previous wave" — Check again. Code changes between waves.
- "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
- "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
- "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.

**Evidence Writing**: After all grep checks, write `evidence/wiring-wave-N.md` (N = current wave):
```
# Wiring Evidence: Wave N

## T-X: <task title>
- Export: <export_name>
- Grep command: `<command>`
- Grep output: <output or "no imports found">
- Result: PASS / FAIL
```
**WIRING HARD GATE**: If any task has `wired: "pending"` after verification (excluding tasks
marked `wired: "n/a"`): log "WIRING HARD GATE: Wave N blocked -- T-X has wired=pending" to
the audit log and STOP. Do not advance to the next wave.

### Step 6: Update State

After successful quality gates:

1. Update each completed task in `state.json.tasks`: status = "completed", record tokens_used
2. Increment `state.json.execution.iteration`
3. Update `state.json.execution.total_tokens`
4. Update `state.json.execution.last_iteration_at`
5. Increment `state.json.execution.tasks_since_checkpoint`
6. Append audit log entry: task_completed event with git SHA, tokens, quality gate results, parallel=true/false
7. Record model version in `state.json.reproducibility.model_versions` if not already present
8. **Run lifecycle hook**: For each completed task, execute `hook_on_task_complete` if configured in init.sh. Best-effort.

### Step 7: Commit

**ATOMIC STATE UPDATE**: Before running `git add`, update `state.json.tasks[T-X].status`
to `"completed"`. Do NOT defer state.json updates to wave boundaries.
Include `.claude/specs/<name>/state.json` in `git add` alongside the task's declared Files.
The state.json MUST be in the same commit as the task's code changes.

1. Stage changed files (excluding secrets detected in Step 5)
2. Commit with descriptive message referencing task IDs

### Step 8: Completion Check

1. **Structural detection**: Read state.json.tasks. If ALL tasks have status "completed" AND wired is "yes" or "n/a", report completion. Tasks with wired="pending" are NOT done.
2. If current wave is complete, advance `state.json.execution.current_wave`
3. Report status: "Completed T-X, T-Y (parallel, Wired: yes). Wave 1: 4/4 done. Advancing to Wave 2. 7/15 tasks total."
4. If all tasks complete, suggest next steps: `/spec-accept`, `/spec-docs`, `gh pr create --head spec/<name>`
5. If all tasks complete, run `hook_on_spec_complete` synchronously if configured in init.sh.

When all tasks have `status: "completed"` and `wired: "yes"` or `"n/a"`:
Set `state.json.phase` to `"executed"`.
Log "Phase advanced to 'executed'" to the audit log.

## Dry-Run Mode

If the user says "dry run" or "--dry-run":

1. Parse the task DAG from state.json
2. Identify parallel groups from file ownership
3. Show the execution plan: waves, parallel groups, estimated tokens, estimated cost
4. Do NOT execute anything
