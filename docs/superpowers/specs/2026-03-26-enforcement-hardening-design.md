# Spec-Engine Enforcement Hardening

**Date**: 2026-03-26
**Status**: Approved
**Motivation**: Feedback from running spec-engine on two real specs (Spec 02: 15 tasks, Spec 03: 30 tasks) revealed that existing rules are specified but not reliably followed by agents, plus missing knowledge for two common failure patterns.

## Problem

Two categories of failure observed in production spec runs:

1. **Enforcement failures** — Rules exist in spec-loop/spec-exec/spec-team but agents don't reliably follow them:
   - Wiring verification: Agents self-report `wired: yes` without verifying imports exist (e.g., RefundDialog had 9 passing tests and `wired: yes` but zero imports anywhere)
   - Auto-commit: Every wave required manual `git add` + `git commit` despite instructions to auto-commit

2. **Missing knowledge** — No instructions exist for:
   - Signature change propagation: Changing a function signature (e.g., sync to async) only updates callers listed in the task, missing others
   - UX interaction pattern: Brainstorm doesn't ask "page vs modal vs dialog?" causing full rework cycles (payment flow went through 3 iterations)

## Approach

Apply the same enforcement patterns that superpowers skills use (HARD-GATE, red flags, zero-trust framing) to harden existing spec-engine rules. Add new rules for the knowledge gaps.

**Key principle**: Duplicate enforcement language inline in each skill file. No shared reference files — agents must see the enforcement in context, not follow a pointer to another file.

## Improvement 1: Harden Wiring Verification

### Current State

- `spec-loop/SKILL.md` step 2e.2: Full grep-based verification specified (lines 313-335)
- `spec-exec/SKILL.md` step 5.6: Single vague sentence — "verify the claim by grepping the app entry point"
- `spec-team/SKILL.md` phase 4 step 11: Single vague sentence — same as spec-exec
- `spec-implementer.md`: Has "Verification Iron Law" with grep requirement

**Failure mode**: Despite spec-loop having detailed instructions, agents skip the grep. spec-exec and spec-team don't even specify what "grepping" means in detail.

### Changes

**Files modified**: `skills/spec-loop/SKILL.md`, `skills/spec-exec/SKILL.md`, `skills/spec-team/SKILL.md`

**In all 3 files**, add before the wiring verification step:

```markdown
<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>
```

**In all 3 files**, add after the wiring verification step:

```markdown
### Wiring Verification Red Flags

If you catch yourself thinking any of these, STOP — you are about to skip verification:

- "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
- "I already checked this in a previous wave" — Check again. Code changes between waves.
- "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
- "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
- "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.
```

**In spec-exec and spec-team specifically**, expand step 5.6 / phase 4 step 11 from one sentence to the full grep-based verification procedure (matching spec-loop's step 2e.2 detail level):

1. Identify the task's primary export from its main output file
2. Grep the codebase for imports of that export (excluding the defining file)
3. If zero imports: downgrade to `wired: "pending"`, log to audit
4. If imports found: keep `wired: "yes"`, log verification
5. Pattern-specific checks (API routes, React components, services, middleware)
6. Blocking: tasks with `wired: "pending"` are NOT complete

## Improvement 2: Harden Auto-Commit

### Current State

- `spec-loop/SKILL.md` step 2d.4a: Auto-commit specified with bash commands
- `spec-exec/SKILL.md` step 4: Sub-bullet "Auto-commit: `git add <task Files>` then `git commit`"
- `spec-team/SKILL.md` phase 1 step 2a: Sub-bullet, same as spec-exec
- Rationalization table entry exists: "The agent probably committed its work" / "Agents routinely do not commit"

**Failure mode**: Auto-commit is a sub-bullet buried in a list. Agents treat it as optional. Every wave in real runs required manual commits.

### Changes

**Files modified**: `skills/spec-loop/SKILL.md`, `skills/spec-exec/SKILL.md`, `skills/spec-team/SKILL.md`

**In all 3 files**, add before the post-agent verification section:

```markdown
<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>
```

**In all 3 files**, add after the auto-commit step:

```markdown
### Auto-Commit Red Flags

If you catch yourself thinking any of these, STOP — you are about to skip the commit:

- "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
- "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
- "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
```

## Improvement 3: Signature Change Propagation

### Current State

No guidance exists in spec-tasker or spec-implementer for handling tasks that change existing function signatures. Agents update only the files explicitly listed in the task, missing other callers.

**Failure mode**: Making `getTaxProvider()` async missed `refund-service.ts` as a caller because it wasn't listed in the task's Files array.

### Changes

**File modified**: `agents/spec-tasker.md`

Add new section after "Task Requirements":

```markdown
## Signature Change Rule

If a task modifies an existing function's signature (adding/removing parameters,
changing return type, sync to async, renaming), the task description MUST include:

1. The exact signature change: `functionName(a) -> functionName(a, b)`
2. A grep instruction: `grep -r "functionName" --include="*.ts" --include="*.tsx" src/`
3. An acceptance criterion: "All callers of functionName updated to new signature"
4. ALL known caller files added to the task's Files array

If the caller list might be incomplete, add to the description:
"Run grep before implementing to discover all callers. Add any unlisted caller
files to your scope and update them."
```

**File modified**: `agents/spec-implementer.md`

Add new section in Process, after step 3 ("Read relevant existing code"):

```markdown
### Signature Changes

If your task changes any existing function's signature:

1. **Before implementing**: Run the grep command from the task description
   (or `grep -r "functionName" --include="*.ts" --include="*.tsx" src/` if none provided)
2. **Identify ALL callers** — not just the ones listed in the task
3. **Update every caller** — if a caller is outside your file boundaries,
   note it in your handoff file as "SIGNATURE BREAK: <file> calls <function>
   with old signature"
4. **Verify no remaining callers use old signature**:
   Re-run grep after changes, confirm zero hits for old pattern
```

## Improvement 4: UX Interaction Pattern Question

### Current State

`spec-brainstorm/SKILL.md` explores 7 topics (problem, users, success criteria, scope, architecture, risks, alternatives) but never asks about UI interaction patterns.

**Failure mode**: Payment flow went through 3 iterations (page -> modal -> dialog) because requirements didn't specify the interaction pattern.

### Changes

**File modified**: `skills/spec-brainstorm/SKILL.md`

Add new bullet in step 4 "Topics to explore" list, after "Are there existing patterns in the codebase we should follow?":

```markdown
- If the feature includes user-facing screens: What interaction pattern should each
  screen use? (page, modal, dialog, drawer, inline expansion, wizard) This matters
  most for screens users will hit frequently — getting it wrong means full rework.
  Ask early: "For [screen X], should this be a full page, a modal overlay, a dialog,
  or something else? Consider how often users will use it and what context they need
  to keep visible."
```

## Files Changed Summary

| File | Change Type | Size |
|------|------------|------|
| `skills/spec-loop/SKILL.md` | Add HARD-GATEs + red flags for wiring and auto-commit | ~40 lines added |
| `skills/spec-exec/SKILL.md` | Expand step 5.6 + add HARD-GATEs + red flags | ~60 lines added |
| `skills/spec-team/SKILL.md` | Expand phase 4 step 11 + add HARD-GATEs + red flags | ~60 lines added |
| `agents/spec-tasker.md` | New "Signature Change Rule" section | ~15 lines added |
| `agents/spec-implementer.md` | New "Signature Changes" protocol in Process | ~12 lines added |
| `skills/spec-brainstorm/SKILL.md` | New exploration topic bullet | ~5 lines added |

## What This Does NOT Change

- No new files created
- No changes to state.json schema
- No changes to spec-planner, spec-validator, spec-reviewer, or other agents
- No changes to CI/CD scripts
- No shared reference files — all enforcement is inline

## Success Criteria

1. Wiring verification grep runs on every wave in spec-loop, spec-exec, and spec-team
2. Auto-commit happens immediately after every agent completion, before any other post-agent step
3. Tasks that change function signatures include grep instructions and caller file lists
4. Brainstorm asks about interaction patterns when UI screens are involved
