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

## Gate 1: Lint

- **Command**: `lint_cmd` from init.sh
- **Auto-detected if not set**:
  - Node.js: `npx eslint . --ext .ts,.tsx,.js,.jsx` or `npm run lint`
  - Python: `ruff check .` or `pylint`
  - Go: `golangci-lint run`
  - Rust: `cargo clippy`
- **What it catches**: Style violations, unused imports, unreachable code, formatting issues
- **On failure**: Debugger agent fixes, re-runs gate (max 2 retries)

## Gate 2: Type Check

- **Command**: `typecheck_cmd` from init.sh
- **Auto-detected if not set**:
  - TypeScript: `npx tsc --noEmit`
  - Python: `mypy .` or `pyright`
- **What it catches**: Type errors, hallucinated imports, wrong function signatures, missing modules
- **On failure**: Debugger agent fixes, re-runs gate (max 2 retries)

## Gate 3: Regression Test

- **Command**: `test_cmd` from init.sh
- **Runs the FULL test suite**, not just new tests
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
```

These values are read into `state.json.quality_gates` at execution start.
