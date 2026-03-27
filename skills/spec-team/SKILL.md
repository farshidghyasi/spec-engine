---
name: spec-team
description: Execute spec with a coordinated agent team (Implementer, Tester, Reviewer, Debugger)
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# /spec-team Command

Execute spec implementation with a 4-agent team: Implementer, Tester, Reviewer, Debugger. Supports parallel implementation within waves for independent tasks.

## Usage

```
/spec-team [spec-name] [--max-iterations N] [--no-parallel]
```

## When to Use

Use `/spec-team` instead of `/spec-loop` when:
- Tasks were being marked complete without real testing
- You need security/quality review before commits
- The feature is complex or security-sensitive
- You want separation of concerns (writer is not the tester)

## Token Cost

Agent teams use ~2-3x more tokens than single-agent mode because each agent has its own context. The **handoff file protocol** reduces this from the old plugin's 4x overhead. Parallel execution adds marginal overhead but reduces wall-clock time.

## Team Roles

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| Implementer | Sonnet | Writes code + persistent tests + wiring | Read, Write, Edit, Glob, Grep, Bash |
| Tester | Sonnet | Checks wiring, verifies end-to-end + error paths | Read, Write, Glob, Grep, Bash, Playwright |
| Reviewer | Opus | Read-only review + cross-task consistency + persisted reports | Read, Glob, Grep |
| Debugger | Sonnet | Fixes issues (max 2 retries) | Read, Write, Edit, Glob, Grep, Bash |

## Handoff File Protocol

Agents communicate via lightweight handoff files instead of passing full context:

```
.claude/specs/<name>/handoffs/
  T-3-implementer.md   # ~200 tokens: files changed, wiring status, test locations
  T-3-tester.md        # ~200 tokens: pass/fail, evidence paths, error details
  T-3-reviewer.md      # ~200 tokens: approve/reject, issues list
```

Each agent receives:
- state.json summary (Layer 0: ~200 tokens)
- Their specific task description (Layer 1: ~200 tokens)
- Previous agent's handoff file (~200 tokens)
- Total per agent: ~600 tokens (vs ~6000 in old plugin)

## Team Workflow

### Per-Wave Execution

For each wave, the team processes tasks through a parallel-then-sequential pipeline:

#### Phase 0: Pre-Wave Setup

1. Read state.json, collect all pending tasks in the current wave
2. Record the current git SHA as `pre_wave_sha`
3. **Generate import manifest**: Scan completed task files from previous waves, extract all exports (functions, classes, types, constants) with exact names and file paths
4. **Build parallel groups** from file ownership (same algorithm as spec-loop):
   - Tasks with non-overlapping Files run in parallel
   - Tasks with file conflicts run sequentially after the parallel group

#### Phase 1: Parallel Implementation + Wiring

1. **For each parallel group**, spawn Implementer agents simultaneously:
   - If 1 task: spawn a single Implementer
   - If 2+ tasks: spawn parallel Implementers, each with `isolation: "worktree"`
   - Each Implementer receives:
     - ONLY its assigned task and file boundaries
     - **Import manifest from completed waves** — exact export names and file paths. "Use EXACTLY these imports."
   - **All parallel Implementers are launched in a single message** (multiple Agent tool calls)
   - Each writes code, tests, wires it in, sets Wired field, produces handoff file


<HARD-GATE>
The FIRST thing you do after ANY agent completes is auto-commit its work.
Before checking wiring, before running gates, before merging — commit.
If you proceed to any other post-agent step without committing first,
you are violating this gate.
</HARD-GATE>

2. **Post-agent verification** (for each worktree, before merge):
   a. **Auto-commit**: `git add <task Files>` then `git commit -m "feat: T-{id} — {subject}"`
     **Auto-Commit Red Flags** — if you catch yourself thinking any of these, STOP:
     - "The agent probably committed" — It didn't. Every wave in a real run required manual commits. Always commit.
     - "I'll commit after the quality gates" — No. Commit first, then gates. If gates fail, you need the commit to diff against.
     - "There's nothing to commit" — Run `git status` in the worktree. If the agent produced no changes, that's a task failure, not a skip.
   b. **Shared file enforcement**: If agent modified any shared file, revert and log warning
   c. **Cross-agent import resolution**: Verify imports between parallel agents match actual exports. Fix mismatches directly or re-dispatch sequentially.

3. Merge parallel results back (sequentially, one worktree at a time)
4. Run **post-merge commands** — treat failures as blocking errors
5. Run quality gates in **diff mode** ONCE after all merges: lint, typecheck, regression (compare against baseline for pre-existing errors)
6. If gates fail: Spawn Debugger (max 2 retries)

#### Phase 2: Parallel Wiring Check + Testing

7. **For each completed task in the group**, spawn Tester agents:
   - If 1 task: spawn a single Tester
   - If 2+ tasks with non-overlapping test scope: spawn parallel Testers
   - Each Tester receives task context + its Implementer's handoff
   - Tester checks Wired field FIRST — if pending, reports WIRING INCOMPLETE
   - Tester checks integration, runs tests, checks error paths, takes screenshots
   - Tester writes handoff file with results

8. If any task fails testing:
   - If WIRING FAIL: Spawn Debugger to fix wiring, then re-test
   - If FUNCTIONAL FAIL: Spawn Debugger with tester's handoff, then re-test (max 2 attempts)

#### Phase 3: Wave Review (SEQUENTIAL — Opus)

9. **After ALL tasks in the wave pass testing**, spawn a SINGLE Reviewer for the entire wave:
   - Reviewer receives: all task contexts + all tester handoffs + full git diff for the wave
   - Reviewer checks security, quality, architecture for each task
   - **Reviewer ALSO checks cross-task consistency**:
     - Do parallel-implemented components interact correctly?
     - Are shared interfaces consistent across tasks?
     - Do error handling patterns match across the wave?
     - Are naming conventions consistent?
   - Reviewer writes one review report per task to `evidence/reviews/`
   - If any task REJECTED: Spawn Debugger with reviewer's feedback, then re-review (max 2 attempts)

**Why review is sequential**: The Opus reviewer needs to see the full wave's changes together to catch cross-task inconsistencies that per-task review would miss. This is the consistency safety net for parallel execution.

#### Phase 4: Post-Wave Verification

10. **Integration smoke test**: If `state.json.quality_gates.integration_cmd` is configured, run it. On failure: roll back to `pre_wave_sha`, re-run wave sequentially.
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

#### Phase 5: Commit

12. Update state.json: all wave tasks completed, tokens used, audit log
13. Commit with descriptive message listing all task IDs
14. Move to next wave

## Escalation

If Debugger fails twice on the same issue:
- Mark task as failed in state.json (increment failures count)
- If failures >= 3: log "AUTO-SKIP: T-X after 3 failures" to audit log, mark task as "skipped", continue to next task. Do NOT ask the user.
- Otherwise: move to next task, come back later

## Completion

When ALL tasks have status "completed" AND wired is "yes" or "n/a" in state.json:
- Present summary with quality metrics, wiring health, and parallel execution stats
- Suggest next steps: /spec-accept, /spec-docs, `gh pr create --head spec/<name>`
