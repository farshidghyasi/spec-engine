## Threat Model: spec-engine-v3-enforcement

### STRIDE Analysis

| Component | S | T | R | I | D | E |
|-----------|---|---|---|---|---|---|
| C-1: state.json Template | - | Manual edit of state.json `phase` field to bypass phase gates | - | - | - | Tampering `phase` to skip directly to `"accepted"` grants unearned pipeline progression |
| C-2: Phase Gate (10 skills) | - | - | - | Phase gate error messages may leak internal file paths or state.json structure to users | - | If phase ordering comparison is flawed (e.g., off-by-one in PHASE_ORDER), skills could execute without prerequisites |
| C-3: Phase Advancement (10 skills) | - | A skill that fails mid-execution but still advances `phase` creates inconsistent state | - | - | - | - |
| C-4: Dependency Gate (3 skills) | Crafted spec name in `## Depends On` could reference path-traversal target (e.g., `../../other`) | - | - | Dependency gate error messages may expose filesystem paths of other specs | - | - |
| C-5: Auto-Format (3 skills) | - | Malicious formatter config (biome.json, .prettierrc) could execute arbitrary commands via npx | - | - | - | - |
| C-6: Atomic state.json Commits | - | - | - | - | - | - |
| C-7: Wiring Evidence (3 skills) | - | - | - | - | - | - |
| C-8: Wiring Evidence Consumption | - | - | - | - | - | - |
| C-9: Types-First Validator | - | - | - | - | - | - |
| C-10: Types-First Tasker | - | - | - | - | - | - |
| C-11: Anti-Deferral (4 agents) | - | - | - | - | - | - |
| C-12: Pre-Acceptance Lint | - | Malicious lint_cmd in state.json could execute arbitrary commands | - | Lint output written to evidence file may contain sensitive file contents | - | - |
| C-13: Pre-Acceptance Security Scan | - | - | - | Security scan evidence file may echo matched secret patterns (password values) back into evidence files | - | - |
| C-14: Doc Audit (spec-accept + documenter) | - | - | - | - | - | - |
| C-15: Sweep Enforcement (validator) | - | - | - | - | - | - |
| C-16: Fresh Validation (exec, loop) | - | - | - | - | - | - |
| C-17: Shared File Isolation (3 skills) | - | - | - | - | - | - |
| C-18: Budget Auto-Calc (spec, status) | - | Manual edit of budget_cap to null triggers recalculation; setting to artificially high value removes budget protection | - | - | - | - |
| C-19: Fix Budget Estimation (acceptor) | - | - | - | - | - | - |

### Trust Boundaries

| Boundary | Components | Data | Protection |
|----------|-----------|------|------------|
| User <-> Skill Invocation | User <-> C-2 (Phase Gate) | Skill command, spec name | Phase gate reads state.json; no authentication (local tool) |
| Skill <-> state.json | C-2/C-3/C-4 <-> C-1 | Phase value, task statuses, budget | File-system permissions only; no integrity verification of phase field |
| Skill <-> External Tools | C-5/C-12 <-> npx/formatter/linter | File contents, command output | Commands are read from config files; no allowlist validation |
| Skill <-> Evidence Files | C-7/C-12/C-13 <-> evidence/ | Grep output, lint output, scan matches | Written to spec directory; no redaction of sensitive content |
| Spec <-> Dependency Spec | C-4 <-> external state.json | Dependency spec phase value | Path constructed from spec name; no sanitization |

### Attack Surface
- Entry points: Skill invocation (10 slash commands with phase gates), `## Depends On` section in requirements.md (spec name input), formatter config detection (biome.json, .prettierrc, .eslintrc), state.json manual edits
- Data stores: state.json (phase, acceptance, budget_cap, tasks), evidence/ directory (wiring, lint, security scan, doc audit files)
- External integrations: npx biome/prettier/eslint (auto-format), project lint command (lint_cmd from state.json), grep (security scan)
- Admin interfaces: None (local CLI tool, no network interfaces)

### Injected Criteria
1. [threat-model] THE SYSTEM SHALL NOT include matched secret values (password strings, API key values) in `evidence/pre-acceptance-security-scan.txt`; only file paths, line numbers, and pattern names shall be written (CRITICAL)
2. [threat-model] WHEN constructing the path to a dependency spec's `state.json` in the dependency gate, THE SYSTEM SHALL validate that the spec name contains only alphanumeric characters, hyphens, and underscores, and does not contain path separators or `..` sequences (HIGH)
3. [threat-model] THE SYSTEM SHALL NOT expose `state.json` internal field names, absolute filesystem paths, or stack traces in phase gate or dependency gate error messages displayed to the user (HIGH)
4. [threat-model] WHEN the auto-format step detects a formatter config file, THE SYSTEM SHALL only execute the predefined formatter commands (`npx biome check --write`, `npx prettier --write`, `npx eslint --fix`) and SHALL NOT execute arbitrary commands read from config file contents (HIGH)
5. [threat-model] WHEN the pre-acceptance security scan writes evidence, THE SYSTEM SHALL truncate each matched line to 200 characters to limit exposure of surrounding sensitive context (MEDIUM)
6. [threat-model] WHEN `state.json.quality_gates.lint_cmd` is used for pre-acceptance lint, THE SYSTEM SHALL validate the command against the `quality_gates.allowed_commands` list before execution; if the list is empty or the command is not in it, log a warning and skip (MEDIUM)
