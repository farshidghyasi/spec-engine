# CLAUDE.md

Guidance for Claude Code when working on the spec-engine plugin itself.

## Git Identity

Always use this email for all git commits: `farshid.ghyasi@gmail.com`. No other email should be used.

## Overview

spec-engine is a Claude Code plugin for spec-driven development: Requirements (EARS) -> Design ->
Tasks (dependency DAG) -> wave-based execution -> quality gates -> acceptance -> docs -> release -> retro.

## Layout

```
.claude-plugin/plugin.json   Manifest (single source of the version; marketplace.json must match)
skills/*/SKILL.md            Slash commands. Execution skills are thin; the algorithm is in references/execution-core.md
agents/*.md                  Subagents with model aliases (opus / sonnet)
references/                  execution-core.md, ears-notation.md, design-patterns.md, task-breakdown.md, quality-gates.md
scripts/spec-state.py        Deterministic state CLI (stdlib python3). Everything skills do with state goes through it
scripts/spec-loop.sh         Headless loop: one fresh `claude -p` per wave, real token accounting, crash rollback
scripts/spec-exec.sh         = spec-loop.sh --max-iterations 1 ;  scripts/spec-team.sh = spec-loop.sh --team
scripts/hooks/               Plugin hook scripts (commit-gate, stop-gate, session-start) wired in hooks/hooks.json
workflows/wave.js, verify.js Workflow-tool scripts: implementer fan-out per wave; testers + reviewer
evals/                       `claude plugin eval` smoke cases (prompt.md + graders/*.md)
templates/                   Spec scaffolding filled by `spec-state init`
tests/                       unittest suite for spec-state + check_plugin.py consistency checks (run in CI)
```

## Working on this repo

- Run `python3 -m unittest discover -s tests` and `python3 tests/check_plugin.py` before finishing.
  CI also runs shellcheck on every shell script.
- Anything deterministic (hashes, waves, JSON edits, grep checks, gate runs) belongs in
  `scripts/spec-state.py`, with a test. Skills and agents only orchestrate and judge.
- Do not add prose "enforcement" (rationalization tables, HARD-GATE blocks) for things a hook or the
  CLI can enforce. Hooks: `hooks/hooks.json`.
- Agents use model aliases, never dated model IDs, and Sonnet execution agents carry `maxTurns`.
  Agents that are read-only stay read-only; the orchestrating skill persists their output.
- Agent fan-out goes through the Workflow tool (`workflows/*.js`, plain JS, no filesystem or Date APIs,
  schema-validated returns). Skills keep an Agent-tool fallback. Skills with side effects set
  `disable-model-invocation: true`.
- Validate with `claude plugin validate .`; `claude plugin eval .` runs `evals/`.
- `tasks.md` is the human-readable source of task structure; `state.json` is derived from it by
  `spec-state sync-tasks` and holds runtime fields (status, wired, failures, tokens). Agents never edit
  Status/Wired by hand.

## Commands

| Command | Purpose |
|---------|---------|
| `/spec <name>` | Create a spec (interactive requirements, threat model, human gate after design, tasks) |
| `/spec-quick <desc>` | Tasks-only spec for 1-3 file changes, executed immediately |
| `/spec-brainstorm` | Explore an idea with optional domain-expert consultants |
| `/spec-import <file>` | Convert a PRD/RFC into a spec |
| `/spec-refine`, `/spec-tasks` | Change a spec with impact analysis; regenerate tasks |
| `/spec-validate` | EARS, traceability, codebase accuracy; auto-fixes spec files |
| `/spec-exec` / `/spec-loop` / `/spec-team` | One wave / all waves / all waves with a tester per task |
| `/spec-status`, `/spec-dashboard`, `/spec-session` | Progress views (CLI-rendered) |
| `/spec-accept`, `/spec-security-audit` | Acceptance with wiring audit; 15-phase audit |
| `/spec-ship` | Docs, release (CRITICAL findings block), optional smoke test, retro in one run |
| `/spec-docs`, `/spec-release`, `/spec-verify`, `/spec-retro` | The same steps individually |

## Model routing

Opus for judgment: spec-planner, spec-reviewer, spec-threat-modeler, spec-security-auditor,
spec-acceptor, spec-consultant. Sonnet for structured execution: spec-tasker, spec-implementer,
spec-tester, spec-debugger, spec-documenter, spec-validator.

## Key concepts

- **EARS**: WHEN / WHILE / IF-WHEN / SHALL NOT / SHALL / WHERE-WHEN patterns; every WHEN has an error-path twin.
- **Wired**: a task is done only when `status=completed` and `wired=yes|n/a`. `spec-state verify-wired`
  decides it by grepping for usages of the task's exports outside the defining file and tests.
- **Waves**: Kahn topological sort of the task DAG; same-wave tasks with disjoint `Files` run as
  parallel implementers in worktrees; `parallel.shared_files` always run sequentially.
- **Gates**: `spec-state run-gates` in diff mode against a recorded baseline, plus a secret scan;
  output persisted to `evidence/tests/`.
- **Phases**: spec -> validated -> executed -> accepted/audited -> documented -> released -> verified -> retro,
  checked with `spec-state phase-gate`. Cross-spec `## Depends On` requires the dependency at `executed`.
- **Drift**: `spec-state drift` diffs referenced codebase files since `git_sha_start`; the codebase is the
  source of truth and spec files are fixed to match.
- **Hooks**: the Stop hook blocks ending a session while a batch has unfinished tasks; the PreToolUse
  hook denies `git commit` with unstaged state.json and auto-allows spec-state calls; SessionStart
  injects the dashboard when specs exist.
- **Budget**: `budget_cap` (tasks x 50000 by default) is enforced by `scripts/spec-loop.sh` using real
  usage from `claude -p --output-format json`. In-session loops only log it.
- **Lessons**: `/spec-retro` appends to `.claude/specs/lessons.json`; `/spec`, `/spec-brainstorm` and
  `/spec-validate` read it.

## Security model

- Reviewer, consultant, validator: Read/Glob/Grep only. Security auditor: plus Bash restricted to audit
  commands. Threat modeler: Write restricted to `evidence/threat-model.md` and `requirements.md`.
- Findings never store credential values; secret scan output is path:line:pattern.
- CRITICAL findings block `/spec-release` unless `--force` (logged as `security_override`).
- Headless scripts run with `--dangerously-skip-permissions` by default (`--no-skip-permissions` to opt out)
  inside a `spec/<name>` worktree and require a clean tree so crash rollback cannot lose work.
