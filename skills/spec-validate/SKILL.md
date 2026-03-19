---
name: spec-validate
description: Validate spec completeness and consistency
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
---

# /spec-validate Command

Validate a spec for completeness, EARS notation compliance, traceability, and implementation readiness.

## Usage

```
/spec-validate [spec-name]
```

If `spec-name` is omitted, auto-detect if only one spec exists.

## Workflow

1. **Locate spec**: Find the spec directory in `.claude/specs/`. Validate the spec name.
2. **Delegate to spec-validator agent**: Use the Agent tool to spawn the spec-validator agent with:
   - The spec directory path
   - Instruction to run the full validation checklist
3. **Present results**: Show the validation report to the user
4. **Update integrity manifest**: If validation passes, recompute SHA256 hashes and update state.json
