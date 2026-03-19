---
name: spec-refine
description: Refine requirements or design with change impact analysis
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
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
- **Preserve completed task status** for unaffected tasks
- Mark affected completed tasks as "needs-review" in state.json

### Step 4: Update Integrity Manifest

Recompute SHA256 hashes for all modified spec files. Update state.json.

### Step 5: Add Change Log Entry

Append to a `## Change Log` section at the bottom of requirements.md:

```
### Change [date]
- Modified: US-3 (updated profile fields)
- Added: US-7 (password reset via SMS)
- Impact: T-5 needs rework, 3 new tasks added
```
