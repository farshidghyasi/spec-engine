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

## Workflow

1. Locate spec directory, validate spec name
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

3. Delegate to spec-acceptor agent with:
   - requirements.md, design.md, tasks.md, state.json
   - Evidence from `evidence/` directory (screenshots, test results, review reports)
   - **Wiring audit results from step 2** (list of verified vs unverified imports)
4. Present the acceptance report to the user
5. Ask via AskUserQuestion: "Accept this implementation?" / "Request changes"
