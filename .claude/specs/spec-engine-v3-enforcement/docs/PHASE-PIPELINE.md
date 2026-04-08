# Phase Pipeline Reference

## Pipeline Diagram

```
/spec
  |
  v
[ phase: "spec" ]
  |
/spec-validate
  |
  v
[ phase: "validated" ]
  |
/spec-exec  OR  /spec-loop  OR  /spec-team
  |
  v
[ phase: "executed" ]
  |         \
  |          \
/spec-accept  /spec-security-audit
  |                  |
  v                  v
[ phase:          [ phase:
  "accepted" ]      "audited" ]
  |
  v (requires "accepted"; audit handled internally by release gate)
/spec-docs
  |
  v
[ phase: "documented" ]
  |
/spec-release
  |
  v
[ phase: "released" ]
  |
/spec-verify
  |
  v
[ phase: "verified" ]
  |
/spec-retro
  |
  v
[ phase: "retro" ]
```

Notes:
- `/spec-accept` and `/spec-security-audit` both require `"executed"` and can run in either order.
- `/spec-docs` only requires `"accepted"`, not `"audited"`. The release skill has its own security gate (`findings.critical` check) that handles the audit requirement.
- `/spec-retro` accepts either `"verified"` or `"released"` as its prerequisite.

---

## Phase Values

| Value | Set by | Numeric rank |
|-------|--------|-------------|
| `null` | Template default (new spec, pre-/spec completion) | 0 |
| `"spec"` | `/spec` | 1 |
| `"validated"` | `/spec-validate` | 2 |
| `"executed"` | `/spec-exec`, `/spec-loop`, `/spec-team` | 3 |
| `"accepted"` | `/spec-accept` | 4 |
| `"audited"` | `/spec-security-audit` | 4 |
| `"documented"` | `/spec-docs` | 5 |
| `"released"` | `/spec-release` | 6 |
| `"verified"` | `/spec-verify` | 7 |
| `"retro"` | `/spec-retro` | 8 |

The phase gate compares these numeric ranks. A skill at rank N requires the current phase to be at rank N-1 or higher.

---

## Prerequisite Map

| Command | Required phase | Blocked if current phase is |
|---------|---------------|----------------------------|
| `/spec-validate` | `"spec"` (rank 1) | `null` |
| `/spec-exec` | `"validated"` (rank 2) | `null`, `"spec"` |
| `/spec-loop` | `"validated"` (rank 2) | `null`, `"spec"` |
| `/spec-team` | `"validated"` (rank 2) | `null`, `"spec"` |
| `/spec-accept` | `"executed"` (rank 3) | anything below rank 3 |
| `/spec-security-audit` | `"executed"` (rank 3) | anything below rank 3 |
| `/spec-docs` | `"accepted"` (rank 4) | anything below rank 4 |
| `/spec-release` | `"accepted"` (rank 4) | anything below rank 4 |
| `/spec-verify` | `"released"` (rank 6) | anything below rank 6 |
| `/spec-retro` | `"verified"` or `"released"` (rank 6+) | anything below rank 6 |

---

## Phase Gate Error Format

When a prerequisite is not met, the skill displays:

```
Phase gate: /spec-exec requires phase 'validated' to be complete. Current phase: 'spec'. Run /spec-validate first.
```

The message never exposes `state.json` internal field names, filesystem paths, or stack traces.

---

## Dependency Gate (cross-spec)

`/spec-exec`, `/spec-loop`, and `/spec-team` check cross-spec dependencies before starting. The dependency gate runs after the phase gate.

A dependency is satisfied when its `state.json.phase` is at rank 4 or higher (`"accepted"`, `"audited"`, or later).

**Error format when dependency is not satisfied**:
```
Dependency gate: spec 'my-dep' is at phase 'executed', requires 'accepted'. Run /spec-accept my-dep first.
```

**Error format when dependency directory does not exist**:
```
Dependency gate: spec 'my-dep' not found in .claude/specs/.
```

Dependency spec names are validated to contain only alphanumeric characters, hyphens, and underscores. Names with `/`, `\`, or `..` are rejected.

---

## Reading the Current Phase

```bash
cat .claude/specs/<name>/state.json | grep '"phase"'
```

Or via `/spec-status`, which shows the current phase alongside token usage and task completion.

---

## Manually Setting Phase

If you need to resume an older spec or recover from a partial run, set `state.json.phase` directly:

```json
"phase": "executed"
```

Valid values: `null`, `"spec"`, `"validated"`, `"executed"`, `"accepted"`, `"audited"`, `"documented"`, `"released"`, `"verified"`, `"retro"`.

Setting an incorrect phase (e.g., `"accepted"` when tasks are not actually complete) bypasses the gate. Use with caution.
