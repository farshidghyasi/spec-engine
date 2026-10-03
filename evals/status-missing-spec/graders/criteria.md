---
type: llm
weight: 1
---

A successful response used the spec-status skill, which runs `spec-state.py status payments-v2` via Bash,
and reports clearly that the spec does not exist (no `.claude/specs/payments-v2` directory or no specs at
all), pointing the user to `/spec payments-v2` to create it. It must not fabricate progress, tasks,
waves, or token numbers.
