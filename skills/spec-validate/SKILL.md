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
3. **Validation fingerprint check**: Before spawning the validator agent, check if validation can be skipped:
   a. Read `state.json.validation.report_hash` and `state.json.integrity_manifest`
   b. Recompute SHA256 hashes of `requirements.md`, `design.md`, `tasks.md`, and `state.json`
   c. If ALL hashes match the integrity manifest AND no drift was detected in step 2:
      - Output: `"Spec unchanged since last validation (hash: <short_hash>) — PASS."`
      - Skip to step 7 (update integrity manifest)
   d. If any hash changed or drift was detected, proceed to step 4

4. **Delegate to spec-validator agent**: Use the Agent tool to spawn the spec-validator agent with:
   - The spec directory path
   - Instruction to run the full validation checklist
   - If `state.json.validation.acknowledged_warnings` exists, include them with: "These warnings were already reported. Only re-report a warning if the underlying spec text has changed (compare against the integrity hashes from the previous run). Report new issues normally."

5. **Present results**: Show the validation report to the user

6. **Auto-fix (default, skip if `--no-fix`)**: If validation failed with ERROR-level issues:
   a. Parse the validation report for ERROR-level issues
   b. Dispatch the spec-debugger agent with:
      - The spec directory path
      - The full validation report
      - Instruction: "Fix the ERROR-level issues in the spec files (requirements.md, design.md, tasks.md) by reading the actual codebase. The codebase is the source of truth — ALWAYS fix spec files to match the codebase, NEVER fix the codebase to match the spec. For interface shape mismatches, grep for the real definition and update the spec to match. For import path errors, verify the correct path and fix it. For count mismatches, recount and fix the prose. Your scope is ONLY files inside .claude/specs/ — do not touch source code, tests, or any other file."
   c. **Verify fixes syntactically** (do NOT re-run the validator agent):
      - Confirm state.json parses as valid JSON
      - Confirm task IDs in state.json still match tasks.md
      - Confirm wave assignments in state.json still match tasks.md
      - Recompute integrity hashes to verify spec files were actually modified
      - If any syntactic check fails, show remaining issues and suggest manual fixes
   d. Present a **change summary** showing what was fixed:
      ```
      ## Auto-Fixed Issues
      - [file]: [what changed] — [why]
      ```

<HARD-GATE>
Step 7 is MANDATORY after every validation run — whether the result is pass, fail, or fail-then-fixed.
The dashboard reads `state.json.validation.status` to populate the "Valid" column.
If you skip Step 7, validation results are invisible to `/spec-dashboard` and `/spec-status`.

You WILL be tempted to skip this step. These rationalizations have all caused real failures:

| You will think... | Reality |
|---|---|
| "I already showed the results to the user, we're done" | The user saw them. The dashboard didn't. state.json is the machine-readable record. |
| "The auto-fix summary was the last step" | The fix summary is user output. state.json is system state. Both are required. |
| "Validation passed, nothing to write" | A pass is a status. "No status" and "pass" are not the same thing. Write it. |
| "I'll update state.json next time" | There is no next time. Each validation run is independent. |
| "The spec was unchanged, I skipped to step 7 already" | Good — but you still need to write the status. The fingerprint shortcut skips the validator agent, not the state update. |

After writing state.json, you MUST read it back and confirm `validation.status` is present.
If the read-back shows no `validation.status` field, the write failed — fix it before responding.
</HARD-GATE>

7. **Update state.json validation state**:
   a. Recompute SHA256 hashes and update `integrity_manifest`
   b. Update `referenced_codebase_files` and set `git_sha_start` to current HEAD
   c. **Determine status**:
      - No ERRORs found → `"pass"`
      - ERRORs found AND auto-fix resolved all of them → `"pass"`
      - ERRORs found AND `--no-fix` was used → `"fail"`
      - ERRORs found AND auto-fix failed to resolve some → `"fail"`
   d. Collect all WARNING-level findings from the validation report and write to state.json:
      ```json
      "validation": {
        "last_pass": "<ISO-8601>",
        "status": "pass|fail",
        "report_hash": "<SHA256 of full validation report>",
        "acknowledged_warnings": [
          "WARN-1: next-mdx-remote pin lacks version comment",
          "WARN-2: T-004 Covers field missing NFR-19/20/21 by number"
        ]
      }
      ```
   e. **Verify the write**: Read back `state.json` and confirm `validation.status` equals the value you intended to write. If it doesn't match, fix the file before proceeding.
   f. On subsequent runs, the acknowledged warnings are passed to the validator agent (step 4) to prevent rediscovery
