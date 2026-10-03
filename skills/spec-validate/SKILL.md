---
name: spec-validate
description: Validate spec completeness and consistency
argument-hint: "[spec-name] [--no-fix] [--strict-lessons]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-validate

Validate a spec for EARS compliance, traceability, codebase accuracy and implementation readiness.
Auto-fixes ERROR-level issues by default (spec files only; the codebase is the source of truth).

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

## Options

- `--no-fix`: report only.
- `--strict-lessons`: lesson-derived rules are ERROR instead of WARNING.

## Workflow

1. `$SS phase-gate <spec> spec` (stop with its message on failure).
2. **Quick-mode**: if `$SS get <spec> quick_mode` is `true`, run only `$SS validate <spec>` and
   `$SS gates <spec>`, report, then go to step 8.
3. **Drift**: `$SS drift <spec>`. If it reports changed files, show them with their commits
   (`git log --oneline <git_sha_start>..HEAD -- <files>`); drift always forces a fix pass even with `--no-fix`.
4. **Fingerprint shortcut**: if `$SS integrity <spec>` passes, no drift, and
   `$SS get <spec> validation.status` is `pass`: print "Spec unchanged since last validation — PASS"
   and go to step 8.
5. **Structure**: `$SS validate <spec>`. On errors, go straight to step 7 with those errors.
6. **Semantic validation**: dispatch `spec-validator` with the spec dir, the full checklist, the
   acknowledged warnings from `$SS get <spec> validation.acknowledged_warnings` ("only re-report if the
   text changed"), and lesson-derived rules:
   - from `lessons.json` entries with category `pattern`/`failure`: WARNING rules (missing error-path
     criteria, routes without auth in design, tasks with >5 files, >30% `Wired: n/a`);
   - entries with `"enforceable": true`: name the `check` to run from the validator's registry.
   Present the report.
7. **Auto-fix** (unless `--no-fix`, except for drift): dispatch `spec-debugger` with the report and
   "fix ERROR-level issues in requirements.md, design.md, tasks.md by reading the actual codebase; never
   touch files outside `.claude/specs/`". Then `$SS sync-tasks <spec>` and `$SS validate <spec>`; if
   still failing, show the remaining issues. Present an "Auto-Fixed Issues" summary.
8. **Record the result** (mandatory on every run):

```
$SS integrity <spec> --update
$SS set <spec> reproducibility.git_sha_start "<git rev-parse HEAD>"
$SS set <spec> validation.status "pass"|"fail"
$SS set <spec> validation.last_pass "<ISO-8601>"        # only on pass
$SS set <spec> validation.acknowledged_warnings '["WARN-1: ...", ...]'
$SS phase <spec> validated                               # only on pass
```

Status is `pass` when no ERRORs remain (including after auto-fix), otherwise `fail`.
