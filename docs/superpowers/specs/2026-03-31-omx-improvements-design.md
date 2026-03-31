# OMX Comparison Improvements — Design Spec

**Date:** 2026-03-31
**Origin:** OMX (oh-my-codex) comparison analysis
**Scope:** 13 improvements across 5 layers

## Layer 1: Foundation (Contract Changes)

### 1.2 — Custom Quality Gates
- Add `gates` bash array to init.sh template: `gates=("lint:cmd" "typecheck:cmd" "test:cmd")`
- New `scripts/lib/gates.sh` with backward-compatible reader: detects old format (individual `lint_cmd` etc.), converts to gates array on read
- state.json `quality_gates` gets optional `gates[]` array; new format takes precedence over legacy fields
- All consumers call `get_gates()` from lib/gates.sh instead of reading fields directly

### 1.3 — Lifecycle Hooks
- Optional hooks in init.sh: `hook_on_wave_start`, `hook_on_task_complete`, `hook_on_spec_complete`
- New `scripts/lib/hooks.sh` with `run_hook <event> <args...>` — best-effort, non-blocking, stderr captured
- Callers: spec-exec, spec-loop, spec-team invoke at appropriate moments

### 1.13 — Notification Hooks
- Extension of lifecycle hooks — `templates/hooks/` with example scripts (slack.sh, discord.sh, webhook.sh)
- Users wire these into init.sh hook fields

## Layer 2: New Skills

### 2.1 — `/spec-quick`
- New skill: `skills/spec-quick/SKILL.md`
- Flow: parse description → create spec dir → minimal state.json (`quick_mode: true`, integrity hashes null) → auto-generate 1-3 tasks in tasks.md → auto-detect init.sh → run single spec-exec iteration
- No requirements.md, no design.md, no validation fingerprint
- Validator and dashboard detect `quick_mode` and adjust expectations

### 2.6 — Consensus Planning (`--consensus`)
- Modification to `/spec` skill only
- When flag present: planner drafts → consultant(Architect) critiques → consultant(Critic) finds gaps → planner revises
- Output: same requirements.md + design.md — downstream contracts unchanged

### 2.11 — `/spec-session`
- New skill: `skills/spec-session/SKILL.md`
- Interactive REPL: reads state.json, shows status, asks what to do next
- Delegates to existing skills (spec-exec, spec-validate, spec-refine) for mutations
- Read-only on state itself

## Layer 3: Execution Improvements

### 3.4 — Live Progress Stream
- New `scripts/lib/progress.sh` — writes to `.claude/specs/<name>/progress.log`
- Events: WAVE_START, TASK_START, TASK_COMPLETE, GATE_PASS, GATE_FAIL, WAVE_COMPLETE
- spec-loop and spec-team emit formatted lines between agent dispatches
- Format: `[HH:MM:SS] > Wave 2/4 | T-5 implementing (file.ts) | 3/8 tasks done`

### 3.5 — Task Decomposition on Failure
- After debugger fails 2x on a task: analyze and split into 2-3 smaller tasks
- New IDs: `T-{max+1}`, `T-{max+2}` (not sub-IDs — preserves regex parsers)
- Original task: `status: decomposed` (new enum value)
- New tasks: wave = original.wave + 1, inherit dependencies
- Recompute integrity hashes. Max 1 decomposition per original task.

### 3.9 — Interactive Escalation (Per-Wave Sequential/Parallel)
- Per-wave decision based on Files overlap and shared dependencies
- If any overlap detected in wave: run sequential for that wave
- `lib/worktree.sh` gets existence check (currently assumes one-time setup)

## Layer 4: Intelligence

### 4.7 — Lessons to Validation Rules
- `/spec-validate` reads lessons.json, derives WARNING-level rules
- Pattern-matched strings against requirements/design content
- WARNING only; `--strict-lessons` flag promotes to ERROR

### 4.8 — Codebase-Aware Templates
- `/spec` init.sh generation auto-detects project type from manifest files
- Supported: package.json (Node), pyproject.toml/setup.py (Python), Cargo.toml (Rust), go.mod (Go)
- Show detection result, allow override. Fallback: blank template.

## Layer 5: Dashboard & UX

### 5.10 — Cross-Spec Dependency Visualization
- `/spec-dashboard --deps` shows ASCII dependency graph
- Data source: existing `lib/deps.sh`
- Blocked specs highlighted

### 5.12 — Diff-Based `/spec-refine` Output
- After refine: show unified diff of changed spec files
- `git diff` on spec files before/after operation
- Presentation only, no contract changes

## Critical Contracts (Preserved)

- state.json version stays at 1; all new fields optional with defaults
- tasks.md regex: `T-{N}` IDs, Status enum (add `decomposed`), Wired values, Files lists unchanged
- init.sh: new fields optional, backward-compatible reader for old format
- Integrity hashes: recomputed on any spec file mutation
- Handoff files: format unchanged
- File ownership: parallel safety unchanged

## Implementation Order

**Wave A (no dependencies):** #1 spec-quick, #8 codebase-aware templates, #12 diff-based refine, #10 dashboard deps, #11 spec-session
**Wave B (foundation):** #2 custom gates + lib/gates.sh, #3 lifecycle hooks + lib/hooks.sh
**Wave C (depends on B):** #13 notification hook templates, #4 live progress (uses hooks.sh patterns), #7 lessons-to-rules
**Wave D (depends on execution):** #5 task decomposition, #6 consensus planning, #9 interactive escalation
