---
name: spec-brainstorm
description: Brainstorm a feature idea through conversation until it is ready for /spec
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /spec-brainstorm Command

Conversational exploration of a feature idea with optional domain expert consultants.

## Usage

```
/spec-brainstorm [idea]
```

## Workflow

1. **Understand the idea**: Ask the user to describe their feature concept
2. **Read lessons.json**: If `.claude/specs/lessons.json` exists, check for relevant past lessons
3. **Explore the codebase**: Read relevant existing code to understand current architecture
4. **Facilitate discussion**: Ask probing questions about scope, users, behaviors, edge cases
5. **Optional: Invite experts**: Ask the user if they want domain expert input. If yes, spawn spec-consultant agents with specific personas and questions.
6. **Over-specification prevention**: When generating ideas, clearly tag which ideas came from the user vs which you or the consultants inferred. Use `[inferred]` tags.
7. **Produce a brief**: When the idea is refined enough, produce a structured brief suitable for `/spec`

## Expert Consultation

Spawn spec-consultant agents with different personas based on the feature type:

- **Security Expert**: For features handling auth, data, payments
- **UX Designer**: For user-facing features
- **Database Architect**: For data-heavy features
- **DevOps Engineer**: For infrastructure features
- **Performance Engineer**: For latency-sensitive features

Each consultant receives the discussion context and returns structured analysis.

## Output

A brief suitable to feed into `/spec`:
```
## Feature Brief: [name]

### Problem
[what this solves]

### Users
[who uses it]

### Key Behaviors
[main flows]

### Edge Cases
[what could go wrong]

### Non-Functional
[performance, security, accessibility needs]

### Out of Scope
[what NOT to build]

### Risks
[identified risks]

### Expert Input
[summaries from consultants, if any]
```
