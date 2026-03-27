# spec-dashboard Design

## Overview

A new `/spec-dashboard` command that provides a portfolio-level view of all specs in the current project. Unlike `/spec-status` (deep dive into one spec), this gives a quick, verified overview of every spec's lifecycle phase completion.

## Command Interface

```
/spec-dashboard [--deep]
```

- **Default mode**: Fast file-based verification, renders a table of all specs with phase completion
- **`--deep` mode**: Additionally dispatches `spec-validator` per spec for semantic validation

## Output Format

### Default Table

```
== Spec Dashboard: my-project ==

Spec              | Req | Design | Tasks | Exec    | Accepted | Docs | Retro | Released
------------------|-----|--------|-------|---------|----------|------|-------|----------
auth-system       |  Y  |   Y    |  Y    | 10/10   |    Y     |  Y   |  Y    |   Y
payment-flow      |  Y  |   Y    |  Y    |  6/12   |    -     |  -   |  -    |   -
notification-svc  |  Y  |   Y    |  -    |  -      |    -     |  -   |  -    |   -
search-feature    |  Y  |   -    |  -    |  -      |    -     |  -   |  -    |   -

Legend: Y = verified  - = not done  X = failed (--deep only)

Summary: 4 specs | 1 released | 1 in progress | 2 in planning
```

- **Exec** column shows `completed/total` task counts (not just Y/-)
- Specs ordered by progress (most complete first)
- Summary line categorizes specs into lifecycle stages

### --deep Validation Appendix

```
== Deep Validation ==

auth-system: PASS (all checks passed)
payment-flow: WARN
  - Requirements: 2 acceptance criteria missing EARS notation
  - Design: traceability gap -- US-3 has no component mapping
notification-svc: PASS
search-feature: SKIP (design not yet created)
```

## Verification Logic

Each phase is verified by reading actual files and parsing content -- no trust in self-reported status.

| Phase | File(s) | Verification |
|-------|---------|-------------|
| Requirements | `requirements.md` | Exists AND contains at least one `### US-` heading |
| Design | `design.md` | Exists AND contains `## Components` or `## Architecture` heading |
| Tasks | `tasks.md` | Exists AND contains at least one `### T-` heading |
| Executed | `state.json` | Parse tasks object, count `status: "completed"` vs total. Show as `X/Y` |
| Accepted | `state.json` + `evidence/` | Audit log has `"action": "accepted"` entry OR evidence contains acceptance report |
| Docs | `evidence/` or spec dir | File matching `*docs*` or `*documentation*` exists |
| Retro | `retro.md` + `lessons.json` | `retro.md` exists in spec dir OR `lessons.json` has entries with matching `spec_name` |
| Released | `release.md` | Exists in spec directory AND is non-empty |

## --deep Mode

Adds semantic validation per spec via `spec-validator` agent (Sonnet, read-only):

- EARS pattern coverage in requirements
- Design traceability (every user story maps to a component)
- Task-requirement coverage (every user story has implementing tasks)
- Cross-document consistency

Phases that exist but fail validation are marked `X` instead of `Y`.

## Lifecycle Stage Categorization

Used for the summary line:

| Stage | Condition |
|-------|-----------|
| Released | `release.md` exists |
| Accepted | Accepted but not released |
| In progress | Has tasks with some completed |
| In planning | Has requirements/design but no execution |
| Draft | Only requirements started |

## Skill Definition

- **Location**: `skills/spec-dashboard/SKILL.md`
- **Allowed tools**: `Read`, `Glob`, `Grep`, `Agent` (Agent only for `--deep`)
- **Model routing**: Runs in main context (no subagent for default mode); `--deep` dispatches `spec-validator` (Sonnet)

## Integration

- Register in `.claude-plugin/plugin.json` (no change needed -- skills are auto-discovered)
- Add to CLAUDE.md command table
- Complements `/spec-status` (single-spec deep dive) and `/spec-validate` (single-spec validation)
