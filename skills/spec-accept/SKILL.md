---
name: spec-accept
description: Run user acceptance testing against spec requirements
argument-hint: "[spec-name]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-accept

Formal verification that the implementation satisfies every requirement, with grep-verified wiring.

```
SS="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-state.py"
```

## Workflow

1. `$SS phase-gate <spec> executed` (stop with its message on failure). `/spec-security-audit` also
   requires `executed`; the two can run in either order.
2. **Pre-acceptance evidence** (all non-blocking; log and continue on tool errors):
   - Full lint: `$SS run-gates <spec> --only lint` (output lands in `evidence/tests/`).
   - Secret and vulnerability patterns on everything changed since the spec began:
     `$SS run-gates <spec> --only none --changed $(git diff --name-only <git_sha_start>..HEAD)`;
     additionally grep those files for `dangerouslySetInnerHTML`, `innerHTML\s*=`, `query\s*\+`,
     `md5\(`, `sha1\(` and write path:line:pattern (never the matched content) to
     `evidence/pre-acceptance-security-scan.txt`.
   - Wiring audit: `$SS verify-wired <spec> --all` (writes `evidence/wiring-wave-*.md`; any FAIL is a
     wiring gap the acceptor must weigh). Also check that every completed wave N has
     `evidence/wiring-wave-N.md` and `evidence/reviews/wave-N.md`; list missing ones as evidence gaps.
   - Documentation audit: dispatch `spec-documenter` in audit mode ("do NOT generate docs; write only
     `evidence/doc-audit.md`").
3. **Acceptor** (Opus): dispatch `spec-acceptor` with requirements.md, design.md, tasks.md, state.json
   (including `security`), the `evidence/` directory contents, the wiring audit output, the evidence
   gaps, `evidence/threat-model.md` if present, and `git_sha_start`. It writes `acceptance.md`.
4. Present the report. Parse "Estimated fix effort: N" and
   `$SS set <spec> acceptance.estimated_fix_rounds N`.
5. AskUserQuestion: "Accept this implementation?" / "Request changes".
   - Accept: `$SS set <spec> acceptance.status accepted` and `$SS phase <spec> accepted`.
   - Changes: `$SS set <spec> acceptance.status not_accepted`; suggest `/spec-refine` or `/spec-loop`
     after fixing the listed gaps.
