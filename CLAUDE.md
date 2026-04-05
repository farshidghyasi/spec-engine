# CLAUDE.md

This file provides guidance to Claude Code when working with the spec-engine plugin.

## Overview

spec-engine is a Claude Code plugin that guides feature development through a structured pipeline: Requirements (EARS notation) -> Design (architecture) -> Tasks (dependency DAG) -> Wave-based Execution -> Quality Gates -> Acceptance -> Docs -> Release -> Retrospective.

## Plugin Structure

```
.claude-plugin/plugin.json  - Plugin manifest
skills/                     - Slash command definitions (SKILL.md format)
agents/                     - Subagent definitions with model routing
scripts/                    - CI/CD shell scripts with worktree + checkpoint support
scripts/lib/                - Shared shell libraries (worktree, checkpoint, deps)
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
| `/spec-status` | Progress dashboard with cost tracking and wiring health |
| `/spec-dashboard` | Portfolio view of all specs with verified phase completion |
| `/spec-exec` | Execute one iteration with quality gates |
| `/spec-loop` | Wave-based loop with batching, cost controls, human checkpoints |
| `/spec-team` | 5-agent team execution (Implementer + Tester + Reviewer + Security Reviewer + Debugger) |
| `/spec-accept` | User acceptance testing with traceability matrix |
| `/spec-security-audit` | 15-phase CSO security audit (daily or comprehensive mode) |
| `/spec-docs` | Generate documentation |
| `/spec-release` | Release notes, changelog, deployment checklist (security gate) |
| `/spec-verify` | Post-deployment smoke tests |
| `/spec-retro` | Retrospective with lessons.json feedback loop |
| `/spec-import` | Import PRD/RFC/design doc into spec format |

## Model Routing

Each agent uses the model best suited to its task nature:

| Agent | Model | Phase | Rationale |
|-------|-------|-------|-----------|
| spec-planner | Opus | Requirements + Design | Deep reasoning for edge cases, security, architecture tradeoffs |
| spec-reviewer | Opus | Review | Security analysis, subtle bugs, cross-task consistency checking |
| spec-security-reviewer | Opus | Review | Read-only security-focused code review, parallel with spec-reviewer |
| spec-threat-modeler | Opus | Planning | STRIDE analysis requires deep reasoning about attack vectors |
| spec-security-auditor | Opus | Audit | 15-phase CSO audit requires judgment about vulnerability patterns |
| spec-acceptor | Opus | Acceptance | Formal sign-off requires deep judgment about requirement coverage |
| spec-consultant | Opus | Brainstorming | Domain expertise benefits from deeper reasoning and nuanced analysis |
| spec-tasker | Sonnet | Task breakdown | Fast, structured decomposition with file ownership assignment |
| spec-implementer | Sonnet | Implementation | Code generation, parallelizable with file boundaries |
| spec-tester | Sonnet | Testing | Test execution, cross-task regression detection |
| spec-debugger | Sonnet | Debugging | Targeted fixes, wiring repair |
| spec-documenter | Sonnet | Documentation | Doc generation from spec and code |
| spec-validator | Sonnet | Validation | Checklist-based verification |

**Principle**: Opus for judgment and reasoning (planning, reviewing, security analysis, accepting, consulting). Sonnet for structured execution (implementing, testing, debugging, documenting).

## Key Concepts

### EARS Notation
All acceptance criteria use Easy Approach to Requirements Syntax with 6 patterns:
- **Event-Driven**: WHEN [trigger] THE SYSTEM SHALL [behavior]
- **State-Driven**: WHILE [state] THE SYSTEM SHALL [behavior]
- **Conditional**: IF [condition] WHEN [trigger] THE SYSTEM SHALL [behavior]
- **Negative**: THE SYSTEM SHALL NOT [behavior]
- **Ubiquitous**: THE SYSTEM SHALL [behavior]
- **Feature-Specific**: WHERE [feature] WHEN [trigger] THE SYSTEM SHALL [behavior]

### state.json
Machine-readable execution state (~200 tokens). Tracks: task statuses, wave assignments, wiring status, token usage, budget cap, quality gate results, security state (posture score, threat model status, findings), integrity manifest, audit log.

### Wired Tracking
Every task tracks a `Wired` field (pending/yes/n/a) alongside its Status. This prevents the #1 failure mode: code that exists but isn't connected to the application. A task is only truly complete when Status=completed AND Wired=yes (or n/a for infra tasks). The tester refuses to test unwired code, the reviewer rejects it, and the acceptor flags it.

### Wave-Based Execution with Parallel Agents
Tasks form a DAG. Topological sort assigns waves. Independent tasks in the same wave with non-overlapping file ownership are executed in parallel using isolated git worktrees. This reduces both iterations (3-5x) and wall-clock time.

### Parallel Safety Model
Each task declares a `Files` field listing which files it will create/modify. The tasker ensures no two tasks in the same wave share files. During execution:
- Parallel implementers run in `isolation: "worktree"` (separate repo copies)
- Each implementer is constrained to its assigned files
- Changes merge back sequentially with quality gates
- The Opus reviewer reviews the full wave's changes together to catch cross-task inconsistencies
- The tester runs the full suite after parallel merges to detect cross-task regressions

### Quality Gates
After every implementation iteration: Lint -> Type Check -> Regression Test -> Secret Scan -> Integration Smoke Test (post-wave). Gates are auto-detected from project config or configured in init.sh. Gates run in **diff mode** when pre-existing errors exist — comparing error counts against a baseline to fail only on NEW errors.

### Codebase Verification
The planner and tasker both perform mandatory codebase verification before writing spec files. They grep for every referenced interface, read actual type definitions, verify import paths exist, and use exact field names from source files — never from memory or paraphrases. The `/spec` orchestrator builds a Verified Interface Registry from the actual codebase and passes it to the tasker. The tasker runs a 6-check self-validation pass after writing tasks.md. The validator includes a "Codebase Accuracy Check" that catches any remaining mismatches and auto-fixes ERROR-level issues by default (use `--no-fix` to skip).

### Drift Detection
Specs track which codebase files they reference (`state.json.reproducibility.referenced_codebase_files`). Before execution, `/spec-exec`, `/spec-loop`, and `/spec-validate` compare the current codebase against `git_sha_start` to detect if another spec (or manual edit) changed files this spec depends on. When drift is detected, the spec is auto-fixed to match the current codebase — the codebase is always the source of truth, never the reverse.

### Import Manifest
Before dispatching each wave, the orchestrator scans completed task files and builds an import manifest of exact export names, function signatures, and file paths. This is included in every agent's prompt to prevent agents from guessing import names.

### Post-Agent Verification
After each parallel agent completes: (1) auto-commit its work in the worktree, (2) enforce shared file boundaries by reverting unauthorized modifications, (3) cross-check imports between parallel agents before merging.

### Feedback Loop
`lessons.json` captures lessons from retrospectives and debugging sessions. Future `/spec` and `/spec-brainstorm` commands read these lessons to improve spec quality.

### Security Model
- No `--dangerously-skip-permissions` — each agent has only the tools it needs
- Spec integrity manifests (SHA256) verified before execution
- Secret-aware git staging
- Strict spec name validation
- Reviewer is strictly read-only (no Write, no Bash)
- Security reviewer is read-only (Read, Glob, Grep only — no Write, Edit, or Bash)
- Threat modeler Write is HARD-GATE constrained to 3 spec-directory paths only
- Security auditor Bash is HARD-GATE constrained to read-only audit commands
- Security findings never store credential values (file paths and line numbers only)
- Security agent failures degrade gracefully (log + continue, never halt pipeline)
- CRITICAL findings block `/spec-release` unless `--force` is used with audit trail

## Spec File Location

Specs are created in the target project at `.claude/specs/<feature-name>/`:
- `requirements.md` - User stories with EARS acceptance criteria
- `design.md` - Architecture with traceability annotations
- `tasks.md` - Implementation tasks with wave assignments and wiring status
- `state.json` - Machine-readable execution state (includes security state)
- `init.sh` - Project-specific build/test/lint commands
- `lessons.json` - Shared across specs, feedback loop
- `evidence/` - Screenshots, test results, review reports, security evidence
- `evidence/threat-model.md` - STRIDE analysis (auto-generated by threat modeler)
- `evidence/security-review-wave-N.md` - Per-wave security findings
- `evidence/security-audit.json` - 15-phase audit report
- `handoffs/` - Agent-to-agent communication (team mode)
- `handoffs/security-T-X-critical.md` - CRITICAL finding fix instructions

## CI/CD Scripts

Shell scripts in `scripts/` for headless execution:
- `spec-exec.sh [--spec-name <name>] [--no-worktree]` - Single iteration
- `spec-loop.sh [--spec-name <name>] [--max-iterations N] [--no-worktree]` - Full loop
- `spec-team.sh [--spec-name <name>] [--max-iterations N] [--no-worktree]` - Team execution

All execution scripts run autonomously by default (no human interaction). Use `--no-skip-permissions` to re-enable Claude Code permission prompts if needed.

Features:
- **Auto-detect**: If only one spec exists, `--spec-name` is optional
- **Worktree isolation**: Runs in a `spec/<name>` branch via git worktree (disable with `--no-worktree`)
- **Checkpoint recovery**: Creates checkpoint commits before each iteration, rolls back on crash
- **Crash safety net**: Detects if state.json wasn't updated and appends a fallback audit log entry
- **Duplicate prevention**: spec-team.sh prevents concurrent runs on the same project+spec
- **Cross-spec dependencies**: Validates dependent specs are complete before execution (with DFS cycle detection)
- **PR suggestion**: Prints `gh pr create` command on completion
