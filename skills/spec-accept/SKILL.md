---
name: spec-accept
description: Run user acceptance testing against spec requirements
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-accept Command

Run user acceptance testing to formally verify the implementation satisfies all requirements.

## Usage

```
/spec-accept [spec-name]
```

## Workflow

1. Locate spec directory, validate spec name
2. Delegate to spec-acceptor agent with:
   - requirements.md, design.md, tasks.md, state.json
   - Evidence from `evidence/` directory (screenshots, test results, review reports)
3. Present the acceptance report to the user
4. Ask via AskUserQuestion: "Accept this implementation?" / "Request changes"
