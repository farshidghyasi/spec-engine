---
name: spec-ship
description: Ship an accepted spec in one go — docs, release artifacts (security gate), optional smoke test, retrospective
argument-hint: "[spec-name] [--tag] [--release] [--version-bump patch|minor|major] [--url <url>] [--force]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-ship

Everything after acceptance, without stopping between steps. Runs the four tail skills in order and
records each phase, so `/spec-docs`, `/spec-release`, `/spec-verify` and `/spec-retro` remain usable on
their own but are no longer required.

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

## Procedure

1. `$SS phase-gate <spec> accepted` (`audited` also satisfies it). Stop with its message on failure.
2. **Docs**: follow the Workflow in `${CLAUDE_PLUGIN_ROOT}/skills/spec-docs/SKILL.md` (phase -> `documented`).
3. **Release**: follow the Workflow in `${CLAUDE_PLUGIN_ROOT}/skills/spec-release/SKILL.md`, passing
   through `--tag`, `--release`, `--version-bump`, `--force` (phase -> `released`). The security gate
   applies unchanged: CRITICAL findings stop here unless `--force`, and the override is logged.
   If the gate stops the run, report it and do not continue to steps 4-5.
4. **Verify** (only with `--url`): follow `${CLAUDE_PLUGIN_ROOT}/skills/spec-verify/SKILL.md`
   (phase -> `verified`). A FAIL is reported but does not block the retrospective.
5. **Retro**: follow `${CLAUDE_PLUGIN_ROOT}/skills/spec-retro/SKILL.md` (phase -> `retro`).
6. Print `$SS status <spec>` and list the artifacts written: `docs/`, `release.md`,
   `verification.md` (if any), `retro.md`, and the lessons appended to `.claude/specs/lessons.json`.

Never call AskUserQuestion. The only decision in this command is the security gate, and it is
expressed through `--force`.
