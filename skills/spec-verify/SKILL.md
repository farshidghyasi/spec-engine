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

## Workflow

1. Validate URL format: must be `https?://[safe characters]`
2. Locate spec, read requirements and design
3. Health check: verify URL responds with HTTP 200
4. Smoke tests based on scope:
   - **quick**: App loads, key routes respond, no errors
   - **full**: Test browser-accessible acceptance criteria via Playwright
5. Write verification report to `.claude/specs/<name>/verification.md`
6. Report PASS or FAIL
