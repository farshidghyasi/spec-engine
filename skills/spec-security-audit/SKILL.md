---
name: spec-security-audit
description: Run a comprehensive 15-phase security audit on a spec's implementation
argument-hint: "<spec-name> [--comprehensive]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-security-audit Command

Run a comprehensive 15-phase CSO security audit on a spec's implementation. Scoped to files changed since the spec began.

## Usage

```
/spec-security-audit [spec-name] [--comprehensive]
```

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"executed"` (order 3)
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-security-audit requires phase 'executed' to be complete. Current phase: '<CURRENT>'. Run /spec-exec (or /spec-loop or /spec-team) first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.

Note: Both `/spec-accept` and `/spec-security-audit` require `'executed'` and may run in either order.

## Workflow

### Step 1: Locate Spec and Read State

1. Validate that `.claude/specs/<spec-name>/` exists. If not: display "Spec '<spec-name>' not found in .claude/specs/. Run /spec-dashboard to list available specs." and stop.
2. Read `.claude/specs/<spec-name>/state.json`.
3. Extract `reproducibility.git_sha_start`. If null or missing, the audit will cover the full codebase.
4. Check if `evidence/security-audit.json` exists (Glob) — used for trend comparison in Phase 13.

### Step 2: Determine Audit Mode

- Default: `mode = "daily"`, confidence gate = 8/10
- If `--comprehensive` flag provided: `mode = "comprehensive"`, confidence gate = 2/10

### Step 3: Dispatch spec-security-auditor Agent

Dispatch the **spec-security-auditor** agent (via Agent tool) with:
- Spec directory path
- `git_sha_start` value (or null)
- `mode` ("daily" or "comprehensive")
- `previous_audit_path` (path to prior `evidence/security-audit.json` if it exists, else null)

If the agent crashes or times out:
- Append to audit log: `{ "event": "security_audit_failed", "reason": "<error>" }`
- Display: "Security audit failed. Check state.json audit_log for details."
- Do NOT block re-running.

### Step 4: Persist Agent Output

The spec-security-auditor agent is read-only with respect to file writing (it has Bash for audit commands but no Write tool). After the agent completes:

1. Extract the `AUDIT_REPORT_JSON` code block from the agent's response
2. Write it to `${SPEC_DIR}/evidence/security-audit.json`
3. Extract the `STATE_UPDATE_JSON` code block from the agent's response
4. Read `${SPEC_DIR}/state.json`, merge the security state update, and write it back (read-modify-write)

### Step 5: Display Results

Show the user a summary including:
- Mode (daily or comprehensive)
- Git range audited
- Posture score (0-100)
- Finding counts by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Filtered count (findings below confidence threshold)

If CRITICAL findings exist, display each with:
- File path and line reference
- Description
- Recommended fix

Show footer: "Report written to: evidence/security-audit.json"

After displaying results, set `state.json.phase` to `"audited"`.
Log "Phase advanced to 'audited'" to the audit log.
