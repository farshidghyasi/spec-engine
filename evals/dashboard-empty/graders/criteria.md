---
type: llm
weight: 1
---

A successful response ran the spec-dashboard skill (which executes the plugin's `spec-state.py dashboard`
command via Bash rather than reading state files by hand), states that no specs exist in `.claude/specs/`,
and suggests creating one with `/spec <name>`. It must not invent spec names or fabricate a table of specs.
