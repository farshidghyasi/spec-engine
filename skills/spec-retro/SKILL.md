---
name: spec-retro
description: Run a retrospective to capture lessons learned
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-retro Command

Analyze a completed spec and produce actionable lessons for future specs.

## Usage

```
/spec-retro [spec-name]
```

## Workflow

### Step 1: Gather Data

1. Read state.json for execution metrics:
   - Total iterations, tokens used, duration
   - Per-task failure counts
   - Quality gate pass/fail history from audit log
2. Read tasks.md for task descriptions and completion status
3. Read git log for commit patterns
4. Read evidence/reviews/ for reviewer feedback patterns

### Step 2: Compute Quality Metrics

From state.json audit log:

- **First-pass success rate**: % of tasks passing quality gates on first attempt
- **Debugger invocation rate**: How often the debugger was needed
- **Regression rate**: How often implementing a new task broke existing tests
- **Review rejection rate**: How often the reviewer rejected code

### Step 3: Analyze

- What went well? (tasks that completed smoothly)
- What caused friction? (tasks with multiple failures)
- Root cause analysis for friction points
- Patterns to repeat vs avoid

### Step 4: Write Retrospective

Write `retro.md` to the spec directory with metrics and analysis.

### Step 5: Write Lessons

**Critically important**: Write structured lessons to `.claude/specs/lessons.json` (project-level, shared across all specs):

```json
{
  "version": 1,
  "lessons": [
    {
      "spec_name": "feature-name",
      "date": "2026-03-19",
      "category": "requirements|design|implementation|testing",
      "lesson": "Specific, actionable lesson",
      "source": "retro|debugging|review",
      "severity": "high|medium|low",
      "enforceable": false,
      "check": null
    }
  ]
}
```

The `enforceable` and `check` fields are optional and default to `false` and `null` respectively when absent. Existing lessons.json files without these fields are processed without errors.

When writing a lesson about deprecated fields, stale references, or schema change blast radius, set `"enforceable": true` and `"check": "grep_for_old_field_references"`. This instructs the validator to automatically re-check for the pattern on future runs.

#### Known Checks

| Check Name | Description |
|-----------|-------------|
| `grep_for_old_field_references` | Greps for old field names from `Deprecates` entries in tasks.md; reports uncovered references |

If lessons.json already exists, APPEND to the lessons array. Do NOT overwrite existing lessons.

These lessons will be read by `/spec` and `/spec-brainstorm` to improve future specs.
