---
name: spec-release
description: Generate release notes, changelog, and deployment checklist
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-release Command

Prepare release artifacts with reproducibility manifest.

## Usage

```
/spec-release [spec-name] [--version-bump patch|minor|major] [--tag] [--release] [--force]
```

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"accepted"` (order >= 4)
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-release requires phase 'accepted' to be complete. Current phase: '<CURRENT>'. Run /spec-accept first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.

Note: Phase `'audited'` or `'documented'` also satisfy this requirement. The existing security gate (CRITICAL findings check) is separate.

## Workflow

1. Locate spec, read spec files and state.json
2. Generate `release.md` with:
   - Changelog (user-facing + technical changes)
   - Breaking changes with migration paths
   - Deployment checklist (pre/during/post)
   - Environment variables needed
   - Database migrations
   - Rollback plan
   - **Reproducibility manifest** from state.json: model versions used, git SHA range, plugin version
2.5. **Security Gate**: Read `state.json.security.findings.critical` (if `state.json.security` does not exist, treat as 0 and proceed):
   - IF `findings.critical` equals 0: proceed normally to step 3
   - IF `findings.critical` is greater than 0 AND `--force` is NOT provided:
     Display: "Release blocked: N unresolved CRITICAL security findings. Run /spec-security-audit to review."
     Stop here. Do not create a git tag or GitHub release.
   - IF `findings.critical` is greater than 0 AND `--force` IS provided:
     Append to audit log: `{ "event": "security_override", "action": "release forced", "critical_count": N }`
     Add a "## Security Override" section to release.md listing each unresolved CRITICAL finding from `evidence/security-audit.json` (if readable).
     Proceed to step 3.
3. If `--tag`: create git tag
4. If `--release`: create GitHub release via `gh release create`

After completing release artifacts (and tag/release if requested), set `state.json.phase` to `"released"`.
Log "Phase advanced to 'released'" to the audit log.
