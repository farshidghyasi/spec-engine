# spec-dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/spec-dashboard` command that provides a verified, portfolio-level view of all specs in the current project with lifecycle phase completion status.

**Architecture:** One new skill file (`skills/spec-dashboard/SKILL.md`) containing the full workflow logic for scanning `.claude/specs/*/`, verifying each phase through file reads and content parsing, and rendering a summary table. One edit to `CLAUDE.md` to register the command. No agents, scripts, or templates needed for default mode. `--deep` mode delegates to existing `spec-validator` agent.

**Tech Stack:** Markdown (skill definition file)

---

### Task 1: Create the spec-dashboard skill file

**Files:**
- Create: `skills/spec-dashboard/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p skills/spec-dashboard
```

- [ ] **Step 2: Write the skill file**

Create `skills/spec-dashboard/SKILL.md` with this exact content:

```markdown
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

` ` `
/spec-dashboard [--deep]
` ` `

- **Default**: Fast file-based verification of all specs
- **`--deep`**: Additionally runs spec-validator per spec for semantic validation

## Workflow

### Step 1: Discover all specs

Use Glob to find all spec directories:

` ` `
.claude/specs/*/requirements.md
` ` `

Extract spec names from directory paths. If no specs found, display:

` ` `
No specs found in .claude/specs/. Run /spec <name> to create one.
` ` `

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

#### 2d. Execution

- Read `.claude/specs/<name>/state.json`
- Parse the `tasks` object
- Count entries where `status` equals `"completed"` and total entries
- **Display**: Show as `completed/total` (e.g., `7/12`)
- **Not started**: If state.json missing or tasks object is empty, show `-`

#### 2e. Accepted

Check TWO sources (either is sufficient):

1. Read `.claude/specs/<name>/state.json` — scan `audit_log` array for any entry where `action` contains `"accepted"` or `"accept"`
2. Use Glob to check for acceptance evidence: `.claude/specs/<name>/evidence/*accept*`

- **PASS**: Audit log has acceptance entry OR acceptance evidence file exists
- **FAIL**: Neither found

#### 2f. Docs

Check for documentation artifacts:

1. Use Glob: `.claude/specs/<name>/evidence/*doc*`
2. Use Glob: `.claude/specs/<name>/*doc*`

- **PASS**: Any documentation file found
- **FAIL**: No documentation artifacts

#### 2g. Retro

Check TWO sources:

1. Use Glob: `.claude/specs/<name>/retro.md` — check if file exists
2. Read `.claude/specs/lessons.json` (if it exists) — check for entries where `spec_name` matches the current spec name

- **PASS**: `retro.md` exists OR `lessons.json` has entries for this spec
- **FAIL**: Neither found

#### 2h. Released

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
| **In planning** | Requirements or Design = PASS but no execution |
| **Draft** | Only requirements started (no design yet) |

### Step 4: Render the dashboard

Sort specs by progress (most complete first — released > accepted > in progress > planning > draft). Within the same stage, sort alphabetically.

Display format:

` ` `
== Spec Dashboard ==

Spec              | Req | Design | Tasks | Exec    | Accepted | Docs | Retro | Released
------------------|-----|--------|-------|---------|----------|------|-------|----------
auth-system       |  Y  |   Y    |  Y    | 10/10   |    Y     |  Y   |  Y    |   Y
payment-flow      |  Y  |   Y    |  Y    |  6/12   |    -     |  -   |  -    |   -
notification-svc  |  Y  |   Y    |  -    |  -      |    -     |  -   |  -    |   -
search-feature    |  Y  |   -    |  -    |  -      |    -     |  -   |  -    |   -

Legend: Y = verified  - = not done  X = failed (--deep only)

Summary: 4 specs | 1 released | 1 in progress | 2 in planning
` ` `

Symbols:
- `Y` — phase verified through file content
- `-` — phase not done (file missing or empty)
- `X` — phase exists but failed deep validation (only in `--deep` mode)
- Exec column always shows `completed/total` or `-`

### Step 5: --deep mode (only if flag provided)

If `--deep` is specified, AFTER rendering the default table:

1. For each spec that has at least requirements.md, dispatch the `spec-validator` agent:

` ` `
Agent tool:
  subagent_type: spec-engine:spec-validator
  prompt: "Validate the spec at .claude/specs/<name>/. Run the full validation checklist. Report: EARS pattern compliance, design traceability, task-requirement coverage, and cross-document consistency. Return a structured result with pass/fail per check."
` ` `

2. For specs where validation finds issues, update the table symbol from `Y` to `X` for the affected phase
3. Append a validation summary:

` ` `
== Deep Validation ==

auth-system: PASS (all checks passed)
payment-flow: WARN
  - Requirements: 2 acceptance criteria missing EARS notation
  - Design: traceability gap -- US-3 has no component mapping
notification-svc: PASS
search-feature: SKIP (design not yet created)
` ` `

Dispatch validators in parallel for independent specs (use multiple Agent tool calls in a single response).

### Step 6: Suggest next actions

After the table, suggest the most impactful next action based on the overall state:

- If any spec is in progress: `Next: Run /spec-status <name> for detailed progress on in-progress specs`
- If any spec is in planning: `Next: Run /spec-exec <name> or /spec-loop <name> to start execution`
- If any spec is accepted but not released: `Next: Run /spec-release <name> to generate release artifacts`
- If all specs are released: `All specs complete! Run /spec-retro <name> on any spec missing a retrospective`
```

- [ ] **Step 3: Verify the skill file structure**

```bash
head -5 skills/spec-dashboard/SKILL.md
```

Expected:
```
---
name: spec-dashboard
description: Show verified status of all specs in the current project
allowed-tools:
  - Read
```

```bash
grep -c "### Step" skills/spec-dashboard/SKILL.md
```

Expected: 6

- [ ] **Step 4: Commit**

```bash
git add skills/spec-dashboard/SKILL.md
git commit -m "feat: add /spec-dashboard skill for portfolio-level spec overview"
```

---

### Task 2: Register spec-dashboard in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md:29` (Commands table)

- [ ] **Step 1: Add the command to the Commands table**

In `CLAUDE.md`, find the Commands table. Add this row after the `/spec-status` row (line 30):

```markdown
| `/spec-dashboard` | Portfolio view of all specs with verified phase completion |
```

The table should read:
```
| `/spec-status` | Progress dashboard with cost tracking and wiring health |
| `/spec-dashboard` | Portfolio view of all specs with verified phase completion |
| `/spec-exec` | Execute one iteration with quality gates |
```

- [ ] **Step 2: Verify the edit**

```bash
grep "spec-dashboard" CLAUDE.md
```

Expected: One line showing the new table row.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add /spec-dashboard to CLAUDE.md commands table"
```

---

### Task 3: Verify end-to-end skill discovery

**Files:** (none modified — verification only)

- [ ] **Step 1: Verify skill file is discoverable**

```bash
ls -la skills/spec-dashboard/SKILL.md
```

Expected: File exists with non-zero size.

- [ ] **Step 2: Verify frontmatter is valid**

```bash
head -8 skills/spec-dashboard/SKILL.md
```

Expected: Valid YAML frontmatter with name, description, and allowed-tools fields.

- [ ] **Step 3: Verify all phase checks are documented**

```bash
grep -c "^#### 2[a-h]\." skills/spec-dashboard/SKILL.md
```

Expected: 8 (one per phase: requirements, design, tasks, execution, accepted, docs, retro, released)

- [ ] **Step 4: Verify --deep mode is documented**

```bash
grep -c "spec-validator" skills/spec-dashboard/SKILL.md
```

Expected: At least 1 (reference to the validator agent)

- [ ] **Step 5: Final review — read the complete skill**

Read the full `skills/spec-dashboard/SKILL.md` and verify:
- All 8 phase verifications have concrete file paths and pass/fail criteria
- The display format matches the design spec
- `--deep` mode delegates to spec-validator (not reimplementing validation)
- Next action suggestions cover all lifecycle states
