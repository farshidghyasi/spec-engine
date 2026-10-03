# Execution Core

The single per-wave algorithm used by `/spec-exec`, `/spec-loop`, `/spec-team` and `/spec-quick`.
Deterministic work is done by the CLI; agent fan-out is done by the Workflow tool; you make the
judgment calls in between.

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

Call it via Bash. It never prompts (the plugin's PreToolUse hook auto-allows it). Every subcommand
takes the spec name first; `$SS -h` lists them.

## Rules that are enforced for you

- **Stop hook**: you cannot end the turn while the current batch has tasks `in_progress` or
  `completed` with `wired: pending`. Finish them or run `$SS exec-end <spec>` to abort deliberately.
- **Commit hook**: `git commit` is denied while `state.json` has unstaged changes. Stage it with the code.
- **Wiring** is decided by `$SS verify-wired --apply` (grep evidence), never by an agent's self-report.
- **Files** are decided by `$SS check-files` (stat), never by an agent's self-report.
- **Autonomy**: never call AskUserQuestion during execution. Decide, log with `$SS log`, continue.

## Step 0: Preflight (once per invocation)

```
$SS phase-gate <spec> validated        # stop with its message if it fails
$SS deps <spec>                        # cross-spec dependency gate
$SS drift <spec>                       # exit 1 => referenced files changed
$SS validate <spec>                    # tasks.md <-> state.json structure
$SS integrity <spec>                   # warn on mismatch, then: $SS integrity <spec> --update
$SS detect-gates <spec>                # no-op if init.sh already has gates
$SS exec-start <spec>
```

- On **drift**: dispatch `spec-debugger` with the drift output and the rule "the codebase is the source
  of truth; fix spec files only (requirements.md, design.md, tasks.md)". Then `$SS sync-tasks`,
  `$SS integrity --update`, `$SS set <spec> reproducibility.git_sha_start "<HEAD sha>"`.
- On **validate** failure: dispatch `spec-debugger` with the errors (spec files only), re-run, stop if still failing.
- If `$SS get <spec> quality_gates.baseline_errors` is `{}`: run `$SS run-gates <spec> --baseline`.

## Step 1: Plan the batch

```
$SS batch <spec>            # JSON: {done, wave, groups: [[T-2,T-3],[T-5]], sequential: [T-4]}
$SS summary <spec>          # Layer 0 context for agents
$SS manifest <spec>         # Layer 1.5 import manifest from completed tasks
```

- `done: true` -> go to Step 5.
- `PRE_WAVE_SHA=$(git rev-parse HEAD)`.
- `$SS log <spec> wave_started --wave N --details "<groups>"` and `$SS progress <spec> "Wave N" "<k> pending"`.
- `$SS hook <spec> wave_start N`.
- `$SS set <spec> execution.current_batch '["T-2","T-3",...]'` with every task id in the batch, then
  `$SS set-task <spec> T-X --status in_progress` for each.
- Dependency installs: if several tasks in the wave add packages, install them all on the main branch first.

## Step 2: Implement the batch (Workflow)

Build the workflow input from the batch:

- `tasks`: for each task id, `{ block: <its section of tasks.md>, files: [...], wireInto: "<Wire into line>" }`
- `summary`, `manifest`: the two CLI outputs above
- `lessons`: top 3 relevant entries from `.claude/specs/lessons.json`, or ""
- `fullSpec`: requirements.md + design.md on the first iteration or after a failed task, else ""

Read `${CLAUDE_PLUGIN_ROOT}/workflows/wave.js` and call the **Workflow** tool with `script` = that file's
contents and `args` = `{ spec, wave, groups, sequential, tasks, summary, manifest, lessons, fullSpec }`
(pass real JSON, not a string). The script runs one `spec-implementer` per task: tasks inside a group in
parallel with worktree isolation, groups in order, then the `sequential` list one at a time. It returns
one result per task: `{ task, failed, committed, branch, worktree, files_changed, tests_run,
wiring_evidence, out_of_scope, notes }`. Wait for the completion notification; do not poll.

If the Workflow tool is not available in this session, dispatch the same agents with the Agent tool
(`isolation: "worktree"` for groups of 2+, all in one message) using the prompt text from `wave.js`.

For each result, in this order:

1. **Failed or uncommitted** (`failed`, or `committed: false`, or `files_changed` empty):
   `$SS set-task <spec> T-X --status failed --fail`, log the notes, skip the remaining checks for it.
2. **Merge** (parallel results only, in task-ID order): `git merge --no-edit <branch>`; then
   `git worktree remove --force <worktree>` and `git branch -d <branch>`. Record the SHA before the
   first merge; if any merge fails, `git reset --hard` to it, and re-run the group with
   `$SS batch <spec> --no-parallel` next iteration (log `merge_failed`).
3. **Shared files**: compare `git diff --name-only PRE_WAVE_SHA HEAD` against
   `$SS get <spec> parallel.shared_files`; revert any hit the task did not own
   (`git checkout PRE_WAVE_SHA -- <file>; git commit -m "revert shared file <file>"`) and log it.
4. **Files exist**: `$SS check-files <spec> T-X`. On MISSING: `--status failed --fail`. Log OVERSIZED
   warnings; add an extraction task to tasks.md for the next wave and `$SS sync-tasks`.
5. **Out-of-scope notes**: log them; if a later task owns that file, add a note to its task block.

Post-merge: run every command in `$SS get <spec> parallel.post_merge_commands`. A failure here is
blocking: attempt one auto-fix via `spec-debugger`, then mark the wave failed and skip it.
Format changed files once (biome / prettier / eslint --fix, whichever config exists; never `--unsafe`),
and commit the formatting if it changed anything.

## Step 3: Gates and verification (after all groups in the wave)

```
CHANGED=$(git diff --name-only PRE_WAVE_SHA HEAD)
$SS run-gates <spec> --wave N --changed $CHANGED          # lint/typecheck/test in diff mode + secret scan
$SS verify-wired <spec> --apply                           # all tasks in the wave; writes evidence/wiring-wave-N.md
$SS run-gates <spec> --wave N --only integration --integration   # only if an "integration" gate exists
```

- **Gate failure**: dispatch `spec-debugger` with the evidence file from `evidence/tests/`. Max 2 attempts.
  Still failing: `git checkout PRE_WAVE_SHA -- <task files>`, `$SS set-task T-X --status failed --fail`.
- **Wiring failure** (`WIRING FAIL: T-X`): dispatch `spec-debugger` with the wiring evidence and the
  task's `Wire into` line. Re-run `verify-wired --apply`. Max 2 attempts, then `--status failed --fail`.
  Tasks whose declared files are pure config/infra with no exports: `$SS set-task T-X --wired n/a`
  with a logged justification.
- **Integration failure**: `git reset --hard PRE_WAVE_SHA`, log `wave_rolled_back`, re-run the
  wave with `$SS batch <spec> --no-parallel`.

Several failing tasks: debuggers run one at a time (they share the working tree).

## Step 4: Review, finalize, commit (Workflow)

1. Read `${CLAUDE_PLUGIN_ROOT}/workflows/verify.js` and call **Workflow** with `args` =
   `{ spec, wave, ids, tasks: { id: { block, handoff } }, diff: <git diff PRE_WAVE_SHA..HEAD>,
   wiringEvidence: <evidence/wiring-wave-N.md>, design: <design.md>, team: <true in /spec-team> }`.
   In team mode it runs one `spec-tester` per task first; it always ends with one Opus `spec-reviewer`
   over the whole wave and returns `{ tests, review }`. (Fallback without Workflow: the same two agent
   dispatches via the Agent tool.)
2. Write `review.report` to `evidence/reviews/wave-N.md` and each `review.critical` entry to
   `handoffs/security-T-X-critical.md`. Update counts:
   `$SS set <spec> security.findings '{"critical":C,"high":H,"medium":M}'` (add to existing values).
3. **Tester failures** (`WIRING_FAIL` / `FUNCTIONAL_FAIL`) and **CRITICAL findings**: dispatch
   `spec-debugger` (max 2 per issue), then re-run the relevant check (`verify-wired --apply`,
   `run-gates`, or a re-review). Unresolved CRITICAL: `$SS log <spec> unresolved_critical --wave N`
   and continue. `REJECTED` non-security tasks: debugger once, then continue.
4. For every task that passed: `$SS set-task <spec> T-X --status completed` (wired was set by
   `verify-wired`), `$SS hook <spec> task_complete T-X completed`,
   `$SS progress <spec> "T-X completed" "<done>/<total>"`.
5. `$SS log <spec> wave_completed --wave N`; `$SS set <spec> execution.current_batch '[]'`; commit:
   `git add <changed files> .claude/specs/<spec>/` then `git commit -m "spec(<spec>): wave N — T-X, T-Y"`.
6. **Stuck tasks** (`failures >= 3`): if `decomposed` is already true -> `--status skipped` and log
   `AUTO-SKIP`. Otherwise dispatch `spec-tasker` to split it into 2-3 tasks with non-overlapping
   Files, new IDs after the max existing, `decomposed_from: T-X`; set the original's `Status` to
   `decomposed` in tasks.md, `$SS set <spec> tasks.T-X.decomposed true`, `$SS sync-tasks`, `$SS integrity --update`.

## Step 5: Completion

```
$SS complete <spec> && { $SS phase <spec> executed; $SS hook <spec> spec_complete completed; }
$SS exec-end <spec>
```

Then print `$SS status <spec>` and suggest `/spec-accept`, `/spec-security-audit`, `/spec-docs`,
`gh pr create --head spec/<spec>`.

If the invocation is single-iteration (`/spec-exec`, `/spec-quick`, or `--max-iterations` reached),
still run `$SS exec-end <spec>` before stopping and report `$SS status <spec>`.

## Dry run

With `--dry-run`: print `$SS batch` and `$SS summary`, estimate ~8k tokens per task, and stop. Do not dispatch anything.
