# Enforcement Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden spec-engine enforcement for wiring verification and auto-commit using superpowers-style HARD-GATEs and red flags, add signature change propagation rules, and add UX interaction pattern question to brainstorm.

**Architecture:** Pure text edits to 6 existing markdown files. No new files, no schema changes, no code. Each task is an independent edit to one file.

**Tech Stack:** Markdown (skill and agent definition files)

---

### Task 1: Harden wiring verification in spec-loop

**Files:**
- Modify: `skills/spec-loop/SKILL.md:312-335` (step 2e.2 wiring verification)

- [ ] **Step 1: Add HARD-GATE before step 2e.2**

Insert immediately before line 313 (`2. **MANDATORY: Grep-based wired verification**`):

```markdown
<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>
```

- [ ] **Step 2: Add red flags after step 2e.2**

Insert immediately after line 335 (`e. **This check is blocking**...`), before line 337 (`3. **Stuck detection**`):

```markdown
   **Wiring Verification Red Flags** — if you catch yourself thinking any of these, STOP:

   - "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
   - "I already checked this in a previous wave" — Check again. Code changes between waves.
   - "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
   - "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
   - "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -c "HARD-GATE" skills/spec-loop/SKILL.md`
Expected: At least 1

Run: `grep -c "Wiring Verification Red Flags" skills/spec-loop/SKILL.md`
Expected: 1

- [ ] **Step 4: Commit**

```bash
git add skills/spec-loop/SKILL.md
git commit -m "fix: add HARD-GATE and red flags for wiring verification in spec-loop"
```

---

### Task 2: Harden auto-commit in spec-loop

**Files:**
- Modify: `skills/spec-loop/SKILL.md:189-197` (step 2d.4 post-agent verification)

- [ ] **Step 1: Add HARD-GATE before step 2d.4**

Insert immediately before line 189 (`4. **Post-agent verification**`):

```markdown
<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>
```

- [ ] **Step 2: Add red flags after the auto-commit sub-step**

Insert immediately after line 197 (`Only add files listed in the task's Files array — do not `git add -A`.`), before line 199 (`b. **Shared file enforcement**`):

```markdown
      **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:

      - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
      - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
      - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -c "HARD-GATE" skills/spec-loop/SKILL.md`
Expected: At least 2 (one from Task 1, one from this task)

Run: `grep -c "Auto-Commit Red Flags" skills/spec-loop/SKILL.md`
Expected: 1

- [ ] **Step 4: Commit**

```bash
git add skills/spec-loop/SKILL.md
git commit -m "fix: add HARD-GATE and red flags for auto-commit in spec-loop"
```

---

### Task 3: Harden wiring verification and auto-commit in spec-exec

**Files:**
- Modify: `skills/spec-exec/SKILL.md:81-82` (step 4 post-agent verification, auto-commit)
- Modify: `skills/spec-exec/SKILL.md:118-120` (step 5.6 wired status verification)

- [ ] **Step 1: Add auto-commit HARD-GATE before step 4 post-agent verification**

Insert immediately before line 81 (`- **Post-agent verification**`):

```markdown
<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>
```

- [ ] **Step 2: Add auto-commit red flags after step 4a**

Insert immediately after line 82 (`a. **Auto-commit**: `git add <task Files>` then `git commit -m "feat: T-{id} — {subject}"` in the worktree`):

```markdown
     **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:
     - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
     - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
     - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
```

- [ ] **Step 3: Replace step 5.6 with full wiring verification**

Replace the entire step 5.6 section (line 118-120):

```
### Step 5.6: Wired Status Verification

For each task marked `wired: "yes"`, verify the claim by grepping the app entry point for an import of the task's exports. If not found, downgrade to `wired: "pending"` and log a warning.
```

With:

```markdown
### Step 5.6: Wired Status Verification

<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>

For EACH task marked `wired: "yes"` in state.json:

1. **Identify the task's primary export**: Read the task's main output file and extract the exported name (function, component, class, constant).

2. **Grep the entire codebase for imports of that export**:
   ```bash
   grep -r "import.*ExportName" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ | grep -v "node_modules" | grep -v "<the_defining_file_itself>"
   ```

3. **Evaluate results**:
   - If **zero imports found outside the defining file**: Downgrade `wired` to `"pending"` in state.json. Append to audit log: `"WIRED DOWNGRADE: T-X export '<name>' has 0 imports in codebase."`
   - If imports found: Keep `wired: "yes"`. Log: `"WIRED VERIFIED: T-X export '<name>' imported by [file list]"`

4. **Pattern-specific checks**:
   - **API routes**: grep for import AND check app entry point for `.use()` or route registration
   - **React components**: grep for import AND check router/navigation config
   - **Services/utilities**: must have at least one call site outside the defining file
   - **Middleware**: grep for `.use()` pattern or imports

5. **This check is blocking**: A task with `wired: "pending"` is NOT complete. Do not advance to the next wave if wired-pending tasks exist that should be wired.

**Wiring Verification Red Flags** — if you catch yourself thinking any of these, STOP:

- "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
- "I already checked this in a previous wave" — Check again. Code changes between waves.
- "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
- "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
- "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.
```

- [ ] **Step 4: Verify the edits**

Run: `grep -c "HARD-GATE" skills/spec-exec/SKILL.md`
Expected: 2

Run: `grep -c "Red Flags" skills/spec-exec/SKILL.md`
Expected: 2

- [ ] **Step 5: Commit**

```bash
git add skills/spec-exec/SKILL.md
git commit -m "fix: add HARD-GATEs and red flags for wiring and auto-commit in spec-exec"
```

---

### Task 4: Harden wiring verification and auto-commit in spec-team

**Files:**
- Modify: `skills/spec-team/SKILL.md:89-92` (phase 1 step 2 post-agent verification)
- Modify: `skills/spec-team/SKILL.md:128-131` (phase 4 wired status verification)

- [ ] **Step 1: Add auto-commit HARD-GATE before phase 1 step 2**

Insert immediately before line 89 (`2. **Post-agent verification**`):

```markdown
<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>
```

- [ ] **Step 2: Add auto-commit red flags after step 2a**

Insert immediately after line 90 (`a. **Auto-commit**: `git add <task Files>` then `git commit -m "feat: T-{id} — {subject}"`):

```markdown
     **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:
     - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
     - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
     - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
```

- [ ] **Step 3: Replace phase 4 step 11 with full wiring verification**

Replace line 131 (`11. **Wired status verification**: For each task marked `wired: "yes"`, grep the app entry point for an import of the task's exports. Downgrade to `"pending"` if not found.`):

With:

```markdown
11. **Wired status verification**:

<HARD-GATE>
Do NOT mark any task as completed or advance to the next wave until you have run
the grep verification below and confirmed non-zero imports. An agent saying
"wired: yes" is not evidence. Grep output is evidence.
</HARD-GATE>

   For EACH task marked `wired: "yes"` in state.json:

   a. **Identify the task's primary export**: Read the task's main output file and extract the exported name.

   b. **Grep the entire codebase for imports of that export**:
   ```bash
   grep -r "import.*ExportName" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ | grep -v "node_modules" | grep -v "<the_defining_file_itself>"
   ```

   c. **Evaluate results**:
   - If **zero imports found outside the defining file**: Downgrade `wired` to `"pending"` in state.json. Append to audit log: `"WIRED DOWNGRADE: T-X export '<name>' has 0 imports in codebase."`
   - If imports found: Keep `wired: "yes"`. Log: `"WIRED VERIFIED: T-X export '<name>' imported by [file list]"`

   d. **Pattern-specific checks**:
   - **API routes**: grep for import AND check app entry point for `.use()` or route registration
   - **React components**: grep for import AND check router/navigation config
   - **Services/utilities**: must have at least one call site outside the defining file
   - **Middleware**: grep for `.use()` pattern or imports

   e. **This check is blocking**: A task with `wired: "pending"` is NOT complete. Do not advance to the next wave if wired-pending tasks exist that should be wired.

   **Wiring Verification Red Flags** — if you catch yourself thinking any of these, STOP:

   - "The agent said wired: yes" — Run the grep. Agent self-reports are wrong ~30% of the time.
   - "I already checked this in a previous wave" — Check again. Code changes between waves.
   - "It's an internal utility, nothing imports it" — Then it's dead code. Set wired: n/a with justification, or find the call site.
   - "The tests pass so it must be wired" — Tests run in isolation. Wired means reachable from the app entry point.
   - "I'll check wiring at the end" — Check per-wave. Deferring wiring checks is how 12 routes got marked wired:yes without being mounted.
```

- [ ] **Step 4: Verify the edits**

Run: `grep -c "HARD-GATE" skills/spec-team/SKILL.md`
Expected: 2

Run: `grep -c "Red Flags" skills/spec-team/SKILL.md`
Expected: 2

- [ ] **Step 5: Commit**

```bash
git add skills/spec-team/SKILL.md
git commit -m "fix: add HARD-GATEs and red flags for wiring and auto-commit in spec-team"
```

---

### Task 5: Add signature change rule to spec-tasker

**Files:**
- Modify: `agents/spec-tasker.md:45-46` (after Task Requirements, before Wave Assignment)

- [ ] **Step 1: Add Signature Change Rule section**

Insert immediately after line 45 (the last line of Task Requirements ending with `2. One error-path criterion (REQUIRED — what happens when things fail?)`), before line 46 (`## Wave Assignment`):

```markdown

## Signature Change Rule

If a task modifies an existing function's signature (adding/removing parameters, changing return type, sync to async, renaming), the task description MUST include:

1. The exact signature change: e.g., `functionName(a) -> functionName(a, b)` or `sync functionName() -> async functionName()`
2. A grep instruction: `grep -r "functionName" --include="*.ts" --include="*.tsx" src/`
3. An acceptance criterion: "All callers of functionName updated to new signature"
4. ALL known caller files added to the task's Files array

If the caller list might be incomplete, add to the description: "Run grep before implementing to discover all callers. Add any unlisted caller files to your scope and update them."
```

- [ ] **Step 2: Verify the edit**

Run: `grep -c "Signature Change Rule" agents/spec-tasker.md`
Expected: 1

- [ ] **Step 3: Commit**

```bash
git add agents/spec-tasker.md
git commit -m "feat: add signature change propagation rule to spec-tasker"
```

---

### Task 6: Add signature change protocol to spec-implementer

**Files:**
- Modify: `agents/spec-implementer.md:100-101` (after process step 3, before step 4)

- [ ] **Step 1: Add Signature Changes section**

Insert immediately after line 100 (`3. Read relevant existing code to understand patterns`), before line 101 (`4. **Plan the wiring path**`):

```markdown
3b. **Signature changes** — If your task changes any existing function's signature:
   - **Before implementing**: Run the grep command from the task description (or `grep -r "functionName" --include="*.ts" --include="*.tsx" src/` if none provided)
   - **Identify ALL callers** — not just the ones listed in the task
   - **Update every caller** — if a caller is outside your file boundaries, note it in your handoff file as `SIGNATURE BREAK: <file> calls <function> with old signature`
   - **Verify no remaining callers use old signature**: Re-run grep after changes, confirm zero hits for old pattern
```

- [ ] **Step 2: Verify the edit**

Run: `grep -c "Signature changes" agents/spec-implementer.md`
Expected: 1

Run: `grep -c "SIGNATURE BREAK" agents/spec-implementer.md`
Expected: 1

- [ ] **Step 3: Commit**

```bash
git add agents/spec-implementer.md
git commit -m "feat: add signature change protocol to spec-implementer"
```

---

### Task 7: Add UX interaction pattern question to spec-brainstorm

**Files:**
- Modify: `skills/spec-brainstorm/SKILL.md:76` (after "Are there existing patterns..." bullet, before "Have you considered..." bullet)

- [ ] **Step 1: Add interaction pattern bullet**

Insert immediately after line 76 (`- Have you considered [alternative approach]?`), keeping it as part of the same bullet list:

```markdown
- If the feature includes user-facing screens: What interaction pattern should each screen use? (page, modal, dialog, drawer, inline expansion, wizard) This matters most for screens users will hit frequently — getting it wrong means full rework. Ask early: "For [screen X], should this be a full page, a modal overlay, a dialog, or something else? Consider how often users will use it and what context they need to keep visible."
```

- [ ] **Step 2: Verify the edit**

Run: `grep -c "interaction pattern" skills/spec-brainstorm/SKILL.md`
Expected: 1

- [ ] **Step 3: Commit**

```bash
git add skills/spec-brainstorm/SKILL.md
git commit -m "feat: add UX interaction pattern question to spec-brainstorm"
```
