## User Acceptance Test Report: spec-engine-v3-enforcement

### Summary
- Total Acceptance Criteria: 74 (across 15 user stories + 5 NFRs)
- Passed: 72 | Failed: 1 | Partial: 1 | Untestable: 0
- **Overall: NOT ACCEPTED**

### Traceability Matrix

#### US-1: Pipeline Phase Gate (AC 1-18)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (phase check in 10 skills) | T-7, T-8, T-9, T-11, T-12, T-14 | completed | **PARTIAL** -- 10 of 11 skills have correct phase gates. `/spec-release` requires `"accepted"` (order 4) but per the phase order in AC-1, release follows docs, so it should require `"documented"` (order 5). This allows running release without docs. |
| AC-2 (error message) | T-7, T-8, T-9, T-11, T-12, T-14 | completed | PASS -- all skills display the correct phase gate error message format |
| AC-3 (spec sets phase) | T-10 | completed | PASS -- skills/spec/SKILL.md sets `state.json.phase` to `"spec"` |
| AC-4 (validate sets phase) | T-11 | completed | PASS -- skills/spec-validate/SKILL.md sets phase to `"validated"` |
| AC-5 (exec/loop/team set phase) | T-7, T-8, T-9 | completed | PASS -- all three set phase to `"executed"` |
| AC-6 (accept sets phase) | T-14 | completed | PASS -- skills/spec-accept/SKILL.md sets phase to `"accepted"` |
| AC-7 (security-audit sets phase) | T-12 | completed | PASS -- skills/spec-security-audit/SKILL.md sets phase to `"audited"` |
| AC-8 (docs sets phase) | T-12 | completed | PASS -- skills/spec-docs/SKILL.md sets phase to `"documented"` |
| AC-9 (release sets phase) | T-12 | completed | PASS -- skills/spec-release/SKILL.md sets phase to `"released"` |
| AC-10 (verify sets phase) | T-12 | completed | PASS -- skills/spec-verify/SKILL.md sets phase to `"verified"` |
| AC-11 (retro sets phase) | T-12 | completed | PASS -- skills/spec-retro/SKILL.md sets phase to `"retro"` |
| AC-12 (exec/loop/team require validated) | T-7, T-8, T-9 | completed | PASS |
| AC-13 (accept requires executed) | T-14 | completed | PASS |
| AC-14 (docs requires accepted) | T-12 | completed | PASS |
| AC-15 [inferred] (missing phase -> "spec") | T-7, T-8, T-9, T-11, T-12, T-14 | completed | PASS -- all phase gate sections include "If the field is absent, treat as `\"spec\"`" |
| AC-16 [inferred] (accept/audit either order) | T-14, T-12 | completed | PASS -- both require "executed" (order 3), independent of each other |
| AC-17 [inferred] (validate with absent phase) | T-11 | completed | PASS -- validate requires "spec" and missing = "spec", so always passes |
| AC-18 [threat-model] (no internal fields in errors) | T-7, T-8, T-9, T-11, T-12, T-14 | completed | PASS -- all phase gate sections include "Do NOT expose state.json field names, filesystem paths, or stack traces" |

#### US-2: Spec Dependency Gate (AC 1-6)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (dependency check) | T-7, T-8, T-9 | completed | PASS |
| AC-2 (error message) | T-7, T-8, T-9 | completed | PASS |
| AC-3 (missing dir) | T-7, T-8, T-9 | completed | PASS |
| AC-4 [inferred] (missing phase = not accepted) | T-7, T-8, T-9 | completed | PASS |
| AC-5 [inferred] (no depends-on = skip) | T-7, T-8, T-9 | completed | PASS |
| AC-6 [threat-model] (path traversal) | T-7, T-8, T-9 | completed | PASS -- all contain "alphanumeric characters, hyphens, and underscores" and path separator validation |

#### US-3: Auto-Format After Every Agent (AC 1-6)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (detect and run formatter) | T-7, T-8, T-9 | completed | PASS |
| AC-2 (no formatter = skip) | T-7, T-8, T-9 | completed | PASS |
| AC-3 (non-zero = proceed) | T-7, T-8, T-9 | completed | PASS |
| AC-4 (no --unsafe on tsx/jsx) | T-7, T-8, T-9 | completed | PASS |
| AC-5 [inferred] (empty file list = skip) | T-7, T-8, T-9 | completed | PASS |
| AC-6 [threat-model] (predefined commands only) | T-7, T-8, T-9 | completed | PASS -- all three contain "Execute ONLY the predefined command. Do NOT execute arbitrary" |

#### US-4: Atomic state.json Updates (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (state.json in same commit) | T-7, T-8, T-9 | completed | PASS |
| AC-2 (failures in rollback commit) | T-7, T-8, T-9 | completed | PASS |
| AC-3 (no deferral to wave boundary) | T-7, T-8, T-9 | completed | PASS |
| AC-4 (state.json in git add) | T-7, T-8, T-9 | completed | PASS |

#### US-5: Grep-Based Wiring Verification Evidence (AC 1-5)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (write evidence/wiring-wave-N.md) | T-7, T-8, T-9 | completed | PASS |
| AC-2 (WIRING HARD GATE blocks wave) | T-7, T-8, T-9 | completed | PASS |
| AC-3 (accept reads wiring evidence) | T-14 | completed | PASS |
| AC-4 (WIRING EVIDENCE GAP flag) | T-14 | completed | PASS |
| AC-5 (include grep command on fail) | T-7, T-8, T-9 | completed | PASS |

#### US-6: Types-First Wave 0 Enforcement (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (check Wave 0 for types task) | T-2 | completed | PASS |
| AC-2 (ERROR if missing) | T-2 | completed | PASS |
| AC-3 (skip for < 5 tasks) | T-2 | completed | PASS |
| AC-4 [inferred] (tasker enforcement) | T-3 | completed | PASS -- contains "required, not optional" and "validator will report an ERROR" |

#### US-7: Remove Deferral Escape Hatches (AC 1-2)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (anti-deferral in 4 agents) | T-4, T-5 | completed | PASS -- found in spec-implementer.md, spec-tester.md, spec-debugger.md, spec-acceptor.md |
| AC-2 (prohibited phrases) | T-4, T-5 | completed | PASS -- all 4 prohibited phrases found in all 4 agent files |

#### US-8: Full-Project Lint Before Acceptance (AC 1-6)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (run lint before acceptor) | T-14 | completed | PASS |
| AC-2 (write evidence file) | T-14 | completed | PASS |
| AC-3 (PASS: 0 lint errors) | T-14 | completed | PASS |
| AC-4 (null lint_cmd = skip) | T-14 | completed | PASS |
| AC-5 (command crash = proceed) | T-14 | completed | PASS |
| AC-6 [threat-model] (allowed_commands validation) | T-14 | completed | PASS -- contains "Validate lint_cmd against state.json.quality_gates.allowed_commands" |

#### US-9: Deprecated Field Sweep Enforcement (AC 1-3)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (verify sweep task exists) | T-2 | completed | PASS |
| AC-2 (ERROR if no sweep task) | T-2 | completed | PASS |
| AC-3 [inferred] (sweep Files coverage) | T-2 | completed | PASS |

#### US-10: Fresh Pre-Execution Validation (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (inline validation checks) | T-7, T-8 | completed | PASS |
| AC-2 (error + auto-fix + stop) | T-7, T-8 | completed | PASS |
| AC-3 (no prior validate required) | T-7, T-8 | completed | PASS |
| AC-4 [inferred] (log on pass) | T-7, T-8 | completed | PASS |

#### US-11: Shared File Isolation (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (move shared file tasks to sequential) | T-7, T-8, T-9 | completed | PASS |
| AC-2 (log SHARED FILE ISOLATION) | T-7, T-8, T-9 | completed | PASS |
| AC-3 (barrel reconciliation) | T-7, T-8, T-9 | completed | PASS |
| AC-4 [inferred] (debugger on conflict) | T-7, T-8, T-9 | completed | PASS |

#### US-12: Security Scan Per-Spec (AC 1-7)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (grep vulnerability patterns) | T-14 | completed | PASS |
| AC-2 (write evidence file) | T-14 | completed | PASS |
| AC-3 (PASS: 0 matches) | T-14 | completed | PASS |
| AC-4 (null git_sha = full scan) | T-14 | completed | PASS |
| AC-5 (grep error = continue) | T-14 | completed | PASS |
| AC-6 [threat-model] (no secret values in evidence) | T-14 | completed | PASS -- "Do NOT write matched line content. Do NOT write credential or secret values." |
| AC-7 [threat-model] (200-char truncation) | T-14 | completed | PASS -- "Truncate any surrounding context to 200 characters maximum." |

#### US-13: Token Budget Auto-Calculation (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (auto-calculate budget_cap) | T-10 | completed | PASS |
| AC-2 (display budget source) | T-13 | completed | PASS -- shows "(auto-calculated, N tasks x 50000)" |
| AC-3 (no overwrite manual) | T-10 | completed | PASS |
| AC-4 [inferred] (no recalculate) | T-10 | completed | PASS |

#### US-14: Post-Acceptance Fix Budget (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (estimated_fix_rounds in report) | T-5 | completed | PASS |
| AC-2 (update state.json.acceptance) | T-14 | completed | PASS |
| AC-3 [inferred] (0 for ACCEPTED) | T-5 | completed | PASS |
| AC-4 (create acceptance field) | T-1, T-14 | completed | PASS -- template has the field; spec-accept creates it if missing |

#### US-15: Documenter as Read-Only Quality Gate (AC 1-4)
| AC | Task(s) | Status | Result |
|----|---------|--------|--------|
| AC-1 (dispatch documenter in audit mode) | T-14 | completed | PASS |
| AC-2 (write evidence/doc-audit.md) | T-6 | completed | PASS |
| AC-3 (include in acceptor input, non-blocking) | T-14 | completed | PASS |
| AC-4 (failure = proceed) | T-6, T-14 | completed | PASS |

#### Non-Functional Requirements
| NFR | Result |
|-----|--------|
| NFR-1 (phase gate < 1s) | PASS -- reading a single JSON field is trivially fast |
| NFR-2 (validation < 5s for 30 tasks) | PASS -- inline BFS validation on in-memory data is fast |
| NFR-3 (missing phase = "spec") | PASS -- all phase gates include backward-compatible fallback |
| NFR-4 (missing acceptance = no error) | PASS -- template includes acceptance field; spec-accept creates if missing |
| NFR-5 (pre-acceptance steps degrade gracefully) | PASS -- lint, security scan, and doc audit all have failure-continue paths |

### Integration Health
- Tasks completed and wired (n/a): 14
- Tasks completed but NOT wired: 0 (all are n/a -- markdown/JSON edits)
- Tasks wired but NOT verified: 0

### Stale References
Stale reference check not applicable. This spec modifies markdown instruction files and a JSON template. No type definitions, schemas, or interfaces were renamed. No field renames detected in git diff.

### Gaps Found

**FAILED: US-1 AC-1 (spec-release phase gate)**
`/spec-release` has `Required phase: "accepted" (order >= 4)`, but per the phase order defined in AC-1 (`spec -> validate -> exec -> accept -> security-audit -> docs -> release -> verify -> retro`), `/spec-release` should require `"documented"` (order 5) since docs precedes release in the pipeline. The current implementation allows running `/spec-release` without `/spec-docs` having been completed. This same issue does NOT affect `/spec-docs` (correctly requires "accepted").

No orphan tasks found. All 14 tasks map to at least one requirement.
No unimplemented requirements found (all ACs have implementing tasks).

### Security Verification
- [security] criteria found: 1 (US-2 AC-6 baseline)
- [threat-model] criteria found: 6
- Criteria with implementing tasks: 7 (of 7 total)
- Security review evidence: 0 waves covered (3 completed waves) -- acceptable: markdown-only project with no runtime code
- Posture score: Not audited
- Threat model status: completed
- Result: PASS (all security criteria have implementing tasks; no security-review-wave files expected for non-code project)

### Non-Functional Requirements
- **Performance**: No concerns. All checks involve reading a single JSON file and comparing string values.
- **Accessibility**: Not applicable (no UI).
- **Data Integrity**: state.json template is valid JSON with all required fields. Atomic commit instructions are present in all execution skills.

### [inferred] Requirements Review
All 10 inferred requirements are valid and well-motivated:
- US-1 AC-15 (backward compat for missing phase): Essential for migration of existing specs
- US-1 AC-16 (accept/audit either order): Practical -- audit and accept are independent quality gates
- US-1 AC-17 (validate with absent phase): Correctly derived from AC-15 + AC-1
- US-2 AC-4 (missing phase = not accepted): Conservative and safe
- US-2 AC-5 (no depends-on = skip): Standard behavior
- US-3 AC-5 (empty file list = skip): Avoids no-op formatter invocations
- US-6 AC-4 (tasker reinforcement): Aligns tasker with validator expectation
- US-9 AC-3 (sweep Files coverage): Catches incomplete sweep tasks
- US-10 AC-4 (log on pass): Useful for debugging
- US-11 AC-4 (debugger on conflict): Provides automated resolution path
- US-13 AC-4 (no recalculate): Prevents budget surprises during execution
- US-14 AC-3 (0 for ACCEPTED): Clean state for accepted specs

All inferred requirements are valid and necessary.

### Human Review Items
None flagged. No evidence/reviews/ files found.

### Recommendation

**NOT ACCEPTED**

One finding blocks acceptance:

1. **US-1 AC-1 -- spec-release phase gate is too permissive** (FAILED): `/spec-release` requires `"accepted"` (order 4) instead of `"documented"` (order 5). This means a user can run `/spec-release` without having run `/spec-docs`, bypassing the pipeline order defined in AC-1. Fix: change the required phase in `skills/spec-release/SKILL.md` from `"accepted" (order >= 4)` to `"documented" (order >= 5)` and update the error message accordingly.

**Estimated fix effort: 1 iteration** (single-line change in one SKILL.md file).
