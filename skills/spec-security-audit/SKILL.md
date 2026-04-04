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

### Step 4: Handle Agent Completion

Read `evidence/security-audit.json` and `state.json.security` after agent completes.

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
