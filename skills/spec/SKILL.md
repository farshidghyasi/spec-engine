---
name: spec
description: Start a new spec-driven development workflow for a feature
argument-hint: "<feature-name> [--consensus]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec

Create a specification in three phases: Requirements (EARS) -> Design (architecture, human gate) -> Tasks (wave DAG).

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

## Options

- `--consensus`: after the planner's draft, an Architect and a Critic (spec-consultant) review it and the
  planner revises. About 2x planning tokens.

## Workflow

### 1. Initialize

`$SS init <feature-name>` (validates the name, copies templates, creates `evidence/` and `handoffs/`,
records `git_sha_start`). If it reports the directory exists, ask the user whether to overwrite and
re-run with `--force`.

### 2. Lessons and preset

- If `.claude/specs/lessons.json` exists, read it and show the top 3 lessons relevant to this feature.
- Ask via AskUserQuestion whether to start from a preset (REST API, React Page, CLI Tool) or from
  scratch. Presets live in `${CLAUDE_PLUGIN_ROOT}/templates/presets/<slug>.md`.

### 3. Interactive requirements gathering (inline, not in a subagent)

Use AskUserQuestion in 2-3 rounds:

1. Scope and users: the core problem, boundaries, who uses it and why.
2. Behaviors and edge cases: main flows, failure modes (invalid input, network), security concerns
   (auth, data sensitivity).
3. Non-functional and context: performance, accessibility, scale, explicit non-goals. Read the
   relevant existing code to learn architecture and conventions.

Collect everything into a structured brief.

### 4. Requirements and design (spec-planner, Opus)

Dispatch `spec-planner` with: feature name and spec dir, the full brief, codebase context, the preset
(labelled "customize, do not copy"), relevant lessons, and "write requirements.md and design.md; do not
ask questions".

### 5. Threat model (always on)

Dispatch `spec-threat-modeler` with the spec dir and the contents of requirements.md and design.md. It
writes `evidence/threat-model.md` and appends `[threat-model]` criteria to requirements.md. Afterwards:
`$SS set <spec> security.threat_model_status completed` and `$SS log <spec> threat_model_complete`.
On agent error: `$SS log <spec> threat_model_failed --details "<error>"` and continue.

### 5.5. Consensus (only with --consensus)

Dispatch two `spec-consultant` agents in parallel (Software Architect: boundaries, scalability,
integration, debt risk; Critical Analyst: missing edge cases, unstated assumptions, scope creep,
untestable requirements; both must cite exact sections). Then dispatch `spec-planner` again with both
reviews and "revise; do not ask questions; add `## Architect Review Notes` and `## Critic Review Notes`
to design.md".

### 6. Human gate (mandatory)

Read design.md and present: components, key decisions, data models, API contracts, risks, and the
"Injected Criteria" from `evidence/threat-model.md` (ask approve/reject per criterion; on reject remove
it from requirements.md and `$SS log <spec> threat_model_criterion_rejected --details "<text>"`).
Then AskUserQuestion: Approve and continue / Request changes (back to step 4 with feedback) / Cancel.

### 7. Verified interface registry

Extract every type, function, file path, table and endpoint that design.md references. Grep/Read the
codebase for each and record the exact shape, signature and import path; mark missing ones `[NEW]`.
Compile a `## Verified Interface Registry` code block. This is passed to the tasker as ground truth.

### 8. Tasks (spec-tasker, Sonnet)

Dispatch `spec-tasker` with the spec dir and the registry: "read requirements.md and design.md, use the
registry as ground truth, write tasks.md only (do not write state.json)". It returns a
`PARALLEL_CONFIG_JSON` block; apply it with `$SS set <spec> parallel.shared_files '[...]'`,
`parallel.generated_files` and `parallel.post_merge_commands`. Then:

```
$SS sync-tasks <spec>          # waves (Kahn), state.json tasks, budget cap, referenced files
$SS validate <spec>            # structural check; on errors re-dispatch the tasker with the output
$SS integrity <spec> --update
$SS detect-gates <spec>        # auto-detect lint/typecheck/test from the project manifest
$SS phase <spec> spec
```

### 9. Summary

Show: user stories (user-stated vs `[inferred]`), task count and wave breakdown (from `$SS summary`),
key decisions, risks, the gates configured (or "edit init.sh"), and next steps:
`/spec-validate`, then `/spec-loop` (or `/spec-exec`, `/spec-team`).
