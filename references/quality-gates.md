# Quality Gates Reference

Quality gates run automatically after every implementation iteration in spec-exec and spec-loop. They catch defects deterministically — no AI judgment involved.

## Gate Pipeline

```
Implementation complete
        |
        v
   [1. Lint] ──fail──> [Debugger fix] ──retry──> [1. Lint]
        |pass                              |fail(2x)
        v                                  v
   [2. Type Check] ──fail──> [Debugger]  [Task Rollback]
        |pass                              |
        v                                  v
   [3. Regression] ──fail──> [Debugger]  [Wave Rollback]
        |pass                              |
        v                                  v
   [4. Secret Scan] ──fail──> [Unstage]  [Human Escalation]
        |pass
        v
   [Commit]
```

## Diff Mode (Baseline-Aware Gates)

Quality gates should run in **diff mode** when pre-existing errors exist in the project. This prevents pre-existing failures from masking new errors introduced by agents.

### How diff mode works:

1. **Before execution starts**, record baseline error counts in `state.json.quality_gates.baseline_errors`:
   ```json
   {
     "baseline_errors": {
       "lint": 0,
       "typecheck": 12,
       "test": 3
     }
   }
   ```

2. **After each batch**, compare current error count against baseline:
   - If error count **increased**: gate FAILS (new errors introduced)
   - If error count **unchanged or decreased**: gate PASSES

3. **File-scoped mode** (preferred when the tool supports it):
   - Capture changed files: `git diff --name-only <pre-batch-SHA> HEAD`
   - Run lint only on changed files: `eslint <changed-files>` or `ruff check <changed-files>`
   - Type check must still run on the full project (types are global), but only fail on errors in changed files
   - Secret scan only checks changed files

### When to use diff mode:
- Always, when `baseline_errors` is set in state.json
- Automatically, when the first quality gate run detects pre-existing errors — record them as baseline and proceed

## Gate 1: Lint

- **Command**: `lint_cmd` from init.sh
- **Auto-detected if not set**:
  - Node.js: `npx eslint . --ext .ts,.tsx,.js,.jsx` or `npm run lint`
  - Python: `ruff check .` or `pylint`
  - Go: `golangci-lint run`
  - Rust: `cargo clippy`
- **Diff mode**: Run on changed files only if linter supports file arguments. Otherwise run full lint and compare error count against baseline.
- **What it catches**: Style violations, unused imports, unreachable code, formatting issues
- **On failure**: Debugger agent fixes, re-runs gate (max 2 retries)

## Gate 2: Type Check

- **Command**: `typecheck_cmd` from init.sh
- **Auto-detected if not set**:
  - TypeScript: `npx tsc --noEmit`
  - Python: `mypy .` or `pyright`
- **Diff mode**: Run full typecheck (types are global). Compare error count against baseline — fail only if count increased. If possible, filter output to show only errors in changed files.
- **What it catches**: Type errors, hallucinated imports, wrong function signatures, missing modules
- **On failure**: Debugger agent fixes, re-runs gate (max 2 retries)

## Gate 3: Regression Test

- **Command**: `test_cmd` from init.sh
- **Runs the FULL test suite**, not just new tests
- **Diff mode**: Compare test failure count against baseline. New failures = gate fails. Pre-existing failures (same test names) = gate passes.
- **What it catches**: Breaking changes to previously verified tasks, integration failures
- **On failure**: Debugger agent investigates which test broke and why, fixes (max 2 retries)

## Gate 4: Secret Scan

- **No command needed** — built into the commit step
- **Checks staged files against**:
  - `.env`, `.env.*`
  - `*.pem`, `*.key`, `*.p12`, `*.pfx`
  - `credentials*`, `secret*`, `token*`
  - Files matching `.gitignore` patterns
  - Strings matching patterns: `AKIA` (AWS), `-----BEGIN.*PRIVATE KEY-----`, base64 strings > 40 chars
- **On failure**: Unstage the file, warn in audit log, continue

## Gate 5: Post-Parallel Merge Checks (after parallel execution only)

These additional checks run after merging parallel worktrees, before the standard gates:

- **Circular import detection**: Check for circular dependencies introduced by parallel-authored modules. For JS/TS projects, use `madge --circular` or equivalent. For Python, check with `import-linter` or a custom script.
- **Route collision detection**: If the project has an API router, check that no two routes conflict (e.g., `/users/:id` vs `/users/search`).
- **Type stub cleanup**: Remove any `.d.ts` stub files generated for cross-worktree type resolution.
- **Generated file regeneration**: Run commands from `state.json.parallel.post_merge_commands` (lockfile regen, codegen, cache clean).

These checks are skipped when running in sequential mode.

## Gate 6: Integration Smoke Test (post-wave)

- **Command**: `integration_cmd` from state.json (configured per-project)
- **Runs after each WAVE completes** (not each task — each wave)
- **Purpose**: Verify that the system actually works end-to-end after merging parallel agent output
- **Examples**:
  - API project: `node scripts/smoke-test.js` — start server, hit key endpoints, verify 200s
  - Frontend project: `npx playwright test smoke.spec.ts` — load main pages, verify no errors
  - Full-stack: `docker compose up -d && ./scripts/e2e-smoke.sh`
- **What it catches**: Parallel agents using incompatible interfaces, wired but non-functional code, runtime errors that pass type checking
- **On failure**: **Wave-level rollback** — reset to pre-wave SHA, re-run the wave sequentially instead of in parallel
- **Configuration** in state.json:
  ```json
  {
    "quality_gates": {
      "integration_cmd": "node scripts/smoke-test.js"
    }
  }
  ```

## Tiered Failure Recovery

When quality gates fail repeatedly:

### Tier 1: Retry (default)
Spawn debugger agent to fix the specific issue. Re-run the failing gate. Max 2 retries per task.

### Tier 2: Task Rollback
If 2 retries fail, `git reset` to the pre-task checkpoint. Mark task as failed in state.json. Increment `tasks[task_id].failures`. Move to next task.

### Tier 3: Wave Rollback
If 3+ tasks in the same wave fail, `git reset` to the pre-wave checkpoint. Re-plan the wave or skip it.

### Tier 4: Human Escalation
After a wave-level rollback, pause execution. Present failure details to the user. Wait for human decision: retry, skip, or abort.

## Auto-Detection Logic

If init.sh does not define quality gate commands, the system attempts to detect them:

1. Check `package.json` for `scripts.lint`, `scripts.typecheck`, `scripts.test`
2. Check for `pyproject.toml` with `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]`
3. Check for `Makefile` with `lint`, `test`, `check` targets
4. Check for `Cargo.toml` (implies `cargo clippy` and `cargo test`)
5. Check for `go.mod` (implies `go vet` and `go test ./...`)

If no commands are detected, the gate is skipped with a warning logged to audit.

## Configuring in init.sh

```bash
# Uncomment and customize for your project:
# lint_cmd="npm run lint"
# typecheck_cmd="npx tsc --noEmit"
# test_cmd="npm test"
# integration_cmd="node scripts/smoke-test.js"
```

These values are read into `state.json.quality_gates` at execution start.

## Configuring Baseline Errors

If your project has pre-existing lint/typecheck/test failures, set the baseline on first run:

```bash
# Run once to establish baseline:
npx tsc --noEmit 2>&1 | grep -c "error TS"  # e.g., 12
npm test 2>&1 | grep -c "failing"             # e.g., 3
```

Then set in state.json:
```json
{
  "quality_gates": {
    "baseline_errors": { "lint": 0, "typecheck": 12, "test": 3 }
  }
}
```

Alternatively, spec-loop will auto-detect baselines on first gate run if it encounters pre-existing failures.
