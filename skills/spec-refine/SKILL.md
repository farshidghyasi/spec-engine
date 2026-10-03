---
name: spec-refine
description: Refine requirements or design with change impact analysis
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-refine Command

Update requirements or design for an existing spec with change impact analysis.

## Usage

```
/spec-refine [spec-name]
```

## Workflow

### Step 1: Understand Changes

Ask the user what they want to change via AskUserQuestion:
- Which requirements are changing?
- Are requirements being added, modified, or removed?
- Has the design approach changed?

### Step 2: Change Impact Analysis

Before applying any changes:

1. For each requirement being changed:
   - Find design components with `Covers: US-X` referencing it
   - Find tasks with `Covers: US-X` referencing it
   - Check task completion status in state.json

2. Present impact report:
```
## Change Impact Analysis

### Modifying US-3: User profile editing
- Design components affected: ProfileService, ProfileController
- Tasks affected: T-5 (completed), T-8 (pending)
- Impact: HIGH — 1 completed task may need rework

### Adding US-7: Password reset via SMS
- New design components needed: SMSService
- New tasks estimated: ~3
- Impact: LOW — additive, no existing tasks affected
```

3. Ask user to approve the impact before proceeding.

### Step 3: Apply Changes

- Delegate to spec-planner agent for requirement/design changes
- Delegate to spec-tasker agent for task regeneration
- Tell the tasker which completed task IDs must keep their IDs and Files unless their requirement changed

### Step 4: Sync State

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
$SS sync-tasks <spec>          # keeps status of unchanged task IDs
$SS integrity <spec> --update
$SS phase <spec> spec          # changed specs must be re-validated
```
Mark affected completed tasks with `$SS set-task <spec> T-X --status needs-review`.

### Step 4.5: Show Spec Diff

After changes are applied and before the change log:

1. Run `git diff -- .claude/specs/<name>/requirements.md .claude/specs/<name>/design.md .claude/specs/<name>/tasks.md` to capture what changed
2. Present the diff to the user in a code block:

   ```
   ## Spec Changes

   ```diff
   --- a/.claude/specs/auth-system/requirements.md
   +++ b/.claude/specs/auth-system/requirements.md
   @@ -45,6 +45,12 @@
    ### US-3: User profile editing
   +
   +#### Acceptance Criteria (EARS Notation)
   +
   +1. WHEN user submits profile update with valid phone number
   +   THE SYSTEM SHALL save the phone number and send verification SMS
   ```

   This makes it easy to see exactly what the refine operation changed, especially when multiple requirements and design components are affected.

**Note:** If git is not available or the spec files aren't tracked, skip this step silently.

### Step 5: Add Change Log Entry

Append to a `## Change Log` section at the bottom of requirements.md:

```
### Change [date]
- Modified: US-3 (updated profile fields)
- Added: US-7 (password reset via SMS)
- Impact: T-5 needs rework, 3 new tasks added
```
