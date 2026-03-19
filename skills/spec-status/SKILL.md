---
name: spec-status
description: Show status and progress of current spec
allowed-tools:
  - Read
  - Glob
  - Grep
---

# /spec-status Command

Display progress, cost, and health metrics for a spec.

## Usage

```
/spec-status [spec-name]
```

## Workflow

1. **Locate spec**: Find spec directory, validate name
2. **Read state.json** as the primary data source
3. **Read tasks.md** for task descriptions

## Display Format

```
== Spec Status: [feature-name] ==

Progress: [=========>          ] 7/15 tasks (47%)

Wave Breakdown:
  Wave 0: [####] 2/2 complete
  Wave 1: [##--] 2/4 complete  <-- current
  Wave 2: [----] 0/5 pending
  Wave 3: [----] 0/2 pending
  Wave 4: [----] 0/2 pending

Current Batch: T-5, T-6 (Wave 1)

Cost:
  Tokens used: 45,230
  Budget cap: 500,000 (9% used)
  Estimated remaining: ~60,000 tokens

Quality Gates:
  Lint: configured (npm run lint)
  Type check: configured (npx tsc --noEmit)
  Regression: configured (npm test)
  Last regression pass: iteration 5

Issues:
  T-4: 2 failures (stuck detection threshold: 3)
  No blocked tasks

Dependencies:
  auth-system: COMPLETE (10/10 verified) [does not block execution]

Integrity: VALID (spec files match manifest)

Next: Run /spec-exec or /spec-loop to continue implementation
```

## Stuck Detection

Highlight tasks with `failures >= 2` in state.json. If any task has `failures >= 3`, display a prominent warning:

```
WARNING: Task T-4 has failed 3 times. Execution will pause for human review.
Consider: /spec-refine to simplify the task, or manually implement it.
```

## Dependency Display

If the spec has a `## Depends On` section in requirements.md, show dependency status by reading those specs' state.json files.
