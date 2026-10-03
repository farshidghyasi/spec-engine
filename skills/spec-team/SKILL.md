---
name: spec-team
description: Execute spec with a coordinated agent team (Implementer, Tester, Reviewer, Debugger)
argument-hint: "[spec-name] [--max-iterations N] [--no-parallel]"
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

# /spec-team

`/spec-loop` plus an independent tester per task. Use it when the feature is complex or
security-sensitive, or when tasks were being marked complete without real testing.
Costs roughly 2x `/spec-loop` (each tester has its own context).

## Usage

```
/spec-team [spec-name] [--max-iterations N] [--no-parallel]
```

## Team

| Agent | Model | Role |
|-------|-------|------|
| spec-implementer | Sonnet | Writes code + persistent tests + wiring |
| spec-tester | Sonnet | Verifies wiring independently, runs end-to-end and error paths, persists evidence |
| spec-reviewer | Opus | Read-only quality, architecture, cross-task consistency and security review per wave |
| spec-debugger | Sonnet | Root-cause fixes, max 2 attempts per issue |

Agents communicate through `handoffs/T-X-<role>.md` files (~200 tokens each), never full context.

## Procedure

1. Read `${CLAUDE_PLUGIN_ROOT}/references/execution-core.md` and follow it literally, in **team mode**
   (Step 4 item 2 applies: one `spec-tester` per task before the wave review).
2. Repeat until `done: true` or `--max-iterations` (default 50). If the prompt says "exactly one
   wave batch", stop after one.
3. Each implementer writes `handoffs/T-X-implementer.md`; each tester reads it and writes
   `handoffs/T-X-tester.md`; the reviewer receives all tester handoffs for the wave.

Never call AskUserQuestion.
