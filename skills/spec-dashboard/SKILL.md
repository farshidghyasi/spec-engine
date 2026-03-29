---
name: spec-dashboard
description: Show verified status of all specs in the current project
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
---

# /spec-dashboard Command

Display a portfolio-level view of all specs with verified lifecycle phase completion.

## Usage

```
/spec-dashboard [--deep]
```

- **Default**: Fast file-based verification of all specs
- **`--deep`**: Additionally runs spec-validator per spec for semantic validation

## Workflow

### Step 1: Discover all specs

Use Glob to find all spec directories:

```
.claude/specs/*/requirements.md
```

Extract spec names from directory paths. If no specs found, display:

```
No specs found in .claude/specs/. Run /spec <name> to create one.
```

### Step 2: Verify each spec's phases

For each discovered spec at `.claude/specs/<name>/`, verify these phases by reading actual files and parsing content. Do NOT trust self-reported status — verify through code.

#### 2a. Requirements

- Read `.claude/specs/<name>/requirements.md`
- **PASS**: File exists AND contains at least one `### US-` heading (user story defined)
- **FAIL**: File missing or no user stories found

#### 2b. Design

- Read `.claude/specs/<name>/design.md`
- **PASS**: File exists AND contains a `## Components` or `## Architecture` heading
- **FAIL**: File missing or no architecture/components section found

#### 2c. Tasks

- Read `.claude/specs/<name>/tasks.md`
- **PASS**: File exists AND contains at least one `### T-` heading (task defined)
- **FAIL**: File missing or no tasks found

#### 2d. Validated

- Read `.claude/specs/<name>/state.json`
- Parse the `validation` object
- **PASS**: `validation.status` equals `"pass"`
- **FAIL**: `state.json` missing, no `validation` object, or `validation.status` is not `"pass"`

#### 2f. Execution

- Read `.claude/specs/<name>/state.json`
- Parse the `tasks` object
- Count entries where `status` equals `"completed"` and total entries
- **Display**: Show as `completed/total` (e.g., `7/12`)
- **Not started**: If state.json missing or tasks object is empty, show `—`

#### 2g. Accepted

Check TWO sources (either is sufficient):

1. Read `.claude/specs/<name>/state.json` — scan `audit_log` array for any entry where `action` contains `"accepted"` or `"accept"`
2. Use Glob to check for acceptance evidence: `.claude/specs/<name>/evidence/*accept*`

- **PASS**: Audit log has acceptance entry OR acceptance evidence file exists
- **FAIL**: Neither found

#### 2h. Docs

Check for documentation artifacts:

1. Use Glob: `.claude/specs/<name>/docs/*`

- **PASS**: Any file found in the `docs/` subdirectory
- **FAIL**: `docs/` directory missing or empty

#### 2i. Retro

Check TWO sources:

1. Use Glob: `.claude/specs/<name>/retro.md` — check if file exists
2. Read `.claude/specs/lessons.json` (if it exists) — check for entries where `spec_name` matches the current spec name

- **PASS**: `retro.md` exists OR `lessons.json` has entries for this spec
- **FAIL**: Neither found

#### 2j. Released

- Use Glob: `.claude/specs/<name>/release.md`
- Read the file if it exists to verify it is non-empty (more than just whitespace)
- **PASS**: File exists and has content
- **FAIL**: File missing or empty

### Step 3: Determine lifecycle stage

Categorize each spec based on its verified phases:

| Stage | Condition |
|-------|-----------|
| **Released** | Released phase = PASS |
| **Accepted** | Accepted = PASS but Released = FAIL |
| **In progress** | Execution shows at least 1 completed task |
| **Validated** | Validated = PASS but no execution started |
| **In planning** | Requirements or Design or Tasks = PASS but not yet validated |
| **Draft** | Only requirements started (no design yet) |

### Step 4: Render the dashboard

Sort specs by progress (most complete first — released > accepted > in progress > validated > planning > draft). Within the same stage, sort alphabetically.

Display format:

```
📋 Spec Dashboard

| Spec             | Req | Design | Tasks | Valid | Exec  | Accepted | Docs | Retro | Rel |
|------------------|-----|--------|-------|-------|-------|----------|------|-------|-----|
| auth-system      | ✅  | ✅     | ✅    | ✅    | 10/10 | ✅       | ✅   | ✅    | ✅  |
| payment-flow     | ✅  | ✅     | ✅    | ✅    | 6/12  | ❌       | ❌   | ❌    | ❌  |
| notification-svc | ✅  | ✅     | ❌    | ❌    | —     | ❌       | ❌   | ❌    | ❌  |
| search-feature   | ✅  | ❌     | ❌    | ❌    | —     | ❌       | ❌   | ❌    | ❌  |

✅ = verified  ❌ = not done  ⚠️ = failed validation (--deep only)

Summary: 4 specs | 1 released | 1 in progress | 2 in planning
```

Symbols:
- `✅` — phase verified through file content
- `❌` — phase not done (file missing or empty)
- `⚠️` — phase exists but failed deep validation (only in `--deep` mode)
- Exec column shows `completed/total` or `—` (em dash) if not started

### Step 5: --deep mode (only if flag provided)

If `--deep` is specified, AFTER rendering the default table:

1. For each spec that has at least requirements.md, dispatch the `spec-validator` agent:

```
Agent tool:
  subagent_type: spec-engine:spec-validator
  prompt: "Validate the spec at .claude/specs/<name>/. Run the full validation checklist.
           Report: EARS pattern compliance, design traceability, task-requirement coverage,
           and cross-document consistency. Return a structured result with pass/fail per check."
```

2. For specs where validation finds issues, update the table symbol from `✅` to `⚠️` for the affected phase
3. Append a validation summary:

```
🔍 Deep Validation

| Spec             | Result | Details                                              |
|------------------|--------|------------------------------------------------------|
| auth-system      | ✅ PASS | All checks passed                                    |
| payment-flow     | ⚠️ WARN | Req: 2 criteria missing EARS; Design: US-3 unmapped  |
| notification-svc | ✅ PASS | All checks passed                                    |
| search-feature   | ⏭️ SKIP | Design not yet created                                |
```

Dispatch validators in parallel for independent specs (use multiple Agent tool calls in a single response).

### Step 6: Suggest next actions

After the table, suggest the most impactful next action based on the overall state:

- If any spec is in progress: `Next: Run /spec-status <name> for detailed progress on in-progress specs`
- If any spec is validated: `Next: Run /spec-exec <name> or /spec-loop <name> to start execution`
- If any spec is in planning: `Next: Run /spec-validate <name> to validate before execution`
- If any spec is accepted but not released: `Next: Run /spec-release <name> to generate release artifacts`
- If all specs are released: `All specs complete! Run /spec-retro <name> on any spec missing a retrospective`
