# Task Breakdown Reference

Guidance for the spec-tasker agent when generating tasks.md.

## Task Structure

Each task must have:
- **Status**: pending | in_progress | completed
- **Wave**: Integer assigned by topological sort (0 = no dependencies)
- **Wired**: pending | yes | n/a (tracks whether code is connected to the application)
- **Deprecates**: Optional field declaring schema changes (field renames, deletions, type changes)
- **Dependencies**: List of task IDs this task depends on
- **Covers**: Which user story/acceptance criteria this implements
- **Files**: List of files this task will create or modify (enables parallel execution)
- **Description**: What to implement
- **Acceptance Criteria**: Testable conditions including at least one error-path criterion

A task is only truly done when `Status: completed` AND `Wired: yes` (or `n/a` for infra tasks).

### File Ownership

The Files field enables safe parallel execution. Tasks in the same wave with non-overlapping files can be implemented simultaneously by separate agents, each in its own git worktree.

Rules:
- No two tasks in the same wave should list the same file
- Shared integration files (routers, navigation) go to the last task in the wave that needs them
- Each task owns its own test files

### Deprecates Field

Optional task metadata that declares schema changes. Required when a task renames, deletes, or changes the type of a shared field.

Formats:
- Rename: `Deprecates: <type>.<oldField> -> <type>.<newField>`
- Deletion: `Deprecates: <type>.<oldField> -> [removed]`
- Type change: `Deprecates: <type>.<field> (<oldType> -> <newType>)`
- Multiple: one entry per line, each following one of the 3 formats above

When one or more tasks contain `Deprecates` fields (value is not `none`), the tasker MUST auto-generate a final-wave sweep task whose `Files` field is populated from a grep of the old field names.

## Wave Assignment (Topological Sort)

Tasks form a Directed Acyclic Graph (DAG) via their Dependencies field. Waves are computed by topological sort:

```
Wave 0: Tasks with no dependencies (can all run in parallel)
Wave 1: Tasks depending only on Wave 0 tasks
Wave 2: Tasks depending on Wave 0 or Wave 1 tasks
...
```

### Algorithm (Kahn's BFS)

1. Compute in-degree for each task
2. Enqueue all tasks with in-degree 0 -> Wave 0
3. For each task in current wave, decrement in-degree of successors
4. Enqueue successors with in-degree 0 -> next Wave
5. Repeat until all tasks assigned

### File-Conflict Detection

Before finalizing waves, check if tasks in the same wave touch the same files:
- Parse task descriptions for file references
- Cross-reference with design.md component-to-file mapping
- If two tasks in the same wave modify the same file, move one to a later sub-wave

## Phase Organization

### Phase 1: Setup (Wave 0)
- Project scaffolding, dependency installation, configuration
- Database setup, schema creation
- These tasks have no dependencies and run first

### Phase 2: Core Implementation (Waves 1-N)
- Main feature logic, API endpoints, UI components
- Each task includes its own test acceptance criteria (testing merged into implementation)
- Each task MUST have at least one error-path acceptance criterion

### Phase 3: Integration (Later waves)
- Wiring components together
- Route registration, navigation links, API connections
- These depend on core implementation tasks

### Phase 4: End-to-End Testing (Final waves)
- Cross-cutting test scenarios only
- Individual task testing is handled in Phase 2
- Regression verification across the full feature

### Phase 5: Polish (Final wave)
- UI refinements, performance optimization, documentation
- Error handling belongs in Phase 2, NOT here

## Task Sizing

Each task should be completable in one spec-exec iteration (one Claude session).

| Size | Description | Lines of Code | Example |
|------|-------------|---------------|---------|
| XS | Config change, single file | <20 | Add env var, update config |
| S | Single component/function | 20-80 | Write a utility function |
| M | Feature slice end-to-end | 80-200 | API endpoint + handler + test |
| L | Multi-component feature | 200-500 | Full page with API integration |

**Target: M-size tasks.** Split L tasks. Batch XS/S tasks into the same wave.

### Integration Point Cap

**Max 5 integration points per task.** An integration point is any import, route registration, provider setup, function call wiring, or UI component render added to an existing file. Tasks exceeding 5 integration points must be split into a core implementation task and a dedicated wiring task. LOC-based sizing alone misses "blast radius" — wiring code is low-LOC but high-risk when there are many targets.

## Error-Path Acceptance Criteria

EVERY implementation task must include at least one error-path criterion. Examples:

```markdown
- **Acceptance Criteria**:
  1. WHEN the user submits a valid form
     THE SYSTEM SHALL save the data and show a success message
  2. WHEN the user submits a form with invalid email
     THE SYSTEM SHALL display "Please enter a valid email" below the email field
  3. WHEN the API returns a 500 error during save
     THE SYSTEM SHALL display "Save failed. Please try again." with a retry button
```

If a task is pure infrastructure (no user-facing behavior), the error path is:
```
WHEN the [command/script] encounters an error
THE SYSTEM SHALL exit with a non-zero code and print the error to stderr
```

## Dependency Rules

1. **No circular dependencies.** The DAG must be acyclic.
2. **Minimal dependencies.** Only declare dependencies that are truly needed.
3. **Setup tasks first.** Infrastructure/scaffolding tasks should be Wave 0.
4. **Integration after implementation.** Wiring tasks depend on the components they connect.
5. **E2E testing last.** End-to-end tests depend on all implementation tasks.
