---
name: spec-release
description: Generate release notes, changelog, and deployment checklist
argument-hint: "[spec-name] [--version-bump patch|minor|major] [--tag] [--release] [--force]"
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

# /spec-release

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

1. `$SS phase-gate <spec> documented` (stop with its message on failure).
2. **Security gate**: `$SS get <spec> security.findings.critical`. If > 0 and no `--force`: print
   "Release blocked: N unresolved CRITICAL security findings. Run /spec-security-audit to review." and
   stop. With `--force`: `$SS log <spec> security_override --details "release forced, critical=N"` and
   add a `## Security Override` section to release.md listing each CRITICAL finding from
   `evidence/security-audit.json`.
3. Write `release.md`: changelog (user-facing and technical), breaking changes with migration paths,
   deployment checklist (pre/during/post), environment variables, database migrations, rollback plan,
   and a reproducibility manifest from state.json (plugin version, model versions, git SHA range).
4. `--tag`: create the git tag (`--version-bump` picks the increment). `--release`: `gh release create`.
5. `$SS phase <spec> released`.
