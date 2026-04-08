# Release: spec-engine-v3-enforcement

## Version: 2.3.0 (minor — new enforcement features, backward compatible)

## Changelog

### Phase Gates (P0)
- Every pipeline skill now checks `state.json.phase` before executing
- Pipeline ordering enforced: spec → validate → exec → accept → docs → release → verify → retro
- Cross-spec dependency gate added to spec-exec, spec-loop, spec-team (verifies deps are accepted)
- Backward compatible: missing `phase` field treated as `"spec"`

### Orchestrator Improvements (P0-P1)
- Auto-format runs after every agent merge, before quality gates (biome/prettier/eslint auto-detected)
- state.json updates are now atomic per-task (same commit as implementation)
- Wiring verification writes evidence files (`evidence/wiring-wave-N.md`) and blocks on pending
- Fresh inline validation runs at spec-exec/spec-loop startup (no stale specs)
- Shared file isolation: tasks owning shared files auto-moved to sequential batches
- Token budget auto-calculated as `tasks × 50000` (manual override preserved)

### Agent Hardening (P1)
- Anti-deferral rule added to 4 agents (implementer, tester, debugger, acceptor)
- Types-first Wave 0 enforcement: validator ERRORs if 5+ task spec lacks types in Wave 0
- Deprecated field sweep enforcement upgraded from WARNING to ERROR
- Fix budget estimation added to acceptor (estimates iteration rounds for rejected specs)
- Documenter audit mode: read-only scan for documentation gaps

### Pre-Acceptance Quality Gates (P2)
- Full-project lint before acceptance (not just per-wave deltas)
- Lightweight security grep scan (secrets, SQL injection, XSS, insecure crypto)
- Documentation audit via spec-documenter in read-only mode

## Breaking Changes

None. All changes are additive. Existing specs without the `phase` field default to `"spec"` and can proceed through the pipeline normally.

## New state.json Fields

- `phase`: string | null — tracks pipeline position (null → "spec" → "validated" → ... → "retro")
- `acceptance.status`: string | null — "accepted" or "not_accepted"
- `acceptance.estimated_fix_rounds`: integer | null — estimated fix iterations

## Deployment Checklist

- [ ] Pull latest changes
- [ ] No database migrations (markdown-only plugin)
- [ ] No environment variables needed
- [ ] Verify plugin loads: run any `/spec-status` command

## Rollback Plan

```bash
git revert HEAD~5..HEAD  # Reverts all 5 commits in this release
```

Existing state.json files with the new `phase` field are harmless — unknown fields are ignored by older skill versions.

## Reproducibility Manifest

- Plugin version: 2.2.0 → 2.3.0
- Git SHA range: 36267ca..3bcfac6
- Models used: Claude Opus 4.6 (planning, acceptance), Claude Sonnet 4.6 (implementation)
- Spec tasks: 14 tasks, 3 waves, 5 commits
