---
name: spec-release
description: Generate release notes, changelog, and deployment checklist
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# /spec-release Command

Prepare release artifacts with reproducibility manifest.

## Usage

```
/spec-release [spec-name] [--version-bump patch|minor|major] [--tag] [--release]
```

## Workflow

1. Locate spec, read spec files and state.json
2. Generate `release.md` with:
   - Changelog (user-facing + technical changes)
   - Breaking changes with migration paths
   - Deployment checklist (pre/during/post)
   - Environment variables needed
   - Database migrations
   - Rollback plan
   - **Reproducibility manifest** from state.json: model versions used, git SHA range, plugin version
3. If `--tag`: create git tag
4. If `--release`: create GitHub release via `gh release create`
