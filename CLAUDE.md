# CLAUDE.md

This file provides guidance to Claude Code when working with the spec-engine plugin.

## Overview

spec-engine is a Claude Code plugin that guides feature development through a structured pipeline: Requirements (EARS notation) -> Design (architecture) -> Tasks (dependency DAG) -> Wave-based Execution -> Quality Gates -> Acceptance -> Docs -> Release -> Retrospective.

## Plugin Structure

```
.claude-plugin/plugin.json  - Plugin manifest
skills/                     - Slash command definitions (SKILL.md format)
agents/                     - Subagent definitions with model routing
scripts/                    - Thin CI/CD shell wrappers (~20 lines each)
templates/                  - Spec file scaffolding
references/                 - Reference docs for agents
```

## Commands

| Command | Purpose |
|---------|---------|
| `/spec <name>` | Create new spec (interactive requirements + human gate after design) |
| `/spec-brainstorm` | Explore a feature idea with optional domain experts |
| `/spec-refine` | Update spec with change impact analysis |
| `/spec-tasks` | Regenerate tasks from updated spec |
| `/spec-validate` | Validate completeness (all 5 EARS patterns, traceability) |
| `/spec-status` | Progress dashboard with cost tracking |
| `/spec-exec` | Execute one iteration with quality gates |
| `/spec-loop` | Wave-based loop with batching, cost controls, human checkpoints |
| `/spec-team` | 4-agent team execution (Implementer + Tester + Reviewer + Debugger) |
| `/spec-accept` | User acceptance testing with traceability matrix |
| `/spec-docs` | Generate documentation |
| `/spec-release` | Release notes, changelog, deployment checklist |
| `/spec-verify` | Post-deployment smoke tests |
| `/spec-retro` | Retrospective with lessons.json feedback loop |
| `/spec-import` | Import PRD/RFC/design doc into spec format |

## Model Routing

| Agent | Model | Phase | Rationale |
|-------|-------|-------|-----------|
| spec-planner | Opus | Requirements + Design | Deep reasoning for edge cases, security |
| spec-reviewer | Opus | Review | Code quality, security, architecture |
| spec-tasker | Sonnet | Task breakdown | Fast structured decomposition |
| spec-implementer | Sonnet | Implementation | Code generation |
| spec-tester | Sonnet | Testing | Verification |
| spec-debugger | Sonnet | Debugging | Fix issues |
| spec-acceptor | Sonnet | Acceptance | Traceability |
| spec-documenter | Sonnet | Documentation | Doc generation |
| spec-consultant | Sonnet | Brainstorming | Domain expertise |
| spec-validator | Sonnet | Validation | Checklist verification |

## Key Concepts

### EARS Notation
All acceptance criteria use Easy Approach to Requirements Syntax with 5 patterns:
- **Event-Driven**: WHEN [trigger] THE SYSTEM SHALL [behavior]
- **State-Driven**: WHILE [state] THE SYSTEM SHALL [behavior]
- **Conditional**: IF [condition] WHEN [trigger] THE SYSTEM SHALL [behavior]
- **Negative**: THE SYSTEM SHALL NOT [behavior]
- **Ubiquitous**: THE SYSTEM SHALL [behavior]
- **Feature-Specific**: WHERE [feature] WHEN [trigger] THE SYSTEM SHALL [behavior]

### state.json
Machine-readable execution state (~200 tokens). Replaces progress.md as the primary state mechanism. Tracks: task statuses, wave assignments, token usage, budget cap, quality gate results, integrity manifest, audit log.

### Wave-Based Execution
Tasks form a DAG. Topological sort assigns waves. Independent tasks in the same wave are batched (2-3 per iteration). This reduces iterations by 3-5x compared to one-task-per-iteration.

### Quality Gates
After every implementation iteration: Lint -> Type Check -> Regression Test -> Secret Scan. Gates are auto-detected from project config or configured in init.sh.

### Feedback Loop
`lessons.json` captures lessons from retrospectives and debugging sessions. Future `/spec` and `/spec-brainstorm` commands read these lessons to improve spec quality.

### Security Model
- No `--dangerously-skip-permissions` — each agent has only the tools it needs
- Spec integrity manifests (SHA256) verified before execution
- Secret-aware git staging
- Strict spec name validation
- Reviewer is strictly read-only (no Write, no Bash)

## Spec File Location

Specs are created in the target project at `.claude/specs/<feature-name>/`:
- `requirements.md` - User stories with EARS acceptance criteria
- `design.md` - Architecture with traceability annotations
- `tasks.md` - Implementation tasks with wave assignments
- `state.json` - Machine-readable execution state
- `init.sh` - Project-specific build/test/lint commands
- `lessons.json` - Shared across specs, feedback loop
- `evidence/` - Screenshots, test results, review reports
- `handoffs/` - Agent-to-agent communication (team mode)

## CI/CD Scripts

Thin shell scripts in `scripts/` for headless execution:
- `spec-exec.sh --spec-name <name>` - Single iteration
- `spec-loop.sh --spec-name <name>` - Full loop
- `spec-team.sh --spec-name <name>` - Team execution

These are ~20-line wrappers that validate input and delegate to `claude -p`.
