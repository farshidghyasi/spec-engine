---
name: spec
description: Start a new spec-driven development workflow for a feature
argument-hint: "<feature-name>"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec Command

Create a new specification using the 3-phase workflow: Requirements, Design, Tasks.

## Arguments

- `feature-name` (required): Name for the feature spec (lowercase, hyphens, dots, underscores only)

## Workflow

### Step 1: Validate and Initialize

1. Validate the spec name matches `^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]?$`. If invalid, reject with an error.
2. Check if `.claude/specs/<feature-name>/` already exists. If so, ask the user if they want to overwrite.
3. Create the spec directory: `.claude/specs/<feature-name>/`
4. Copy templates from `${CLAUDE_PLUGIN_ROOT}/templates/` to the spec directory:
   - `requirements.md`, `design.md`, `tasks.md`, `state.json`, `init.sh`
5. Create `evidence/screenshots/`, `evidence/reviews/`, `evidence/tests/`, `handoffs/` subdirectories

### Step 2: Read Lessons

If `.claude/specs/lessons.json` exists, read it and extract lessons relevant to this feature type. Present the top 3 relevant lessons to the user: "Based on past specs, consider: [lesson]"

### Step 3: Preset Selection

Ask the user via AskUserQuestion:

> Would you like to start from a preset template or from scratch?

Options:
- **REST API** — Pre-filled user stories for CRUD, validation, auth, errors, pagination
- **React Page** — Pre-filled user stories for rendering, routing, state, API integration, responsive layout
- **CLI Tool** — Pre-filled user stories for arg parsing, subcommands, output formatting, errors
- **Start from scratch** — Blank requirements

If a preset is selected, read `${CLAUDE_PLUGIN_ROOT}/templates/presets/<slug>.md`.

### Step 4: Interactive Requirements Gathering

**This phase runs inline, NOT in a subagent** (subagents cannot use AskUserQuestion).

Use AskUserQuestion in 2-3 rounds:

**Round 1: Scope and Users**
- What is the core problem this feature solves? What are the boundaries?
- Who will use this feature? What are their goals?

**Round 2: Behaviors and Edge Cases**
- What are the main actions/flows?
- What happens when things go wrong? Invalid input? Network failures?
- Security concerns? Authentication, authorization, data sensitivity?

**Round 3: Non-Functional and Context**
- Performance expectations? Accessibility? Scalability?
- What explicitly should NOT be included?
- Read relevant existing code to understand architecture, patterns, conventions.

Collect all answers into a structured brief.

### Step 5: Requirements + Design Writing (spec-planner agent)

Delegate to the **spec-planner** agent using the Agent tool. Pass ALL context:

- Feature name and spec directory path
- Complete user answers from Step 4
- Relevant codebase context
- Preset content (if selected in Step 3), labeled as "Preset Template — customize, do not copy verbatim"
- Relevant lessons from lessons.json (if any)
- Instruction: write both requirements.md and design.md, do NOT ask clarifying questions

### Step 6: MANDATORY HUMAN GATE

**Do NOT skip this step.** After the spec-planner completes:

1. Read the generated design.md
2. Present a design summary to the user:
   - Components identified
   - Key architectural decisions
   - Data models
   - API contracts (if any)
   - Risks identified
3. Ask via AskUserQuestion: "Review the design above. How would you like to proceed?"
   - **Approve and continue to tasks** — proceed to Step 7
   - **Request changes** — go back to spec-planner with the user's feedback
   - **Cancel** — stop the workflow

### Step 7: Tasks Phase (spec-tasker agent)

After design approval, delegate to the **spec-tasker** agent:

- Feature name and spec directory path
- Instruction: read requirements.md and design.md, generate tasks.md, update state.json

### Step 8: Compute Integrity Manifest

After tasks are written:

1. Compute SHA256 of requirements.md, design.md, tasks.md
2. Update state.json `integrity` section with the hashes and current timestamp
3. Record the current git SHA in `state.json.reproducibility.git_sha_start`

### Step 9: Parse init.sh

Read init.sh in the spec directory. If quality gate commands are defined (lint_cmd, typecheck_cmd, test_cmd), update state.json `quality_gates` section. Also read budget_cap and human_checkpoint_interval if defined.

### Step 10: Summary

Present:
- Number of user stories created (distinguish user-stated vs [inferred])
- Number of tasks created
- Wave breakdown (how many waves, tasks per wave)
- Key architectural decisions
- Risks identified
- Quality gates configured (or "Not configured — edit init.sh")
- Next steps: suggest `/spec-validate` before implementation, then `/spec-exec` or `/spec-loop`
