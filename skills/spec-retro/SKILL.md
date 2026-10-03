---
name: spec-retro
description: Run a retrospective to capture lessons learned
argument-hint: "[spec-name]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-retro

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. `$SS phase-gate <spec> released` (`verified` also satisfies it; stop with the message on failure).
2. Gather: `$SS summary <spec>`, state.json `audit_log` and `execution` (iterations, tokens, failures
   per task, gate pass/fail events), tasks.md, `git log --oneline <git_sha_start>..HEAD`,
   `evidence/reviews/`.
3. Compute from the audit log: first-pass gate success rate, debugger invocation rate, regression
   rate (gate_failed on `test`), review rejection rate, wiring downgrade count.
4. Analyze: what went smoothly, what caused friction (tasks with failures >= 1), root causes, patterns
   to repeat or avoid.
5. Write `retro.md` in the spec dir.
6. Append lessons to `.claude/specs/lessons.json` (create it if missing; never overwrite existing entries):

```json
{
  "spec_name": "<spec>",
  "date": "YYYY-MM-DD",
  "category": "requirements|design|implementation|testing",
  "lesson": "Specific, actionable lesson",
  "source": "retro|debugging|review",
  "severity": "high|medium|low",
  "enforceable": false,
  "check": null
}
```

Lessons about deprecated fields or schema blast radius get `"enforceable": true` and
`"check": "grep_for_old_field_references"` so `/spec-validate` re-checks them automatically.
These lessons are read by `/spec` and `/spec-brainstorm`.

7. `$SS phase <spec> retro`.
