# Quality Gates Reference

Gates run after every wave via `spec-state run-gates`. They are deterministic: no AI judgment decides
pass or fail, and the raw output is persisted to `evidence/tests/` for acceptance.

## Configuration (`init.sh`)

```bash
gates=("lint:npm run lint" "typecheck:npx tsc --noEmit" "test:npm test" "integration:node scripts/smoke.js")
```

- Any gate name works; `lint`, `typecheck`, `test` are conventional.
- A gate named `integration` is skipped by the normal run and executed only with
  `run-gates --only integration --integration` after the whole wave merged (smoke test).
- `spec-state detect-gates` writes this array from `package.json` scripts, `pyproject.toml`,
  `Cargo.toml`, `go.mod` or a `Makefile`.
- Legacy variables `lint_cmd`, `typecheck_cmd`, `test_cmd`, `integration_cmd` are still read.

## Diff mode (baseline-aware)

Projects with pre-existing failures must not block on them. `spec-state run-gates --baseline` runs
every gate once before execution starts and records the error count per gate in
`state.json.quality_gates.baseline_errors`. Later runs fail a gate only when it exits non-zero **and**
its error count exceeds the baseline. `scripts/spec-loop.sh` records the baseline automatically;
in-session orchestration does it in execution-core Step 0.

Error count = lines matching `error`, `FAIL`, `FAILED`, `FAILING` or `✗` (case-insensitive).
That is a heuristic; when a tool supports file arguments or JSON output and you need precision,
make the gate command itself scope to changed files.

## Secret scan

Built into `run-gates --changed <files>`: filenames `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, and
content patterns for AWS keys, private keys, GitHub tokens, OpenAI-style keys and Slack tokens.
Findings are written as `path:line:pattern` only, never the matched value.

## Pipeline per wave

```
run-gates (lint, typecheck, test, secret scan)  --fail-->  spec-debugger (max 2)  --still failing-->  task rollback, failures += 1
verify-wired --apply (grep evidence)            --fail-->  spec-debugger (max 2)  --still failing-->  failures += 1
run-gates --only integration --integration      --fail-->  wave rollback to pre-wave SHA, re-run sequentially
spec-reviewer (Opus; quality + security)        --CRITICAL--> spec-debugger (max 2) --unresolved--> logged, release blocked
```

## Failure tiers

1. **Retry**: debugger fixes, gate re-runs (2 attempts).
2. **Task rollback**: `git checkout <pre_wave_sha> -- <task files>`, `set-task --status failed --fail`.
3. **Wave rollback**: `git reset --hard <pre_wave_sha>` when the integration gate fails or 3+ tasks
   in a wave fail; the wave re-runs with `batch --no-parallel`.
4. **Auto-skip / decompose**: a task with 3 failures is split once by the tasker; if a sub-task fails
   3 times it is skipped and logged. Execution never pauses for a human; review the audit log afterwards.
