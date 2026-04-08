---
name: spec-verify
description: Run post-deployment smoke tests against a live environment
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-verify Command

Post-deployment smoke tests against a live URL.

## Usage

```
/spec-verify [spec-name] --url <target-url> [--scope full|quick]
```

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"released"` (order 6)
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-verify requires phase 'released' to be complete. Current phase: '<CURRENT>'. Run /spec-release first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.

## Workflow

1. Validate URL format: must be `https?://[safe characters]`
2. Locate spec, read requirements and design
3. Health check: verify URL responds with HTTP 200
4. Smoke tests based on scope:
   - **quick**: App loads, key routes respond, no errors
   - **full**: Test browser-accessible acceptance criteria via Playwright
5. Write verification report to `.claude/specs/<name>/verification.md`
6. Report PASS or FAIL

After reporting results, set `state.json.phase` to `"verified"`.
Log "Phase advanced to 'verified'" to the audit log.
