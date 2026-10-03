---
name: spec-tasks
description: Regenerate tasks from updated spec requirements and design
argument-hint: "[spec-name]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-tasks

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. Read the current tasks.md and `$SS summary <spec>` to capture which tasks are completed.
2. Build the Verified Interface Registry as in `/spec` step 7.
3. Dispatch `spec-tasker` to regenerate tasks.md from requirements.md and design.md. Tell it which
   task IDs are completed and must keep their IDs, titles and Files unless the requirement changed.
4. `$SS sync-tasks <spec>` (keeps status/wired/failures for task IDs that still exist) and
   `$SS validate <spec>`; on errors re-dispatch the tasker with the output.
5. `$SS integrity <spec> --update`. If the phase was `validated` or later, `$SS phase <spec> spec`
   and suggest `/spec-validate`.
