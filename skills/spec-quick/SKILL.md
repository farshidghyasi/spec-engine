---
name: spec-quick
description: Quick spec mode — skip requirements/design for small tasks
argument-hint: "<description>"
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

# /spec-quick

For 1-3 file changes with an obvious solution. Creates a minimal spec (tasks only) and executes it
immediately with spec-engine's gates and wiring verification. Use `/spec` when there are
architectural trade-offs, multiple interacting components, or more than one wave.

## Usage

```
/spec-quick <description>
```

## Procedure

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. Name: slugify the first 4-5 words (`fix login button alignment` -> `fix-login-button`). If the
   directory exists, append `-2`, `-3`, ...
2. `$SS init <name> --quick` then `$SS detect-gates <name>`.
3. Read the 1-5 most relevant files (Grep/Glob) to decide which files change.
4. Write `tasks.md` with 1-3 tasks in the standard task format (Status, Wave, Wired, Wire into,
   Dependencies, Covers: quick-mode, Files, Description, Acceptance Criteria with one error path).
   Most quick specs are one task.
5. `$SS sync-tasks <name>` ; `$SS integrity <name> --update` ; `$SS phase <name> validated`.
6. Read `${CLAUDE_PLUGIN_ROOT}/references/execution-core.md` and run Step 0 through Step 5 until
   `done: true` (quick specs are usually one wave).
7. Report `$SS status <name>` and the changed files. Do not suggest `/spec-accept` or `/spec-docs`.
