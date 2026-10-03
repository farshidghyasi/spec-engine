# spec-engine

A Claude Code plugin for spec-driven development. Features go through a structured pipeline from
requirements to release, with wave-based parallel execution, deterministic quality gates, grep-verified
wiring, and a feedback loop of lessons.

Inspired by [Kiro](https://kiro.dev)'s spec workflow and descended from
[spec-driven-plugin](https://github.com/habib0x0/spec-driven-plugin).

```
/spec <name>   Requirements (EARS) -> Design -> Threat model -> Human gate -> Tasks (wave DAG)
/spec-validate EARS, traceability, codebase accuracy (auto-fix)
/spec-loop     per wave: parallel implementers -> gates (diff mode) -> wiring grep -> Opus review -> commit
/spec-accept   /spec-security-audit  /spec-ship (docs, release, smoke test, retro)
```

## Install

```bash
claude plugin install spec-engine@<marketplace>     # from a marketplace that lists this repo
# or, for local development, add this directory as a marketplace in `/plugin` and install from it
```

Requires `python3` (3.9+, stdlib only) and `git`.

## Quick start

```
/spec user-authentication     # interactive; approve the design at the human gate
/spec-validate
/spec-loop                    # or /spec-exec for one wave, /spec-team for a tester per task
/spec-security-audit
/spec-accept
/spec-ship --tag             # docs + release notes + tag + retro in one go (add --url to smoke-test a deploy)
```

Small change? `/spec-quick "fix the login button alignment on mobile"` creates a tasks-only spec and
runs it with the same gates and wiring verification.

## Commands

| Command | Description |
|---------|-------------|
| `/spec <name> [--consensus]` | Create a spec: interactive requirements, STRIDE threat model, mandatory design gate, task DAG |
| `/spec-quick <description>` | Tasks-only spec for 1-3 files, executed immediately |
| `/spec-brainstorm [idea]` | Explore an idea; optional domain-expert consultants (Opus) |
| `/spec-import <file>` | Convert a PRD/RFC/design doc into spec format |
| `/spec-refine` / `/spec-tasks` | Change requirements with impact analysis / regenerate tasks |
| `/spec-validate [--no-fix]` | Validate; auto-fix spec files against the real codebase |
| `/spec-exec` | Execute one wave batch |
| `/spec-loop [--dry-run] [--max-iterations N] [--no-parallel]` | Execute all waves autonomously |
| `/spec-team` | `/spec-loop` plus an independent tester per task |
| `/spec-status` / `/spec-dashboard [--deep] [--deps]` / `/spec-session` | Progress for one spec / all specs / guided mode |
| `/spec-accept` | Acceptance with traceability matrix and wiring audit |
| `/spec-security-audit [--comprehensive]` | 15-phase security audit, posture score |
| `/spec-ship [--tag] [--release] [--url] [--force]` | Docs, release (blocked by CRITICAL findings), optional smoke test, retrospective, in one run |
| `/spec-docs` / `/spec-release` / `/spec-verify --url` / `/spec-retro` | The same four steps individually |

## How it works

### The state CLI

`scripts/spec-state.py` does every deterministic step so it is done the same way every time:
spec scaffolding, SHA256 integrity, Kahn wave assignment from `tasks.md`, parallel-group planning by
file ownership, structural validation, drift detection, phase and dependency gates, quality gates in
diff mode with evidence files, secret scan, grep-based wiring verification, import manifests, token
accounting, lifecycle hooks, status and dashboard rendering. Skills and agents only orchestrate and
judge. `tasks.md` is the human-readable source of structure; `state.json` is derived from it and holds
runtime fields.

```
python3 scripts/spec-state.py -h
```

### Execution core

`/spec-exec`, `/spec-loop`, `/spec-team` and `/spec-quick` all follow
[`references/execution-core.md`](references/execution-core.md):

1. Preflight: phase gate, cross-spec dependencies, drift, structure, integrity, gate detection.
2. `batch`: pending tasks of the current wave split into parallel groups (disjoint `Files`,
   `shared_files` always sequential, failed tasks sequential).
3. Implementers (Sonnet) run in isolated worktrees with only their task, their file boundaries and the
   import manifest of completed work. After each one: commit, shared-file revert, `check-files`.
4. `run-gates` (lint, typecheck, test, secret scan) in diff mode; `verify-wired --apply`; integration
   smoke test if configured. Failures go to the debugger (2 attempts) then task or wave rollback.
5. One Opus review per wave covering quality, architecture, cross-task consistency and security.
   CRITICAL findings dispatch the debugger. In team mode a tester verifies each task first.
6. Commit with state.json in the same commit; stuck tasks (3 failures) are decomposed once, then skipped.

### Agent fan-out through the Workflow tool

Implementers for a wave are launched by `workflows/wave.js` through Claude Code's Workflow tool:
deterministic JavaScript decides the fan-out (parallel within a file-disjoint group, groups in order,
worktree isolation only when two or more tasks run together) and every implementer returns a
schema-validated result (files changed, commit, branch, test output, wiring evidence) instead of free
text. `workflows/verify.js` runs the per-task testers (team mode) and the single Opus reviewer the
same way. The skills fall back to the Agent tool when Workflow is unavailable in a session.

### Enforced, not requested

Three plugin hooks (`hooks/hooks.json`) make the rules structural:

- **Stop hook**: a session cannot end while a spec is executing with tasks in progress or completed
  but unwired.
- **PreToolUse hook**: `git commit` is denied while `state.json` has unstaged changes, and spec-state
  calls are auto-allowed so state writes never prompt.
- **SessionStart hook**: when the project has specs, the dashboard is placed in context so every
  session starts knowing what is in flight.

Execution agents carry `maxTurns` caps, side-effecting skills are `disable-model-invocation: true`
(only you can start them), and read-only agents stay read-only with the orchestrator persisting output.

Wiring and file existence are decided by grep and stat, never by an agent's self-report.

### Security pipeline

- The planner generates `[security]` EARS criteria per detected category (API, storage, integrations,
  user input) plus a baseline "no internal error details" criterion.
- The threat modeler runs STRIDE on the design and injects up to 10 `[threat-model]` criteria, shown at
  the human gate for approve/reject.
- The per-wave Opus review greps changed files for injection, auth gaps, secrets, unsafe eval, SSRF and
  unvetted dependencies; CRITICAL requires two confirming signals.
- `/spec-security-audit` runs a 15-phase audit scoped to `git_sha_start..HEAD`; posture score
  `100 - 20*CRITICAL - 5*HIGH - 2*MEDIUM`. `/spec-release` blocks on CRITICAL unless `--force` (logged).
- Security agents never record credential values. Reviewer and auditor cannot modify code.

### Model routing

| Agent | Model | Role |
|-------|-------|------|
| spec-planner, spec-threat-modeler, spec-consultant | Opus | Requirements, design, STRIDE, expert review |
| spec-reviewer, spec-security-auditor, spec-acceptor | Opus | Per-wave review, 15-phase audit, acceptance |
| spec-tasker, spec-implementer, spec-tester, spec-debugger, spec-documenter, spec-validator | Sonnet | Structured execution |

### Feedback loop

`/spec-retro` writes lessons to `.claude/specs/lessons.json`. `/spec` and `/spec-brainstorm` surface
them; `/spec-validate` turns pattern lessons into warnings and runs `enforceable` checks.

## Headless / CI

```bash
scripts/spec-loop.sh --spec-name user-authentication [--max-iterations 30] [--team]
scripts/spec-exec.sh                      # one iteration; spec auto-detected when only one exists
```

Each iteration is a fresh `claude -p` session running one wave, so context never bloats and a crash
loses at most one wave. The script records real token usage from the JSON result, enforces
`budget_cap`, rolls back to the pre-iteration commit on a non-zero exit, stops after two crashes or two
iterations without progress, and refuses to start on a dirty tree (so rollback cannot lose your work).
Runs in a `spec/<name>` worktree by default (`--no-worktree` to opt out) and prints a `gh pr create`
suggestion on completion. Permission prompts are skipped by default (`--no-skip-permissions` to re-enable).

## Spec files

```
.claude/specs/<name>/
  requirements.md   EARS user stories, risk register, optional "## Depends On"
  design.md         Architecture with Covers: US-X traceability
  tasks.md          Task DAG: Status, Wave, Wired, Wire into, Dependencies, Covers, Files
  state.json        Derived runtime state: tasks, waves, phase, gates, security, audit_log
  init.sh           gates=(...), budget_cap, lifecycle hooks
  evidence/         tests/, reviews/wave-N.md, wiring-wave-N.md, threat-model.md, security-audit.json
  handoffs/         Agent-to-agent notes (team mode, CRITICAL findings)
  acceptance.md, release.md, verification.md, retro.md, docs/
.claude/specs/lessons.json   Shared across specs
```

## Development

```bash
python3 -m unittest discover -s tests      # spec-state behaviour + spec-loop.sh with a fake claude
python3 tests/check_plugin.py              # versions, agent/skill/CLI/workflow references, hooks, evals
shellcheck scripts/*.sh scripts/hooks/*.sh scripts/lib/*.sh
claude plugin validate .                   # manifest
claude plugin eval . --trust-plugin        # evals/*: smoke cases graded by an LLM judge (costs tokens)
```

## Lineage

spec-engine keeps spec-driven-plugin's methodology (EARS, three-phase workflow, wiring rule, agent
team, cross-spec dependencies, worktree isolation) and changes the execution architecture: wave-based
batching instead of one task per iteration, a deterministic state CLI instead of prompt-driven
bookkeeping, hooks instead of instructions for the non-negotiable gates, machine-readable
`state.json` instead of a markdown progress log, per-agent tool allowlists, automated quality gates in
diff mode, and persisted evidence for acceptance.

## Contributors

- [farshidghyasi](https://github.com/farshidghyasi) — Author
- [habib0x](https://github.com/habib0x0) — Original spec-driven-plugin author

## License

MIT
