# Migration Guide: spec-engine v3 Enforcement Enhancements

## Backward Compatibility Summary

These changes are backward compatible. No existing spec files need to be edited before running pipeline commands. The two new behaviors applied to older specs are described below.

---

## Existing Specs (created before this change)

### Missing `phase` field

Older `state.json` files do not have a `phase` field.

**Behavior**: Every pipeline skill treats a missing `phase` field as `"spec"`. A warning is logged to the audit log: `"Phase field missing, defaulting to 'spec'"`.

**What this means in practice**:

| You want to run | Phase required | Older spec starts at | Result |
|-----------------|---------------|----------------------|--------|
| `/spec-validate` | `"spec"` | `"spec"` (default) | Allowed |
| `/spec-exec` / `/spec-loop` / `/spec-team` | `"validated"` | `"spec"` (default) | Blocked — run `/spec-validate` first |
| `/spec-accept` | `"executed"` | `"spec"` (default) | Blocked |
| `/spec-docs` | `"accepted"` | `"spec"` (default) | Blocked |

**To unblock an existing spec that has already completed execution**: manually set `state.json.phase` to the appropriate value, then continue.

```json
// After confirmed-complete execution, to unblock /spec-accept:
"phase": "executed"

// After confirmed acceptance, to unblock /spec-docs:
"phase": "accepted"
```

There is no command to retroactively advance phase — it is a JSON field you edit directly.

### Missing `acceptance` field

Older `state.json` files do not have an `acceptance` field.

**Behavior**: The field is silently absent. `/spec-accept` will create it when it writes the acceptance report. No error is produced if it is missing at startup.

---

## New Specs (created after this change)

New specs created via `/spec` get both fields automatically from `templates/state.json`:

```json
"phase": null,
"acceptance": {
  "status": null,
  "estimated_fix_rounds": null
}
```

`phase` starts as `null` (not `"spec"`). `/spec` sets it to `"spec"` at the end of the spec-creation workflow. The phase gate checks treat `null` the same as `"spec"` (below `"validated"`).

---

## New Evidence Files Produced

After this change, the following new files may appear in a spec's `evidence/` directory:

| File | Produced by | Description |
|------|-------------|-------------|
| `evidence/wiring-wave-N.md` | `/spec-exec`, `/spec-loop`, `/spec-team` | Grep-based wiring verification results per wave |
| `evidence/pre-acceptance-lint.txt` | `/spec-accept` | Full-project lint output |
| `evidence/pre-acceptance-security-scan.txt` | `/spec-accept` | Vulnerability pattern grep results |
| `evidence/doc-audit.md` | `/spec-accept` (via spec-documenter) | Documentation coverage audit |

These files are informational. Missing evidence files do not block the pipeline (the pre-acceptance steps degrade gracefully on failure), but absent `wiring-wave-N.md` files are flagged as gaps in the acceptance report.

---

## Cross-Spec Dependencies

If your spec's `requirements.md` has a `## Depends On` section, execution will now block if the listed dependency specs are not at phase `"accepted"` or later. This was previously only enforced by the shell scripts (`scripts/lib/deps.sh`); it is now also enforced in the skill instructions.

To check the phase of a dependency spec:

```bash
cat .claude/specs/<dep-name>/state.json | grep '"phase"'
```

---

## No Action Required For

- Specs with no cross-spec dependencies
- Specs where you run commands in the standard order (`/spec` -> `/spec-validate` -> `/spec-exec` -> `/spec-accept` -> `/spec-docs` -> `/spec-release` -> `/spec-verify` -> `/spec-retro`)
- Shell scripts in `scripts/` — these are unchanged; enforcement is in the skill and agent markdown files
- `plugin.json` — unchanged
