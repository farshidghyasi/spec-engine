---
name: spec-loop
description: Loop spec execution with wave-based batching until all tasks complete
argument-hint: "[spec-name] [--dry-run] [--max-iterations N] [--no-parallel]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - Workflow
---

# /spec-loop

Execute every remaining wave of a spec autonomously: parallel implementers where file ownership
allows, quality gates in diff mode, grep-verified wiring, one Opus review per wave, commit per wave.

## Usage

```
/spec-loop [spec-name] [--dry-run] [--max-iterations N] [--no-parallel]
```

## Procedure

1. Read `${CLAUDE_PLUGIN_ROOT}/references/execution-core.md`. It is the complete algorithm; follow it literally.
2. Run Step 0 (preflight) once.
3. Repeat Steps 1-4 until `$SS batch` returns `done: true` or `--max-iterations` (default 50) is reached.
   Use `--no-parallel` as `$SS batch <spec> --no-parallel`.
4. Run Step 5 (completion).

Never call AskUserQuestion. Every decision is made autonomously and logged with `$SS log`.
Progress lines go through `$SS progress` (it prints and appends `progress.log`).

For headless/CI runs use `scripts/spec-loop.sh`, which runs one fresh session per wave with real
token accounting, budget enforcement and crash rollback.
