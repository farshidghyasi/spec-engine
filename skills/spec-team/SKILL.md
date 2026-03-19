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
  - AskUserQuestion
---

# /spec-team Command

Execute spec implementation with a 4-agent team: Implementer, Tester, Reviewer, Debugger.

## Usage

```
/spec-team [spec-name] [--max-iterations N]
```

## When to Use

Use `/spec-team` instead of `/spec-loop` when:
- Tasks were being marked complete without real testing
- You need security/quality review before commits
- The feature is complex or security-sensitive
- You want separation of concerns (writer is not the tester)

## Token Cost

Agent teams use ~2-3x more tokens than single-agent mode because each agent has its own context. The **handoff file protocol** reduces this from the old plugin's 4x overhead.

## Team Roles

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| Implementer | Sonnet | Writes code + persistent tests | Read, Write, Edit, Glob, Grep, Bash |
| Tester | Sonnet | Verifies + error-path tests + screenshots | Read, Write, Glob, Grep, Bash, Playwright |
| Reviewer | Opus | Read-only review + persisted reports | Read, Glob, Grep |
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

For each task:

### Phase 1: Implementation
1. Read state.json, pick next pending task
2. Spawn Implementer with task context
3. Implementer writes code, tests, produces handoff file
4. Run quality gates (lint, typecheck, regression)
5. If gates fail: Spawn Debugger (max 2 retries)

### Phase 2: Testing
6. Spawn Tester with task context + implementer's handoff
7. Tester checks integration, runs tests, checks error paths, takes screenshots
8. Tester writes handoff file with results
9. If FAIL: Spawn Debugger with tester's handoff, then re-test (max 2 attempts)

### Phase 3: Review
10. Spawn Reviewer with task context + tester's handoff + git diff
11. Reviewer checks security, quality, architecture
12. Reviewer writes review report to `evidence/reviews/`
13. If REJECTED: Spawn Debugger with reviewer's feedback, then re-review (max 2 attempts)

### Phase 4: Commit
14. Update state.json: task completed, tokens used, audit log
15. Commit with descriptive message
16. Move to next task

## Escalation

If Debugger fails twice on the same issue:
- Mark task as failed in state.json (increment failures count)
- If failures >= 3: pause for human input
- Otherwise: move to next task, come back later

## Completion

When ALL tasks have status "completed" in state.json:
- Present summary with quality metrics
- Suggest next steps: /spec-accept, /spec-docs, PR creation
