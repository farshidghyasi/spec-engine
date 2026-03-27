# spec-engine

A Claude Code plugin for spec-driven development. Guides features through a structured pipeline from requirements to release, with wave-based execution, quality gates, and continuous learning.

Inspired by [Kiro](https://kiro.dev)'s spec-driven development approach and built as a clean-room rewrite of the [spec-driven-plugin](https://github.com/habib0x0/spec-driven-plugin).

## What It Does

```
/spec <name>  -->  Requirements (EARS)  -->  Design (Architecture)  -->  Tasks (DAG)
                        |                        |                        |
                   Interactive              Human Gate               Wave Assignment
                   gathering               (approve design)          (topological sort)
                                                                         |
                                                                         v
/spec-loop    -->  Wave Execution  -->  Quality Gates  -->  Commit  -->  Repeat
                   (batch 2-3 tasks)    (lint, typecheck,
                                         regression, secrets)
                                                                         |
                                                                         v
/spec-accept  -->  UAT  -->  /spec-docs  -->  /spec-release  -->  /spec-retro
                                                                   (lessons.json)
```

## Installation

```bash
# Add as a Claude Code plugin
claude plugins add /path/to/spec-engine
```

## Quick Start

```bash
# 1. Create a spec (interactive)
/spec user-authentication

# 2. Validate before implementation
/spec-validate

# 3. Execute (choose one)
/spec-exec                    # Single iteration
/spec-loop                    # Full loop with wave batching
/spec-team                    # 4-agent team (Implementer + Tester + Reviewer + Debugger)

# 4. After implementation
/spec-accept                  # User acceptance testing
/spec-docs                    # Generate documentation
/spec-release --tag           # Release notes + git tag
/spec-retro                   # Retrospective + lessons learned
```

## Commands

| Command | Description |
|---------|-------------|
| `/spec <name>` | Create a new spec with interactive requirements gathering |
| `/spec-brainstorm [idea]` | Explore a feature idea with optional domain experts |
| `/spec-refine` | Update requirements/design with change impact analysis |
| `/spec-tasks` | Regenerate tasks from updated spec |
| `/spec-validate` | Validate completeness and consistency |
| `/spec-status` | Progress dashboard with cost and wiring health |
| `/spec-exec` | Execute one iteration with quality gates |
| `/spec-loop [--dry-run]` | Wave-based execution loop |
| `/spec-team` | 4-agent team execution |
| `/spec-accept` | User acceptance testing |
| `/spec-docs` | Generate documentation |
| `/spec-release` | Release notes and deployment checklist |
| `/spec-verify --url <url>` | Post-deployment smoke tests |
| `/spec-retro` | Retrospective with lessons feedback loop |
| `/spec-import <file>` | Import PRD/RFC into spec format |

## Architecture

### Model Routing

Each agent uses the model best suited to its task nature:

| Agent | Model | Why |
|-------|-------|-----|
| spec-planner | Opus | Deep reasoning for edge cases, security, architecture tradeoffs |
| spec-reviewer | Opus | Security analysis, subtle bugs, cross-task consistency |
| spec-acceptor | Opus | Formal sign-off requires deep judgment about requirement coverage |
| spec-consultant | Opus | Domain expertise benefits from deeper, more nuanced analysis |
| spec-implementer | Sonnet | Fast code generation, parallelizable with file boundaries |
| spec-tester | Sonnet | Test execution, cross-task regression detection |
| spec-tasker | Sonnet | Structured decomposition with file ownership assignment |
| spec-debugger | Sonnet | Targeted fixes, wiring repair |
| spec-documenter | Sonnet | Documentation generation |
| spec-validator | Sonnet | Checklist-based verification |

**Principle**: Opus for judgment and reasoning. Sonnet for structured execution.

### Wave-Based Execution with Parallel Agents

Tasks form a dependency DAG. Topological sort (Kahn's algorithm) assigns each task to a wave. Independent tasks in the same wave with non-overlapping file ownership run in **parallel** using isolated git worktrees, reducing both iterations (3-5x) and wall-clock time.

```
Wave 0: [T-1]                    Setup (sequential)
Wave 1: [T-2, T-3]              Core — PARALLEL (no file overlap)
         [T-4]                   Core — sequential (shares files with T-2)
Wave 2: [T-5, T-6]              Integration — PARALLEL (no file overlap)
Wave 3: [T-7]                    E2E testing (sequential)
Wave 4: [T-8]                    Polish (sequential)
```

Each task declares a `Files` field listing which files it will create or modify. The tasker ensures no two tasks in the same parallel group touch the same files.

### Quality Gates

After every implementation iteration, four automated gates run:

1. **Lint** — catches style violations, unused imports
2. **Type Check** — catches type errors, hallucinated imports
3. **Regression Test** — runs the full test suite
4. **Secret Scan** — prevents accidental credential commits

Gates are auto-detected from project config (package.json, pyproject.toml, Makefile, Cargo.toml, go.mod) or configured in `init.sh`:

```bash
lint_cmd="npm run lint"
typecheck_cmd="npx tsc --noEmit"
test_cmd="npm test"
```

Gates run in **diff mode** when pre-existing errors exist — comparing error counts against a baseline to fail only on NEW errors. All gate output is persisted to `evidence/tests/wave-N-{lint,typecheck,tests}.txt` so acceptance testing has evidence to verify against.

Failure triggers a tiered recovery: Debugger retry (2x) -> Task rollback -> Wave rollback -> Human escalation.

### Wiring Tracking

Every task tracks a `Wired` field alongside its status:

- **pending** — Code not yet connected to the application
- **yes** — Code is reachable from the app's entry point
- **n/a** — Infrastructure task with nothing to wire

This prevents the most common failure mode in AI-driven development: code that exists but isn't connected. The implementer must set it, the tester refuses to test without it, the reviewer rejects if pending, and the acceptor reports integration health. A task is not complete until `Status: completed` AND `Wired: yes` (or `n/a`).

**Wire into field**: Every component creation task declares a `Wire into:` field specifying the exact file where it must be imported (e.g., `Wire into: src/app.tsx (router)`). This target file is included in the task's `Files` array so the implementer owns the wiring change.

**Grep-based verification**: Wired status is never trusted from agent self-reports. After each wave, spec-loop greps the entire codebase for actual imports of each component's exports. Components with zero imports are downgraded to `wired: "pending"` regardless of what the agent claimed. spec-accept runs an independent wiring audit before acceptance testing. This verification is enforced with a `<HARD-GATE>` block that prevents any task from being marked complete without grep evidence — matching the enforcement patterns used in superpowers skills.

### Parallel Execution Safety

Running multiple AI agents in parallel introduces subtle failure modes. spec-engine addresses these with a layered safety model:

**File Ownership**: Each task declares which files it will create/modify. The tasker validates no overlap within a wave. Parallel agents are constrained to their assigned files only.

**Shared Files Registry**: Files that inherently need modification by multiple tasks (barrel/index files, `package.json`, lock files, config files, routers, test setup files, Dockerfiles) are classified as "shared" and excluded from parallel execution. They are modified in a sequential reconciliation step after parallel agents complete.

**Add-Only Rule**: Parallel agents may only ADD new code — they cannot refactor existing function signatures, rename variables, or restructure existing modules. This prevents the case where one agent changes an interface that another agent depends on.

**Signature Change Propagation**: When a task modifies an existing function's signature (parameters, return type, sync to async), the tasker includes a grep instruction and lists all known caller files. The implementer must grep for ALL callers before implementing — not just the ones listed — and flag any boundary violations via `SIGNATURE BREAK` handoff notes for sequential follow-up.

**Contract-First Design**: Shared types and interfaces are produced in Wave 0 before any parallel execution begins. All subsequent tasks import from these contracts, preventing type disagreements between parallel agents.

**Import Dependency Validation**: The tasker validates that if task B imports from files in task A's `Files` list, then B must depend on A. Tasks with cross-imports cannot be in the same parallel group.

**Atomic Merge**: Before merging any worktree, the system records the pre-merge HEAD SHA. If ANY merge fails, ALL merges in the group are reverted and the system falls back to sequential execution.

**Post-Merge Regeneration**: After merging parallel results, the system regenerates lock files, runs codegen, and cleans caches before running quality gates. This handles artifacts that are fundamentally incompatible with parallel execution (lockfiles, generated code, build caches).

**Cross-Task Consistency Review**: The Opus reviewer reviews the FULL wave's changes together (not per-task) to catch inconsistencies: interface mismatches, naming convention drift, error handling pattern divergence, and circular imports.

**Test Data Isolation**: Each task's tests use unique, namespaced test data (prefixed with task ID or UUIDs). No global mocks in shared setup files. Per-test setup/teardown only.

**No Formatters in Worktrees**: Code formatters run ONCE after all parallel merges are complete, not in individual worktrees. This prevents cosmetic changes from creating merge conflicts.

**Build vs. Extract Separation**: Complex components are split into implementation tasks ("make it work") and extraction tasks ("make it clean") in later waves. This prevents agents from inlining everything into monolithic files. A 500-line file size guard auto-creates extraction tasks if the tasker misses one.

### Agent Teams (`/spec-team`)

Four specialized agents with separation of concerns:

| Agent | Model | Role |
|-------|-------|------|
| Implementer | Sonnet | Writes code + persistent tests + wiring |
| Tester | Sonnet | Checks wiring first, then verifies end-to-end + error paths |
| Reviewer | Opus | Read-only security/quality/wiring review |
| Debugger | Sonnet | Fixes issues (max 2 retries, checks wiring first) |

Agents communicate via lightweight handoff files (~200 tokens each) instead of full context duplication, reducing token usage by ~85%.

### Post-Task Verification

After every task completes, spec-loop runs mandatory verification enforced with `<HARD-GATE>` blocks and red flags lists (superpowers-style enforcement patterns that prevent agent rationalization):

1. **Auto-commit** — the FIRST post-agent action, before any other check. Enforced with a `<HARD-GATE>` because agents routinely skip commits.
2. **File existence check** — stats every file in the task's `Files` array. Missing files mark the task as failed. Agent self-reports are never trusted.
3. **Max file size guard** — files exceeding 500 lines trigger auto-creation of extraction tasks in the next wave, preventing monolithic components.
4. **Audit log append** — every task start, completion, failure, wave transition, and gate result is logged. An empty audit log is treated as a bug.
5. **Evidence persistence** — gate output is written to `evidence/tests/` for downstream acceptance testing.

### State Management

`state.json` is the execution brain — a machine-readable file (~200 tokens) that tracks:

- Task statuses, wave assignments, and wiring status
- Token usage and budget cap
- Quality gate results
- Integrity manifest (SHA256 of spec files)
- Reproducibility data (model versions, git SHA)
- Audit log (mandatory — written at every transition, not batched)

Execution can be interrupted and resumed across sessions with zero re-orientation cost.

### Security Model

- **No `--dangerously-skip-permissions` by default** — each agent has only the tools it needs. Scripts accept `--yolo` to opt into skipping permissions for fully autonomous CI/CD execution.
- **Spec integrity verification** — SHA256 manifests checked before execution
- **Secret-aware staging** — sensitive files detected and excluded from commits
- **Input validation** — strict regex on spec names, URL validation
- **Read-only reviewer** — the Opus reviewer cannot modify code, only read and report
- **Audit logging** — all execution events are logged (enforced at every transition, not optional)

### Feedback Loop

`/spec-retro` analyzes completed specs and writes structured lessons to `lessons.json`. Future `/spec` and `/spec-brainstorm` commands read these lessons and apply them. The system learns from its mistakes across specs.

### Human Checkpoints

- **Mandatory gate after design** — user must approve architecture before tasks are generated
- **Periodic checkpoints** — every N tasks (configurable), execution pauses for human review
- **Budget cap** — execution pauses when token budget is exhausted
- **Stuck detection** — 3 failures on the same task triggers a pause for human input

## EARS Notation

All acceptance criteria use the six EARS patterns:

| Pattern | Syntax | When to Use |
|---------|--------|------------|
| Event-Driven | WHEN [trigger] THE SYSTEM SHALL [behavior] | Response to action |
| State-Driven | WHILE [state] THE SYSTEM SHALL [behavior] | During a state |
| Conditional | IF [condition] WHEN [trigger] THE SYSTEM SHALL | Conditional behavior |
| Negative | THE SYSTEM SHALL NOT [behavior] | Prohibited behavior |
| Ubiquitous | THE SYSTEM SHALL [behavior] | Always true |
| Feature-Specific | WHERE [feature] WHEN [trigger] THE SYSTEM SHALL | Limited context |

## Presets

Start from a pre-filled template:
- **REST API** — CRUD, validation, auth, errors, pagination
- **React Page** — Rendering, routing, state, API integration, responsive
- **CLI Tool** — Arg parsing, subcommands, output formatting, errors

## CI/CD Integration

Shell scripts for headless execution with built-in safety:

```bash
# Normal mode (prompts for permissions)
./scripts/spec-loop.sh --spec-name user-authentication
./scripts/spec-team.sh --spec-name payment-processing --max-iterations 30

# Fully autonomous (skips all permission prompts)
./scripts/spec-loop.sh --spec-name user-authentication --yolo
./scripts/spec-exec.sh --yolo
./scripts/spec-team.sh --spec-name payment-processing --yolo
```

Script features:
- **Auto-detect** — `--spec-name` is optional if only one spec exists
- **Worktree isolation** — runs in a `spec/<name>` branch (disable with `--no-worktree`)
- **`--yolo` mode** — passes `--dangerously-skip-permissions` for fully autonomous execution
- **Checkpoint recovery** — creates checkpoint commits before each iteration, rolls back on crash
- **Crash safety net** — detects if state.json wasn't updated and appends fallback audit entry
- **Duplicate prevention** — `spec-team.sh` prevents concurrent runs on the same spec
- **Cross-spec dependencies** — validates dependent specs are complete (with DFS cycle detection)
- **PR suggestion** — prints `gh pr create` command on completion

## Spec File Structure

```
.claude/specs/<feature-name>/
  requirements.md      # EARS requirements with risk register
  design.md            # Architecture with traceability
  tasks.md             # DAG with wave assignments and wiring status
  state.json           # Execution state (the brain)
  init.sh              # Project-specific commands
  lessons.json         # Shared feedback loop
  evidence/            # Screenshots, test results, reviews
  handoffs/            # Agent communication (team mode)
  docs/                # Generated documentation
  acceptance.md        # UAT report
  release.md           # Release notes
  retro.md             # Retrospective
```

## Inspiration and Lineage

This plugin is inspired by [Kiro](https://kiro.dev)'s spec-driven development functionality. Kiro introduced the concept of structured specification workflows that guide developers through requirements gathering, design, and task breakdown before implementation.

The direct predecessor is [spec-driven-plugin](https://github.com/habib0x0/spec-driven-plugin) (v3), which proved the concept works in Claude Code. spec-engine is a clean-room rewrite that keeps the core methodology while fundamentally changing the execution architecture.

### What spec-engine inherits from spec-driven-plugin

- **Three-phase workflow**: Requirements (EARS) -> Design -> Tasks
- **EARS notation**: Structured, testable acceptance criteria
- **Spec file organization**: Dedicated directories with separate documents per phase
- **Task traceability**: Linking tasks back to requirements
- **Agent team model**: Implementer + Tester + Reviewer + Debugger separation of concerns
- **Wiring rule**: Code must be connected to the application, not just written
- **Expert consultation**: Domain expert consultants during brainstorming
- **Cross-spec dependencies**: Specs can declare dependencies on other specs
- **Worktree isolation**: Git worktrees for safe parallel execution
- **Checkpoint recovery**: Pre-iteration commits with rollback on failure

### What spec-engine does differently

| Dimension | spec-driven-plugin v3 | spec-engine |
|-----------|----------------------|-------------|
| **Execution model** | Shell loop spawning fresh `claude -p` processes per iteration, each cold-starting with the full spec in the prompt | Native Agent tool — agents are subprocesses within the session, no cold start, no re-parsing |
| **Permissions** | `--dangerously-skip-permissions` on every invocation | Granular tool allowlists per agent (reviewer gets Read/Glob/Grep only, implementer gets Write/Edit/Bash, etc.) |
| **Task batching** | One task per iteration (`"Pick ONE task"`) | Wave-based DAG batching — 2-3 independent tasks per iteration, reducing total iterations 3-5x |
| **State tracking** | `progress.md` — append-only markdown log (~4000+ tokens), parsed with awk | `state.json` — machine-readable (~200 tokens), structurally parsed, resumable across sessions |
| **Completion detection** | `grep '<promise>COMPLETE</promise>'` in stdout | Structural check: all tasks in state.json have `status: completed` and `wired: yes\|n/a` |
| **Quality gates** | None — relies on Claude to self-test | Automated lint + type check + regression test + secret scan after every iteration, with evidence persistence and file existence verification |
| **Agent context (team mode)** | Full spec dumped into every agent's prompt (~6000 tokens each) | Handoff files (~200 tokens each) — ~85% token reduction |
| **Wiring enforcement** | `Wired: yes/no` field, manually checked by tester | `Wire into:` target declared per task, grep-verified after each wave (not self-reported), acceptor runs independent wiring audit |
| **Human checkpoints** | None after the requirements phase | Mandatory design gate + periodic task checkpoints + budget cap + stuck detection |
| **Feedback loop** | None — each spec starts from scratch | `lessons.json` written by `/spec-retro`, read by `/spec` and `/spec-brainstorm` |
| **Error recovery** | Checkpoint commits + rollback | 4-tier: debugger retry (2x) -> task rollback -> wave rollback -> human escalation |
| **Traceability** | Requirements -> Tasks | Full chain: Requirements -> Design (`Covers: US-X`) -> Tasks (`Covers: US-X`) -> Code -> Tests -> Acceptance |
| **Error-path testing** | Not required | Mandatory — every task must have at least one error-path acceptance criterion |
| **Review persistence** | Ephemeral (in conversation) | Persisted to `evidence/reviews/` with human-review flags for sensitive areas |
| **Crash recovery** | Checkpoint + progress.md fallback logging | Checkpoint + state.json update detection + fallback audit log entry |
| **Shell scripts** | 250+ lines of business logic (prompt building, awk parsing, worktree management) | Thin wrappers (~80 lines) with shared `lib/` helpers — business logic lives in skill definitions |
| **Cost controls** | `--max-iterations` only | Token budget cap + dry-run cost estimates + per-task token tracking in state.json |
| **Spec integrity** | None — spec files can change mid-execution without detection | SHA256 manifests computed after task generation, verified before every execution |
| **Inferred requirements** | Not tracked | AI-inferred requirements tagged with `[inferred]` so users can distinguish what they asked for vs what was added |
| **Parallel execution** | Sequential (one task per iteration) | Parallel agents with file ownership, shared files registry, atomic merge, and cross-task consistency review |
| **Model routing** | Opus for planner + reviewer, Sonnet for the rest | Opus for all judgment tasks (planner, reviewer, acceptor, consultant), Sonnet for all execution tasks |

### Why the rewrite?

The spec-driven-plugin proved that structured spec workflows dramatically improve AI-driven development quality. But its shell-loop architecture hit fundamental limits:

1. **Cold start overhead** — every iteration spawns a fresh `claude -p`, re-reads the full spec, and loses all prior context
2. **Permission model** — `--dangerously-skip-permissions` is a binary choice that gives every agent every tool
3. **No quality enforcement** — without automated gates, tasks get marked "complete" without real verification
4. **Linear execution** — one task per iteration means a 15-task spec takes 15+ iterations even when tasks are independent

spec-engine addresses all four by leveraging Claude Code's native Agent tool, per-agent tool restrictions, automated quality gates, and wave-based batching. Critically, every verification step is **enforced** with `<HARD-GATE>` blocks, rationalization prevention tables, and red flags lists — the same enforcement patterns used in superpowers skills. Agents cannot skip auto-commit, wiring verification, or file existence checks because the enforcement is structural (grep evidence required), not instructional (hoping agents follow directions).

## Contributors

- [farshidghyasi](https://github.com/farshidghyasi) — Author
- [habib0x](https://github.com/habib0x0) — Orignal spec-driven-plugin Author

## License

MIT
