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

### 1. Understand the Starting Point

If the user provided an initial idea, acknowledge it and start exploring. If not, ask what they're thinking about.

Read relevant parts of the codebase to understand context:
- What does the current implementation look like?
- What patterns does this codebase use?
- What constraints exist?

### 2. Read Lessons

If `.claude/specs/lessons.json` exists, read it and extract lessons relevant to this feature type. Present the top 3 relevant lessons: "Based on past specs, consider: [lesson]"

### 3. Offer Expert Consultation (Optional)

Ask the user if they'd like domain expert consultants available during the session.

Use AskUserQuestion:
- **"No experts needed"** — Skip to Step 4 (standard brainstorm)
- **"Yes, bring in experts"** — Select consultants below

If they want experts, use AskUserQuestion with `multiSelect: true`:

- **Software Architect** — System design, scalability, component boundaries, integration patterns
- **Security Expert** — Threat modeling, authentication, data protection, compliance
- **ERP/Enterprise Expert** — Business workflows, data modeling, multi-tenancy, auditing
- **UX Designer** — User flows, accessibility, interaction patterns, information architecture
- **DevOps/Infrastructure** — Deployment, CI/CD, monitoring, containerization
- **Performance Engineer** — Bottlenecks, caching strategies, load patterns, optimization
- **Other** — Custom expert role (follow up to ask what role and domain)

Store the selected expert list for the session.

### 4. Iterative Exploration

Have a natural conversation. In each round:

1. **Reflect back** what you understand so far
2. **Ask 1-2 focused questions** that dig deeper or challenge assumptions
3. **Offer observations** — things they might not have considered
4. **Suggest alternatives** when relevant

Use AskUserQuestion for structured choices when helpful, but don't overuse it. Sometimes a simple "What do you think about X?" in prose is better.

Topics to explore over multiple rounds:
- What problem are we actually solving?
- Who experiences this problem? How painful is it?
- What does success look like?
- What's the simplest version that would be useful?
- What are we explicitly NOT doing?
- Are there existing patterns in the codebase we should follow?
- What are the risks or unknowns?
- If the feature includes user-facing screens: What interaction pattern should each screen use? (page, modal, dialog, drawer, inline expansion, wizard) This matters most for screens users will hit frequently — getting it wrong means full rework. Ask early: "For [screen X], should this be a full page, a modal overlay, a dialog, or something else? Consider how often users will use it and what context they need to keep visible."
- Have you considered [alternative approach]?

#### Expert Consultation (if experts were selected)

Spawn spec-consultant agents via the Agent tool when:
- The discussion hits a **domain-specific trade-off** (e.g., security vs. UX, performance vs. simplicity)
- You identify a **gap** in your or the user's knowledge that an expert could fill
- The user **asks** about a topic that maps to a selected expert
- Every **2-3 conversational rounds**, check if any selected expert would have useful input

**How to spawn a consultant:**

Use the Agent tool with `subagent_type: "spec-driven:spec-consultant"`. In the prompt, provide:

1. **Expert Role**: The specific role (e.g., "Security Expert")
2. **Domain Expertise**: What this expert specializes in
3. **Discussion Context**: A concise summary of the conversation so far
4. **Specific Question**: The precise question you want the expert to analyze
5. **Codebase Context**: Relevant file paths and patterns you've discovered

Example spawn prompt:
```
You are a Security Expert specializing in threat modeling, authentication, data protection, and compliance.

## Discussion Context
We're brainstorming a user authentication feature for a Next.js app. The user wants social login (Google, GitHub) plus email/password. We're considering storing sessions in JWTs vs server-side sessions.

## Specific Question
What are the security implications of JWT-based sessions vs server-side sessions for this use case? Consider token theft, session invalidation, and OWASP best practices.

## Codebase Context
- Current auth: none (greenfield)
- Framework: Next.js 14 with App Router
- Database: PostgreSQL via Prisma
- Relevant files: src/app/api/ (API routes), prisma/schema.prisma
```

**After receiving expert analysis:**

- Synthesize it conversationally: *"I consulted with our Security Expert, and they raised some important points..."*
- Present the key concerns and recommendations in your own words
- Ask the user how they want to respond to the expert's input
- Don't dump raw analysis — integrate it into the conversation

**Consultation guardrails:**
- Only spawn experts from the user's selected list
- Don't re-spawn the same expert without meaningful new context since their last consultation
- Can spawn multiple experts in parallel if the discussion spans domains
- Keep expert questions focused — one clear question per spawn, not a brain dump
- If experts disagree with each other, present both perspectives and let the user decide
- If the user has strong opinions in a domain, respect that and skip the expert

### 5. Over-Specification Prevention

When generating ideas, clearly tag which came from the user vs which you or the consultants inferred. Use `[inferred]` tags. This prevents scope creep and lets the user control what makes it into the spec.

### 6. Check for Readiness

After a few rounds, or when the conversation feels like it's converging, ask:

"I think we have a solid picture now. Ready to formalize this into a spec, or do you want to explore further?"

Use AskUserQuestion:
- **"Ready for /spec"** — Move to step 7
- **"Keep exploring"** — Continue the conversation
- **"Consult another expert"** — (if experts active) Request a specific expert consultation before moving on
- **"I want to change direction"** — Pivot to a new angle

### 7. Output the Brief

When the user is ready, synthesize the conversation into a structured brief:

```markdown
## Feature Brief: [Feature Name]

### Problem Statement
[1-2 sentences on what problem this solves]

### Proposed Solution
[High-level description of the approach]

### Key Behaviors
- [Behavior 1]
- [Behavior 2]
- [Behavior 3]

### User Roles
- [Role 1]: [What they need]
- [Role 2]: [What they need]

### Edge Cases
[what could go wrong]

### Non-Functional
[performance, security, accessibility needs]

### Out of Scope
- [Thing we're explicitly not doing]
- [Another thing]

### Risks
[identified risks]

### Expert Input (if consultants were used)

#### [Expert Role 1] (e.g., Security Expert)
- **Key Concerns**: [Top concerns raised]
- **Recommendations**: [Actionable recommendations adopted]
- **Design Constraints**: [Constraints this expert's input introduces]

### Open Questions
- [Any unresolved items to address in /spec]

### Codebase Context
- [Relevant existing patterns]
- [Files/modules this will touch]
```

Then tell the user:

"Here's the brief. Run `/spec <feature-name>` to formalize this into requirements, design, and tasks. The brief above will be your starting context."

## Tips

- Keep it conversational, not interrogative
- It's OK if the conversation takes 5+ rounds
- Don't rush to conclusions — let the user think
- If they seem stuck, offer concrete options to react to
- Reference specific code when discussing feasibility
- Experts supplement the discussion — they don't replace your role as thought partner
- Introduce expert input naturally: "Our architect suggests..." not "EXPERT ANALYSIS FOLLOWS"
