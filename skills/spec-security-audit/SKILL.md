---
name: spec-security-audit
description: Run a comprehensive 15-phase security audit on a spec's implementation
argument-hint: "[spec-name] [--comprehensive]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-security-audit

15-phase CSO audit scoped to files changed since the spec began. Default mode `daily` (confidence
gate 8/10); `--comprehensive` lowers the gate to 2/10.

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

## Workflow

1. `$SS phase-gate <spec> executed` (stop with its message on failure).
2. Read `git_sha_start` via `$SS get <spec> reproducibility.git_sha_start` (null means audit the full
   codebase) and check whether `evidence/security-audit.json` exists (trend comparison).
3. Dispatch `spec-security-auditor` with the spec dir, `git_sha_start`, the mode and the previous
   report path or null. On crash: `$SS log <spec> security_audit_failed --details "<error>"`, tell the
   user, stop (re-running is allowed).
4. The agent has no Write tool. Extract its `AUDIT_REPORT_JSON` block to `evidence/security-audit.json`
   and apply its `STATE_UPDATE_JSON` block with `$SS set <spec> security.posture_score N`,
   `security.last_audit_date`, and `security.findings '{...}'`.
5. Show: mode, git range, posture score, counts by severity, filtered count, and each CRITICAL finding
   with file:line, description and fix. Footer: "Report written to: evidence/security-audit.json".
6. `$SS phase <spec> audited`.
