---
name: spec-import
description: Import a markdown document and convert it to spec requirements
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-import Command

Import an existing document (PRD, RFC, design doc) and convert it to spec-engine format.

## Usage

```
/spec-import <file-path> [--spec-name <name>]
```

## Workflow

1. Read the imported document
2. If `--spec-name` not provided, ask the user for a name
3. Validate spec name
4. Create spec directory and copy templates
5. Delegate to spec-planner agent with:
   - The imported document content
   - Instruction to extract requirements in EARS format
   - Instruction to derive design from the document
6. Run the mandatory human gate (present design summary for approval)
7. Delegate to spec-tasker for task generation
8. Compute integrity manifest
