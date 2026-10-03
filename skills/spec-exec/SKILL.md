---
name: spec-exec
description: Execute one spec task iteration (one wave batch) with quality gates
argument-hint: "[spec-name] [--no-parallel] [--dry-run]"
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

# /spec-exec

One iteration of `/spec-loop`: the pending tasks of the current wave, with gates, wiring
verification, review and commit. Resumable; `state.json` carries the position.

## Usage

```
/spec-exec [spec-name] [--no-parallel] [--dry-run]
```

## Procedure

1. Read `${CLAUDE_PLUGIN_ROOT}/references/execution-core.md` and follow it literally.
2. Run Step 0, then Steps 1-4 exactly once (one `$SS batch` result, all of its groups).
3. Run Step 5. If tasks remain, say so and suggest `/spec-exec` again or `/spec-loop`.

Never call AskUserQuestion. Decisions are logged with `$SS log`.
