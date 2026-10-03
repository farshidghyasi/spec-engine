---
name: spec-docs
description: Generate user-facing documentation from spec and implementation
argument-hint: "[spec-name] [--output-dir <path>]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-docs

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. `$SS phase-gate <spec> accepted` (`audited` also satisfies it; stop with the message on failure).
2. Output dir defaults to `.claude/specs/<spec>/docs/`.
3. Dispatch `spec-documenter` with the spec files and the output dir.
4. List the generated documents, then `$SS phase <spec> documented`.
