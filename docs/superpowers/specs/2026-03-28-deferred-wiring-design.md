# Deferred Wiring Lifecycle

**Problem**: The `Wired: pending -> yes` lifecycle assumes the task executor does the wiring. When the wire target (e.g., router, navigation config) is a shared file owned by a different task in a later wave, the executing task cannot mark itself wired — creating zombie tasks that block wave advancement and deadlock the spec.

**Root cause**: Three contradictory rules:
1. Tasker Phase Structure (Phase 2 = Core, Phase 3 = Integration) encourages split-wiring
2. Tasker File Ownership ("Files array MUST include Wire-into target") expects self-wiring
3. Shared Files Registry ("Router/navigation files NEVER owned by single parallel tasks") prevents self-wiring

**Solution**: Add a `deferred` wired state with explicit cross-task resolution.

## 1. Wired State Machine

Current:
```
pending -> yes      (grep confirms import chain)
pending -> n/a      (infra task, nothing to wire)
yes -> pending      (downgrade: grep finds zero imports)
```

New:
```
pending -> yes              (grep confirms import chain)
pending -> n/a              (infra task, nothing to wire)
pending -> deferred(T-X)    (wire target owned by T-X in a later wave)
deferred(T-X) -> yes        (T-X completed, grep confirms import)
deferred(T-X) -> pending    (T-X completed, grep finds zero imports — T-X failed to wire)
yes -> pending              (downgrade: grep finds zero imports)
```

### Rules

- Only the **tasker** or **implementer** may set `deferred` — not self-reported post-hoc
- Tasker sets it when the wire target is a shared file or owned by a different task
- Implementer sets it when wire target is outside file boundaries and a downstream task owns it
- **Wave advancement**: `deferred` does not block (treated like `n/a`)
- **Task completion**: a task with `deferred` is completable (unlike `pending`)
- **Spec completion**: any task still `deferred` at end is an error — every `deferred` must resolve to `yes` or `pending`

### state.json Representation

Separate `wired` and `wired_by` fields (no string-embedded task ID):

```json
{
  "T-3": {
    "status": "completed",
    "wired": "deferred",
    "wired_by": "T-7",
    "wave": 1,
    "failures": 0,
    "files": ["src/components/RefundDialog.tsx", "tests/RefundDialog.test.ts"]
  }
}
```

## 2. Tasker Changes

### Detection

When assigning Wire-into targets:
1. Wire target in task's own Files array -> normal self-wiring (no change)
2. Wire target is shared file or owned by a different task -> set `Wired: deferred(T-X)`

### Integration Tasks

Phase 3 integration tasks gain a `Resolves` field listing upstream task IDs whose deferred wiring they complete. Their description must name each upstream task and its export, and their acceptance criteria must include grep confirmation.

### Example

```markdown
### T-3: Build RefundDialog component
- **Status**: pending
- **Wave**: 1
- **Wired**: deferred(T-7)
- **Wire into**: src/app/routes.tsx (router)
- **Files**: src/components/RefundDialog.tsx, tests/RefundDialog.test.ts
- **Description**: Build the RefundDialog component. Wiring into the router
  is handled by T-7.

### T-7: Wire Phase 2 components into app router
- **Status**: pending
- **Wave**: 2
- **Wired**: pending
- **Wire into**: n/a (this IS the wiring task)
- **Resolves**: T-3, T-4, T-5
- **Files**: src/app/routes.tsx, src/app/navigation.tsx
- **Description**: Import and register RefundDialog (T-3), PaymentHistory (T-4),
  and ExportButton (T-5) in the app router.
  AC: grep confirms all three exports are imported in routes.tsx.
```

### Self-Validation Check 7

- For every task with `Wired: deferred(T-X)`: verify T-X exists, is in a strictly later wave (not same wave — same-wave tasks should self-wire or use sequential sub-batches), and lists the wire target in its Files array
- For every task with `Resolves`: verify each resolved task has `Wired: deferred` pointing back to this task

## 3. Implementer Changes

### Behavior

- If the task already has `Wired: deferred(T-X)` set by tasker: respect it. Do not attempt to wire. Complete the task with `deferred` intact.
- If the task has `Wired: pending` but wire target is outside file boundaries: check if a downstream task has a `Resolves` field listing this task. If yes, set `Wired: deferred(T-X)`. If no, set `Wired: pending` and note in handoff (tasker oversight).

### Line 64 Fix

Current: "pending — Not yet wired (do NOT leave a task in this state when completing it)"

New: "pending — Not yet wired (do NOT leave a task in this state when completing unless the wire target is outside your file boundaries and no resolving task exists — this indicates a tasker bug)"

### Handoff File

When completing with `Wired: deferred`, the handoff file must include:
- Exact export name(s) the resolving task needs to import
- File path containing the export
- Expected wire target

## 4. Orchestration Changes

Applies to spec-loop, spec-exec, and spec-team identically.

### 4a. Wave Advancement Gate

Relax the block: `deferred` does not block wave advancement. Only `pending` blocks.

Current: "Do not advance to the next wave if wired-pending tasks exist that should be wired."

New: "Do not advance to the next wave if wired-pending tasks exist that should be wired. Deferred tasks do not block."

### 4b. Post-Wave Wiring Resolution Pass

New mandatory step after the existing grep-based wired verification:

```
WIRING RESOLUTION PASS

For each task T-X that completed in this wave and has a `Resolves` field:
  For each upstream task ID in T-X.Resolves:
    1. Read the upstream task's primary export name (from tasks.md or handoff file)
    2. Grep the codebase for imports of that export
    3. If imports found:
       - Set upstream task wired: "yes", clear wired_by
       - Log: "DEFERRED RESOLVED: T-3 export 'RefundDialog' wired by T-7,
               confirmed import in src/app/routes.tsx"
    4. If zero imports found:
       - Set upstream task wired: "pending", clear wired_by
       - Log: "DEFERRED FAILED: T-7 was supposed to wire T-3 but grep
               found 0 imports. T-3 downgraded to pending."
       - Normal retry/debugger flow kicks in for T-3
```

### 4c. End-of-Spec Safety Net

At spec completion, before declaring success: scan for any tasks still `wired: "deferred"`. Treat as error — the resolving task completed but resolution pass missed them.

## 5. Downstream Agent Changes

### spec-tester
- `pending`: reports WIRING INCOMPLETE (no change)
- `deferred`: test in isolation (unit tests), skip integration/reachability tests. Note: "Wiring deferred to T-X, integration testing deferred."

### spec-reviewer
- Accept `deferred` as valid alongside `yes` and `n/a`.

### spec-acceptor
- Traceability matrix: verify every formerly-deferred task resolved to `yes` by spec completion. Any still `deferred` is a P0 blocker.
- Verify grep evidence exists in audit log (DEFERRED RESOLVED entry) for each.

### spec-validator
- Check: every `deferred(T-X)` has a corresponding task T-X with `Resolves` listing the deferred task. Bidirectional consistency required.
- Severity: ERROR (auto-fixable).

### templates/tasks.md and references/task-breakdown.md
- Add `deferred` to wired state documentation
- Add `Resolves` to optional task fields
- Update lifecycle diagram

## Files to Modify

| File | Change |
|------|--------|
| `agents/spec-tasker.md` | Detection logic, Resolves field, Self-Validation Check 7 |
| `agents/spec-implementer.md` | Deferred handling, line 64 fix, handoff requirements |
| `agents/spec-tester.md` | Accept deferred state, isolation testing |
| `agents/spec-reviewer.md` | Accept deferred as valid state |
| `agents/spec-acceptor.md` | Deferred resolution audit in traceability matrix |
| `skills/spec-loop/SKILL.md` | Relaxed gate, wiring resolution pass, end-of-spec check |
| `skills/spec-exec/SKILL.md` | Same as spec-loop |
| `skills/spec-team/SKILL.md` | Same as spec-loop |
| `templates/tasks.md` | Document deferred state and Resolves field |
| `references/task-breakdown.md` | Document deferred state and Resolves field |
| `agents/spec-validator.md` | Bidirectional consistency check |
