---
name: spec-dashboard
description: Show verified status of all specs in the current project
argument-hint: "[--deep] [--deps]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-dashboard

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py dashboard
```

Print the table verbatim. Every column is verified from files (headings present, `validation.status`,
`security.posture_score`, task counts, `acceptance.status`, `docs/`, `release.md`, `retro.md`), not from
self-reports. Then suggest the most useful next action: in-progress specs -> `/spec-status <name>`;
validated -> `/spec-loop <name>`; planning -> `/spec-validate <name>`; accepted but not released ->
`/spec-release <name>`; all released -> `/spec-retro` for any spec without one.

## --deep

For each spec that has requirements.md, dispatch `spec-validator` (in parallel, one Agent call per spec)
with "validate `.claude/specs/<name>/`; return pass/fail per check". Append a `Deep Validation` table
(PASS / WARN with details / SKIP when design is missing).

## --deps

For each spec, parse the `## Depends On` section of requirements.md and render an indented tree with
each spec's `completed/total` and phase. Mark a spec `BLOCKED` when a dependency is below phase
`executed`. Run `spec-state.py deps <name>` per spec to surface cycles.
