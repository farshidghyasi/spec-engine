---
name: spec-validate
description: Validate spec completeness and consistency
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-validate Command

Validate a spec for completeness, EARS notation compliance, traceability, and implementation readiness.

## Usage

```
/spec-validate [spec-name] [--no-fix]
```

If `spec-name` is omitted, auto-detect if only one spec exists.

## Options

- `--no-fix`: Skip auto-fix and only report errors. By default, validation automatically fixes ERROR-level issues.

## Workflow

1. **Locate spec**: Find the spec directory in `.claude/specs/`. Validate the spec name.
2. **Drift detection**: Check if the codebase has changed under this spec since it was written:
   a. Read `state.json` for `reproducibility.git_sha_start` and `reproducibility.referenced_codebase_files`
   b. If `git_sha_start` is missing (older spec), fall back to `state.json.created_at` and use `git log --since="<created_at>" --diff-filter=M --name-only -- <referenced_files>` instead
   c. If `referenced_codebase_files` is missing (older spec), skip drift detection — the Codebase Accuracy Check in step 3 will catch mismatches anyway
   d. If both exist, run: `git diff --name-only <git_sha_start>..HEAD -- <referenced_files>`
   e. If any files changed, warn the user:
      ```
      ⚠ Codebase drift detected — N files referenced by this spec have changed since it was written:
      - src/services/auth.ts (modified by commit abc1234: "feat: add currency param to createTransaction")
      - src/types/transaction.ts (modified by commit def5678: "refactor: rename debit fields")

      Auto-fix will update the spec to match the current codebase.
      ```
   f. Drift-detected specs get auto-fixed regardless of `--no-fix` (since the spec is guaranteed stale). The user is always shown what changed.
3. **Delegate to spec-validator agent**: Use the Agent tool to spawn the spec-validator agent with:
   - The spec directory path
   - Instruction to run the full validation checklist
4. **Present results**: Show the validation report to the user
5. **Auto-fix (default, skip if `--no-fix`)**: If validation failed with ERROR-level issues:
   a. Parse the validation report for ERROR-level issues
   b. Dispatch the spec-debugger agent with:
      - The spec directory path
      - The full validation report
      - Instruction: "Fix the ERROR-level issues in the spec files (requirements.md, design.md, tasks.md) by reading the actual codebase. The codebase is the source of truth — ALWAYS fix spec files to match the codebase, NEVER fix the codebase to match the spec. For interface shape mismatches, grep for the real definition and update the spec to match. For import path errors, verify the correct path and fix it. For count mismatches, recount and fix the prose. Your scope is ONLY files inside .claude/specs/ — do not touch source code, tests, or any other file."
   c. After debugger completes, re-run the spec-validator agent
   d. Present a **change summary** showing what was fixed:
      ```
      ## Auto-Fixed Issues
      - [file]: [what changed] — [why]
      ```
   e. If still failing after auto-fix, show remaining issues and suggest manual fixes
6. **Update integrity manifest**: If validation passes, recompute SHA256 hashes, update `referenced_codebase_files`, and set `git_sha_start` to current HEAD in state.json
