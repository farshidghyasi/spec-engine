---
name: spec-status
description: Show status and progress of current spec
argument-hint: "[spec-name]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# /spec-status

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py status [spec-name]
```

Print its output verbatim. Then add:

- **Dependencies**: if requirements.md has a `## Depends On` section, run `spec-state.py deps <spec>`
  and show the result.
- **Integrity**: `spec-state.py integrity <spec>` (VALID / MISMATCH).
- **Next step** from the phase: `spec` -> `/spec-validate`; `validated` -> `/spec-loop`;
  `executed` -> `/spec-accept` and `/spec-security-audit`; `accepted`/`audited` -> `/spec-docs`;
  `documented` -> `/spec-release`; `released` -> `/spec-verify`; `verified` -> `/spec-retro`.
- If any task shows 3+ failures: it has been auto-skipped; suggest `/spec-refine` to simplify it or a manual implementation.
