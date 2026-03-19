# spec-engine

A Claude Code plugin for spec-driven development. Guides features through a structured pipeline from requirements to release, with wave-based execution, quality gates, and continuous learning.

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
| `/spec-status` | Progress dashboard with cost tracking |
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

### Wave-Based Execution

Tasks form a dependency DAG. Topological sort assigns each task to a wave. Independent tasks in the same wave are batched together (2-3 per iteration), reducing total iterations by 3-5x.

```
Wave 0: [T-1]                    Setup (no dependencies)
Wave 1: [T-2, T-3]              Core (depend only on T-1, batched)
Wave 2: [T-4, T-5]              Integration (batched)
Wave 3: [T-6]                    E2E testing
Wave 4: [T-7]                    Polish
```

### Quality Gates

After every implementation iteration, four automated gates run:

1. **Lint** — catches style violations, unused imports
2. **Type Check** — catches type errors, hallucinated imports
3. **Regression Test** — runs the full test suite
4. **Secret Scan** — prevents accidental credential commits

Configure in `init.sh`:
```bash
lint_cmd="npm run lint"
typecheck_cmd="npx tsc --noEmit"
test_cmd="npm test"
```

### Agent Teams (`/spec-team`)

Four specialized agents with separation of concerns:

| Agent | Model | Role |
|-------|-------|------|
| Implementer | Sonnet | Writes code + persistent tests |
| Tester | Sonnet | Verifies end-to-end + error paths |
| Reviewer | Opus | Read-only security/quality review |
| Debugger | Sonnet | Fixes issues (max 2 retries) |

Agents communicate via lightweight handoff files (~200 tokens each) instead of full context duplication, reducing token usage by ~85% compared to naive approaches.

### State Management

`state.json` is the execution brain — a machine-readable file (~200 tokens) that tracks:

- Task statuses and wave assignments
- Token usage and budget cap
- Quality gate results
- Integrity manifest (SHA256 of spec files)
- Reproducibility data (model versions, git SHA)
- Audit log

### Security Model

- **No `--dangerously-skip-permissions`** — each agent has only the tools it needs
- **Spec integrity verification** — SHA256 manifests checked before execution
- **Secret-aware staging** — sensitive files detected and excluded from commits
- **Input validation** — strict regex on spec names, URL validation
- **Read-only reviewer** — the Opus reviewer cannot modify code, only read and report
- **Audit logging** — all execution events are logged

### Feedback Loop

`/spec-retro` analyzes completed specs and writes structured lessons to `lessons.json`. Future `/spec` and `/spec-brainstorm` commands read these lessons and apply them. The system learns from its mistakes across specs.

### Human Checkpoints

- **Mandatory gate after design** — user must approve architecture before tasks are generated
- **Periodic checkpoints** — every N tasks (configurable), execution pauses for human review
- **Budget cap** — execution pauses when token budget is exhausted
- **Stuck detection** — 3 failures on the same task triggers a pause for human input

## EARS Notation

All acceptance criteria use the five EARS patterns:

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

Thin shell scripts for headless execution:

```bash
./scripts/spec-loop.sh --spec-name user-authentication
./scripts/spec-team.sh --spec-name payment-processing --max-iterations 30
```

## Spec File Structure

```
.claude/specs/<feature-name>/
  requirements.md      # EARS requirements with risk register
  design.md            # Architecture with traceability
  tasks.md             # DAG with wave assignments
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

## Comparison with Previous Plugin

| Feature | spec-driven-plugin v3 | spec-engine v1 |
|---------|----------------------|----------------|
| Execution | Shell loop spawning fresh `claude` processes | Native Agent tool (no cold start) |
| Permissions | `--dangerously-skip-permissions` | Granular tool allowlists per agent |
| Task batching | 1 task per iteration | Wave batching (2-3 per iteration) |
| Quality gates | None | Lint + typecheck + regression + secret scan |
| State tracking | progress.md (~4000 tokens) | state.json (~200 tokens) |
| Human checkpoints | None after requirements | After design + every N tasks + budget cap |
| Learning | None | lessons.json feedback loop |
| Agent context | Full spec duplication | Handoff files (~200 tokens each) |
| Completion detection | `grep '<promise>COMPLETE</promise>'` | Structural parsing of state.json |
| Shell scripts | 250+ lines of business logic | ~20 lines delegating to skills |
| Traceability | Requirements -> Tasks | Requirements -> Design -> Tasks -> Code -> Tests |
| Error-path testing | Not required | Mandatory for every task |
| Review persistence | Ephemeral | Persisted to evidence/ directory |

## License

MIT
