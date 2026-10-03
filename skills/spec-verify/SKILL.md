---
name: spec-verify
description: Run post-deployment smoke tests against a live environment
argument-hint: "[spec-name] --url <target-url> [--scope full|quick]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-verify

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. `$SS phase-gate <spec> released` (stop with its message on failure).
2. Validate the URL: `^https?://[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+$`. Reject anything else.
3. Health check: the URL must answer HTTP 200 (`curl -sS -o /dev/null -w '%{http_code}'`).
4. Smoke tests: `quick` (default) loads the app and key routes and checks for errors; `full` exercises
   the browser-accessible acceptance criteria from requirements.md (Playwright via `npx playwright`
   when the project has it, otherwise curl).
5. Write `verification.md` to the spec dir with PASS/FAIL per check, then report the overall result.
6. `$SS phase <spec> verified`.
