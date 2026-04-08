---
name: spec-docs
description: Generate user-facing documentation from spec and implementation
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-docs Command

Generate documentation from spec files and implemented code.

## Usage

```
/spec-docs [spec-name] [--output-dir <path>]
```

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"accepted"` (order >= 4)
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-docs requires phase 'accepted' to be complete. Current phase: '<CURRENT>'. Run /spec-accept first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.

Note: Phase `'audited'` (order 4) also satisfies this requirement.

## Workflow

1. Locate spec directory, validate spec name
2. Default output: `.claude/specs/<name>/docs/`
3. Delegate to spec-documenter agent with spec files and output directory
4. Present list of generated documents to user

After presenting documents, set `state.json.phase` to `"documented"`.
Log "Phase advanced to 'documented'" to the audit log.
