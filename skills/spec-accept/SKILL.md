---
name: spec-accept
description: Run user acceptance testing against spec requirements
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-accept Command

Run user acceptance testing to formally verify the implementation satisfies all requirements.

## Usage

```
/spec-accept [spec-name]
```

## Phase Gate

Before proceeding, read `state.json.phase`. If the field is absent, treat as `"spec"`.

**Required phase**: `"executed"`
**Phase order**: spec(1) -> validated(2) -> executed(3) -> accepted/audited(4) -> documented(5) -> released(6) -> verified(7) -> retro(8)

If `state.json.phase` has not reached the required phase (compare numeric order), display:
"Phase gate: /spec-accept requires phase 'executed' to be complete. Current phase: '<CURRENT>'. Run /spec-exec (or /spec-loop or /spec-team) first."
Stop execution. Do not proceed to any subsequent step.
Do NOT expose state.json field names, filesystem paths, or stack traces in this message.
Note: Both `/spec-accept` and `/spec-security-audit` require `'executed'` and may run in either order.

## Workflow

1. Locate spec directory, validate spec name

### Step 1.5: Pre-Acceptance Full Lint

1. Read `state.json.quality_gates.lint_cmd`. If null or empty: log "Pre-acceptance lint
   skipped: no lint command configured" to audit log and skip to Step 1.6.
2. Validate `lint_cmd` against `state.json.quality_gates.allowed_commands`. If
   `allowed_commands` is empty or `lint_cmd` is not in the list: log "Pre-acceptance lint
   skipped: lint_cmd not in allowed_commands" and skip to Step 1.6.
3. Run `lint_cmd` on the full codebase (no file filtering).
4. Write output to `evidence/pre-acceptance-lint.txt`:
   - Zero errors: write "PASS: 0 lint errors"
   - Errors present: write full lint output
5. If `lint_cmd` fails to execute (command not found, crash — not lint errors): log the error
   to the audit log, write the error to `evidence/pre-acceptance-lint.txt`, and proceed.
6. Include lint results in the acceptor's input.

### Step 1.6: Pre-Acceptance Security Scan

1. Read `state.json.reproducibility.git_sha_start`.
2. If non-null: get changed files via `git diff --name-only <sha>..HEAD`
3. If null: scope to all source files, excluding: `node_modules/`, `dist/`, `.next/`,
   `vendor/`, `.git/`
4. Grep for patterns across scoped files:
   - Hardcoded secrets: `password\s*=\s*["']`, `api_key\s*=\s*["']`, `secret\s*=\s*["']`
   - SQL injection: `query\s*\+`, `"SELECT.*"\s*\+`
   - XSS sinks: `dangerouslySetInnerHTML`, `innerHTML\s*=`
   - Insecure crypto: `Math\.random\(\)` in security context, `md5\(`, `sha1\(`
5. Write results to `evidence/pre-acceptance-security-scan.txt`:
   - Zero matches: write "PASS: No common vulnerability patterns detected"
   - Matches found: write ONLY file path, line number, and pattern name.
     Do NOT write matched line content. Do NOT write credential or secret values.
     Truncate any surrounding context to 200 characters maximum.
6. Include in acceptor's input. Non-blocking: if grep fails, log the error and continue.

### Step 1.7: Documentation Audit

1. Dispatch spec-documenter agent with these exact instructions:
   "Scan the implementation for documentation gaps. Do NOT generate documentation files.
    Report: undocumented exports, functions missing JSDoc/docstrings, components missing
    prop documentation. Write your findings ONLY to evidence/doc-audit.md."
2. If the agent fails or times out: log the error to the audit log and proceed (non-blocking).
3. Include `evidence/doc-audit.md` in the acceptor's input as non-blocking context.

2. **Pre-acceptance wiring audit** (run BEFORE delegating to acceptor — this catches the #1 failure mode):

   For every task in state.json with `wired: "yes"`:
   a. Read the task's primary output file, extract its main export name
   b. Grep the codebase for imports of that export (excluding the defining file itself):
      ```bash
      grep -r "import.*ExportName" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ | grep -v "<defining_file>"
      ```
   c. If **zero imports found**: Flag in a wiring report. "File exists" ≠ "file is used."
   d. Include the wiring report in the acceptor's input so it can factor this into its assessment.
   e. Also read `state.json` for `reproducibility.git_sha_start` and include it in the acceptor's input: "git_sha_start: <value or null>" — the acceptor uses this value in Step 2.5 for stale reference checking.

   This audit exists because the first acceptance pass in a real run missed 5 unwired components that existed as files but had zero imports.

   Additionally, read all `evidence/wiring-wave-*.md` files and include their contents in the
   acceptor's input. For each completed wave in `state.json.waves`, verify a corresponding
   `evidence/wiring-wave-N.md` file exists. If any completed wave is missing its evidence file,
   flag: "WIRING EVIDENCE GAP: Wave N has no wiring evidence" in the acceptance input.

3. Delegate to spec-acceptor agent with:
   - requirements.md, design.md, tasks.md, state.json
   - Evidence from `evidence/` directory (screenshots, test results, review reports)
   - **Wiring audit results from step 2** (list of verified vs unverified imports)
   - `state.json.security` section content (read from state.json; if the key is absent, pass `null`)
   - List of existing `evidence/security-review-wave-*.md` files (Glob result)
   - Content of `evidence/threat-model.md` if it exists (else pass `null`)
4. Present the acceptance report to the user

### Step 5.5: Update state.json Acceptance Data

After the acceptor completes and writes acceptance.md:
1. Parse `estimated_fix_rounds` from the acceptance report (the "Estimated fix effort: N" line)
2. Determine status: "accepted" if user confirmed, "not_accepted" otherwise
3. Update `state.json.acceptance`:
   ```json
   {
     "status": "accepted" | "not_accepted",
     "estimated_fix_rounds": N
   }
   ```
4. Write the updated state.json to disk.

5. Ask via AskUserQuestion: "Accept this implementation?" / "Request changes"

When the user responds with acceptance ("Accept this implementation" or equivalent positive
confirmation):
Set `state.json.phase` to `"accepted"`.
Log "Phase advanced to 'accepted'" to the audit log.
