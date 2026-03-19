---
name: spec-docs
description: Generate user-facing documentation from spec and implementation
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-docs Command

Generate documentation from spec files and implemented code.

## Usage

```
/spec-docs [spec-name] [--output-dir <path>]
```

## Workflow

1. Locate spec directory, validate spec name
2. Default output: `.claude/specs/<name>/docs/`
3. Delegate to spec-documenter agent with spec files and output directory
4. Present list of generated documents to user
