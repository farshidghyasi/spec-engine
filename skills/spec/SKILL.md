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

## Options

- `--consensus`: Enable consensus planning. After the planner writes the initial draft, an Architect and Critic review it before finalization. Adds ~2x tokens to the planning phase but catches more design issues.

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

### Step 5.5: Threat Model Dispatch (Always On)

After the spec-planner completes (writing both requirements.md and design.md), dispatch the **spec-threat-modeler** agent:

- Pass: spec directory path, content of requirements.md, content of design.md
- The agent writes `evidence/threat-model.md`, injects `[threat-model]` criteria into requirements.md, and updates `state.json.security.threat_model_status`
- On agent error or timeout: append `{ "event": "threat_model_failed", "reason": "<error>" }` to the audit log and continue to the next step without blocking

There is NO opt-out for this step.

### Step 5.6: Consensus Deliberation (only if --consensus)

If `--consensus` flag was provided:

1. **Architect Review**: Dispatch spec-consultant agent with:
   - Role: "Software Architect"
   - Question: "Review this requirements.md and design.md. Evaluate: component boundaries, scalability, integration patterns, and technical debt risk. List specific concerns and improvement suggestions."
   - Context: The full requirements.md and design.md content

2. **Critic Review**: Dispatch spec-consultant agent (in parallel with Architect) with:
   - Role: "Critical Analyst"
   - Question: "Review this requirements.md and design.md as a devil's advocate. Find: missing edge cases, unstated assumptions, scope creep risks, and requirements that are untestable. Be specific — cite the exact requirement or design section."
   - Context: The full requirements.md and design.md content

3. **Revision**: After both consultants respond, dispatch spec-planner agent again with:
   - The original requirements.md and design.md
   - Architect feedback
   - Critic feedback
   - Instruction: "Revise requirements.md and design.md to address the feedback. Do NOT ask questions — make the best judgment call for each concern. Add an `## Architect Review Notes` and `## Critic Review Notes` appendix to design.md summarizing what was addressed."

The output is the same requirements.md + design.md — downstream contracts are unchanged. The human gate in Step 6 still applies.

### Step 6: MANDATORY HUMAN GATE

**Do NOT skip this step.** After the spec-planner completes:

1. Read the generated design.md
2. Present a design summary to the user:
   - Components identified
   - Key architectural decisions
   - Data models
   - API contracts (if any)
   - Risks identified
   - Threat model findings: if evidence/threat-model.md exists, show the "Injected Criteria" section. For each [threat-model] criterion shown, ask the user to approve or reject it. For each rejection: remove it from requirements.md and append { "event": "threat_model_criterion_rejected", "criterion": "<text>", "reason": "<user reason>" } to the audit log.
3. Ask via AskUserQuestion: "Review the design above. How would you like to proceed?"
   - **Approve and continue to tasks** — proceed to Step 7
   - **Request changes** — go back to spec-planner with the user's feedback
   - **Cancel** — stop the workflow

### Step 6.5: Build Interface Registry (MANDATORY before tasking)

After design is approved, build a verified interface registry from the actual codebase. This prevents the tasker from guessing at interface shapes.

1. **Read design.md** and extract every referenced:
   - Type/interface name (e.g., `Transaction`, `UserProfile`, `ApiResponse`)
   - Function/method name (e.g., `createTransaction`, `validateInput`)
   - File path (e.g., `src/types/transaction.ts`, `src/services/auth.ts`)
   - Database table/column reference
   - API endpoint reference

2. **For each referenced item**, use Grep/Read to find the actual definition in the codebase:
   - Record exact type shapes with all field names and types
   - Record exact function signatures (parameters, return types, async/sync)
   - Record exact import paths as used by existing consumers
   - If an item doesn't exist in the codebase, mark it as `[NEW]`

3. **Compile the registry** as a markdown code block:
   ```
   ## Verified Interface Registry

   // From src/types/transaction.ts
   interface Transaction { id: string; debitAmount: number; creditAmount: number; status: "pending" | "completed" }

   // From src/services/auth.ts
   export async function validateToken(token: string): Promise<{ userId: string; role: Role }>

   // [NEW] — to be created by this spec
   interface AuditLog { ... }
   ```

4. **Pass this registry** to the spec-tasker agent in the next step. The tasker MUST use these exact shapes in task descriptions, not design.md paraphrases.

### Step 7: Tasks Phase (spec-tasker agent)

After design approval, delegate to the **spec-tasker** agent:

- Feature name and spec directory path
- The Verified Interface Registry from Step 6.5
- Instruction: read requirements.md and design.md, use the provided Interface Registry as ground truth for all type shapes and function signatures, generate tasks.md, update state.json

### Step 7.5: Auto-Calculate Budget

After the tasker completes and `state.json.tasks` is populated:
1. Count the total number of tasks in `state.json.tasks` (call it `task_count`)
2. If `state.json.execution.budget_cap` is null: set it to `task_count * 50000`
3. Log "Budget auto-calculated: <cap> tokens (<task_count> tasks x 50000)" to the audit log
4. If `state.json.execution.budget_cap` is already non-null: do NOT overwrite it
   (manually configured budgets take precedence)

### Step 8: Compute Integrity Manifest

After tasks are written:

1. Compute SHA256 of requirements.md, design.md, tasks.md
2. Update state.json `integrity` section with the hashes and current timestamp
3. Record the current git SHA in `state.json.reproducibility.git_sha_start`
4. **Populate `referenced_codebase_files`**: Scan design.md and tasks.md for all codebase file paths referenced (in `Files:` fields, import paths, interface source locations). Record these in `state.json.reproducibility.referenced_codebase_files`. This list is used for drift detection — if another spec modifies any of these files before this spec executes, the spec is stale and needs re-validation.

### Step 9: Auto-Detect and Parse init.sh

1. **Auto-detect project type** (if init.sh has no gates configured):

   Check for project manifests and populate init.sh quality gates automatically:

   | Manifest | Project Type | Default Gates |
   |----------|-------------|---------------|
   | `package.json` | Node.js | lint: `npm run lint` (if script exists), typecheck: `npx tsc --noEmit` (if tsconfig.json exists), test: `npm test` (if script exists) |
   | `pyproject.toml` / `setup.py` | Python | lint: `ruff check .` or `flake8`, typecheck: `mypy .` (if in deps), test: `pytest` (if in deps) |
   | `Cargo.toml` | Rust | lint: `cargo clippy -- -D warnings`, typecheck: `cargo check`, test: `cargo test` |
   | `go.mod` | Go | lint: `golangci-lint run` (if installed), typecheck: `go vet ./...`, test: `go test ./...` |

   For Node.js projects, read `package.json` `scripts` object to verify which scripts actually exist before setting gates.

   Show the user what was detected:
   ```
   Detected Node.js project (from package.json).
   Auto-configured quality gates:
     lint: npm run lint
     typecheck: npx tsc --noEmit
     test: npm test

   Edit .claude/specs/<name>/init.sh to customize.
   ```

2. **Parse init.sh**: Read quality gate commands (supporting both `gates=()` array and legacy individual variables). Update state.json `quality_gates` section.

3. **Read budget_cap and human_checkpoint_interval** if defined.

### Step 10: Summary

Present:
- Number of user stories created (distinguish user-stated vs [inferred])
- Number of tasks created
- Wave breakdown (how many waves, tasks per wave)
- Key architectural decisions
- Risks identified
- Quality gates configured (or "Not configured — edit init.sh")
- Next steps: suggest `/spec-validate` before implementation, then `/spec-exec` or `/spec-loop`

Set `state.json.phase` to `"spec"` to record that spec creation is complete.
Log "Phase set to 'spec'" to the audit log.
