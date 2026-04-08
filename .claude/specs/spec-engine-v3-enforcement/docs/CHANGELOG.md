# Changelog: spec-engine v3 Enforcement Enhancements

> Implemented in spec `spec-engine-v3-enforcement` (14 tasks, 3 waves). All 14 tasks completed. Phase: accepted.
> Base commit: `36267ca`

---

## Phase Gates (US-1, US-2)

### Pipeline Phase Gate added to 10 skills

Every pipeline skill now reads `state.json.phase` at startup and refuses to proceed if the prerequisite phase has not been reached. The phase sequence is:

```
spec -> validated -> executed -> accepted/audited -> documented -> released -> verified -> retro
```

Each skill also advances `state.json.phase` to its own phase value on successful completion.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`, `skills/spec-accept/SKILL.md`, `skills/spec-security-audit/SKILL.md`, `skills/spec-docs/SKILL.md`, `skills/spec-release/SKILL.md`, `skills/spec-verify/SKILL.md`, `skills/spec-retro/SKILL.md`, `skills/spec-validate/SKILL.md`, `skills/spec/SKILL.md`

**Error message format** (on phase gate block):
```
Phase gate: /spec-exec requires phase 'validated' to be complete. Current phase: 'spec'. Run /spec-validate first.
```

### Cross-Spec Dependency Gate added to 3 execution skills

`/spec-exec`, `/spec-loop`, and `/spec-team` now check cross-spec dependencies before starting. If `requirements.md` has a `## Depends On` section, each listed dependency must be at phase `"accepted"` or later. Spec names containing path separators or `..` sequences are rejected.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`

---

## Orchestrator Improvements (US-3, US-4, US-5, US-10, US-11, US-13)

### Auto-Format After Agent Merge (US-3)

After each agent merge and before quality gates, execution skills now auto-detect and run the project formatter on changed files. Detection priority: `biome.json` -> `.prettierrc*` -> `.eslintrc*`. The `--unsafe` flag is never passed for `.tsx` or `.jsx` files. Formatting failures are non-blocking (logged, not halted).

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`

### Atomic state.json Commits Per Task (US-4)

`state.json` is now included in the same `git commit` as each task's code changes. Task status is updated in `state.json` before `git add` runs, not deferred to wave boundaries.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`

### Wiring Evidence Files + Hard Gate (US-5)

After wiring verification for each wave, the orchestrator writes `evidence/wiring-wave-N.md` containing each task's export name, the grep command executed, grep output, and PASS/FAIL result. If any task still has `wired: "pending"` after verification, wave advancement is blocked (hard gate).

`/spec-accept` now reads all `evidence/wiring-wave-*.md` files and passes them to the acceptor. Waves missing a wiring evidence file are flagged as gaps.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`, `skills/spec-accept/SKILL.md`

### Fresh Pre-Execution Validation (US-10)

`/spec-exec` and `/spec-loop` now run inline structural validation after drift detection (new Step 1.7). Checks: task ID consistency between `state.json` and `tasks.md`, wave assignment consistency, no dangling dependency references, no circular dependencies (BFS). On failure, `spec-debugger` is dispatched; execution stops if the fix fails.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`

### Shared File Isolation Hard Gate (US-11)

Before building parallel groups, execution skills now compare each task's `Files` array against `state.json.parallel.shared_files`. Tasks owning a shared file are moved to a sequential sub-batch with an audit log entry. After the wave, a barrel reconciliation step consolidates all shared file modifications.

**Files changed**: `skills/spec-exec/SKILL.md`, `skills/spec-loop/SKILL.md`, `skills/spec-team/SKILL.md`

### Token Budget Auto-Calculation (US-13)

`/spec` now sets `state.json.execution.budget_cap` to `task_count * 50000` when `budget_cap` is null after the tasker phase. Manually set values are not overwritten. `/spec-status` shows whether the budget was auto-calculated or manually set.

**Files changed**: `skills/spec/SKILL.md`, `skills/spec-status/SKILL.md`, `templates/state.json`

---

## Agent Hardening (US-6, US-7, US-9, US-14, US-15)

### Anti-Deferral Rule in 4 Agents (US-7)

`spec-implementer`, `spec-tester`, `spec-debugger`, and `spec-acceptor` now have an `## Anti-Deferral Rule` section. The following phrases are prohibited in agent output unless accompanied by an explicit FAILURE report: `"deferred to future spec"`, `"TODO: implement later"`, `"stub for now"`, `"placeholder implementation"`.

**Files changed**: `agents/spec-implementer.md`, `agents/spec-tester.md`, `agents/spec-debugger.md`, `agents/spec-acceptor.md`

### Types-First Wave 0 Enforcement (US-6)

`spec-validator` now checks (Check 9) that specs with 5 or more tasks have at least one Wave 0 task whose description or `Files` field references types, schemas, interfaces, or contracts. Violation is an ERROR. `spec-tasker` now states this requirement explicitly as "required, not optional."

**Files changed**: `agents/spec-validator.md`, `agents/spec-tasker.md`

### Deprecated Field Sweep Enforcement (US-9)

Check 7 in `spec-validator` is upgraded from implicit to explicit ERROR: if a task has `Deprecates != "none"` and no sweep task exists whose `Dependencies` includes that task ID, an ERROR is reported. A second ERROR covers sweep tasks whose `Files` array doesn't cover all files containing the deprecated field.

**Files changed**: `agents/spec-validator.md`

### Fix Budget Estimation in spec-acceptor (US-14)

When the acceptor produces a NOT ACCEPTED report, it now calculates `estimated_fix_rounds` using four tiers (wiring-only = 1, ≤3 functional gaps = 2, 4–6 gaps = 3, 7+ gaps = 3 + ceil(gap_count/3)) and writes the value to the report for the orchestrator to store in `state.json.acceptance.estimated_fix_rounds`.

**Files changed**: `agents/spec-acceptor.md`

### Documenter Audit Mode (US-15)

`spec-documenter` now has an `## Audit Mode` section. When dispatched with audit-mode instructions (the dispatch message contains "audit" or "Do NOT generate documentation files"), it scans implementation files for undocumented exports and writes only to `evidence/doc-audit.md`. It does not write to `docs/`.

**Files changed**: `agents/spec-documenter.md`

---

## Quality Gates (US-8, US-12)

### Pre-Acceptance Full-Project Lint (US-8)

`/spec-accept` now runs the project lint command (`state.json.quality_gates.lint_cmd`) on the full codebase before delegating to the acceptor (Step 1.5). Output is written to `evidence/pre-acceptance-lint.txt`. The step is skipped if `lint_cmd` is null or not in `allowed_commands`. Lint failures are non-blocking.

**Files changed**: `skills/spec-accept/SKILL.md`

### Pre-Acceptance Security Scan (US-12)

`/spec-accept` now greps changed files (since `git_sha_start`) for common vulnerability patterns before acceptance (Step 1.6): hardcoded secrets, SQL injection indicators, XSS sinks, and insecure crypto. Matched lines are truncated to 200 characters; secret values are never written to evidence. Results go to `evidence/pre-acceptance-security-scan.txt`. Non-blocking.

**Files changed**: `skills/spec-accept/SKILL.md`

### Documentation Audit Before Acceptance (US-15)

`/spec-accept` now dispatches `spec-documenter` in audit mode (Step 1.7) before delegating to the acceptor. Results in `evidence/doc-audit.md` are passed as non-blocking context to the acceptor. Agent failure or timeout is logged and skipped.

**Files changed**: `skills/spec-accept/SKILL.md`, `agents/spec-documenter.md`

---

## State Schema Changes

`templates/state.json` gains two new top-level fields:

```json
"phase": null,
"acceptance": {
  "status": null,
  "estimated_fix_rounds": null
}
```

Field order: `version`, `spec_name`, `created_at`, `quick_mode`, **`phase`**, `integrity`, `tasks`, `waves`, `parallel`, `execution`, `reproducibility`, `quality_gates`, `lessons_applied`, `audit_log`, `security`, **`acceptance`**.
