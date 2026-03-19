---
name: spec-tasks
description: Regenerate tasks from updated spec requirements and design
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
---

# /spec-tasks Command

Regenerate tasks from an updated spec. Preserves completed task status for unaffected tasks.

## Usage

```
/spec-tasks [spec-name]
```

## Workflow

1. Locate spec directory, validate spec name
2. Read current tasks.md and state.json to capture existing task statuses
3. Delegate to spec-tasker agent to regenerate tasks from requirements.md and design.md
4. After regeneration, restore completion status for tasks that were not affected by changes
5. Recompute wave assignments
6. Update state.json with new task list and waves
7. Update integrity manifest
