---
name: spec-import
description: Import a markdown document and convert it to spec requirements
argument-hint: "<file-path> [--spec-name <name>]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-import

Convert a PRD, RFC or design doc into spec-engine format.

1. Read the document. If `--spec-name` is missing, ask for one.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py init <name>`.
3. Dispatch `spec-planner` with the document, "extract requirements in EARS notation and derive
   design.md from the document; do not ask questions".
4. Continue from `/spec` step 5 (threat model) through step 9 exactly as written there.
