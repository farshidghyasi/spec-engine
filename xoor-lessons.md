{
  "version": 1,
  "lessons": [
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Always run biome check --write on agent output before committing. Every parallel agent produces code with slightly different formatting than biome enforces, requiring a fix commit after every wave merge.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Do not use worktree isolation for tasks that modify existing files. Worktrees branch from an earlier commit where the files may not exist yet, causing cherry-pick conflicts. Use worktrees only for tasks that create new files exclusively.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "When the project uses TypeScript strict mode with noUncheckedIndexedAccess, note this in task prompts. Agents routinely produce array[i] without undefined checks, causing typecheck failures post-merge.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "requirements",
      "lesson": "Spec validation must cross-reference enumerated values (operator lists, property lists, enum variants) in requirements.md against the design's type definitions. The 02-data-engine acceptance found is/is_not operators and min/max/pattern properties mentioned in requirements but missing from type definitions.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "design",
      "lesson": "Use forward-reference duck-typed interfaces for cross-layer dependencies in the design phase. This eliminates circular import issues and allows parallel wave execution without import ordering problems. Example: ModelDeps uses ModelRegistryInterface instead of importing ModelRegistry directly.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Provide import manifests (exact export names and signatures from completed waves) to parallel agents. This prevents cross-agent naming mismatches and eliminates the need for post-merge import resolution. 02-data-engine had zero naming conflicts across 8 parallel groups.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "02-data-engine",
      "date": "2026-03-30",
      "category": "testing",
      "lesson": "Quality gates (lint, typecheck, tests) verify code correctness but NOT spec compliance. Formal acceptance testing with AC-by-AC traceability matrix is essential to catch missing operators, properties, and semantic mismatches that pass all gates.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "01-platform-infra",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Pin all tooling versions (biome, vitest, TypeScript, pnpm) at project setup before any spec execution begins. Changing tool versions mid-spec (e.g., biome 1.x \u2192 2.x) causes config migration churn across all files.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "01-platform-infra",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Ensure complete audit logging from the first spec. Partial audit logs (only waves 0-1 logged in 01-platform-infra) reduce retrospective data quality and make it harder to identify patterns across specs.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "01-platform-infra",
      "date": "2026-03-30",
      "category": "design",
      "lesson": "Establish the bootstrap composition pattern (single entry point with dependency injection) in the first spec. 01-platform-infra's bootstrap.ts pattern was reused by 02-data-engine's ModelDeps, proving the pattern scales.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Run biome check --write --unsafe on agent output files IMMEDIATELY after each agent completes, before quality gate checks. Every wave in specs 02 and 03 (14 waves total) needed post-merge lint fixes. Automating this eliminates 7+ extra commits per spec.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "testing",
      "lesson": "Quality gates (lint, typecheck, tests) do NOT catch spec compliance issues. Test files must assert on response envelope shape (e.g., error responses include both 'code' AND 'message' fields), not just HTTP status codes. 03-base-core acceptance found 3 missing message fields that all gates missed.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "design",
      "lesson": "When the design references foundation interfaces (Config, Database, Logger), read the actual implementation signatures and include them in task prompts. 03-base-core's design said config.get<string>('auth.jwt_secret') but the real Config uses Zod-typed keys, requiring an adapter interface in the auth service.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "design",
      "lesson": "When a model declares 'inherits', callers should use it \u2014 not manually create parent records. The data engine's _createWithParents handles auto-creation. Verify delegation inheritance behavior in the data engine BEFORE writing seed/bootstrap code that creates parents explicitly.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Bootstrap wiring tasks (integrating all components) consistently use the most tokens (~70k in spec 03, similar in spec 02). Budget 1.5x the average task cost for wiring tasks, and provide extra context about the existing bootstrap structure.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-base-core",
      "date": "2026-03-30",
      "category": "requirements",
      "lesson": "Specify error response envelopes precisely in acceptance criteria. Instead of 'returns 401', write 'returns 401 with { success: false, error: { code: \"AUTH_TOKEN_EXPIRED\", message: \"Refresh token has expired\" } }'. Vague ACs lead to implementations that pass tests but fail acceptance.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Apply the shadcn preset during scaffold with `shadcn init --preset <id>` as the very first command, before adding any component or writing any CSS. Applying it after scaffold causes HSL-vs-OKLCH CSS variable conflicts that cascade into 10+ fix commits.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Tailwind 4 changed the default border-color from gray-200 to currentColor. Any border element without an explicit color class becomes invisible or inherits an unexpected color. Add `@layer base { * { @apply border-border; } }` to globals.css immediately after shadcn init, before any component work.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "@xoor/kernel cannot be imported in client (browser) code. It pulls server-side dependencies (pg, fastify, etc.) that break the browser bundle. All types needed by the frontend must either be duplicated locally or extracted to a shared @xoor/types package. Never add @xoor/kernel as a dependency of apps/web.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "TypeScript's exactOptionalPropertyTypes causes type errors in shadcn generated components that use optional props with undefined defaults. After every `shadcn add`, scan the generated .tsx files and add `| undefined` to optional prop types where needed. This fix must be re-applied because shadcn regenerates the files on every add.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Never use standard ports (3000, 3001, 5432) for any xoor dev server. Other projects on the same machine will conflict. Specify non-standard ports in the scaffold spec (e.g., 3010 for web dev, 3011 for API) so the package.json dev script is correct from the first commit.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "All UI styling must come from the shadcn theme preset. Never add custom CSS variable values outside the preset. When a custom override is found, delete it immediately \u2014 it will conflict with the preset's OKLCH color system and cause border/background color cascades.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "Parallel worktree execution works well for tasks that create new files in non-overlapping directories. Wave 2 ran 4 tasks simultaneously (hooks, simple widgets, login page, app shell) with zero conflicts. The prerequisite is that each task's Files list is strictly disjoint.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "implementation",
      "lesson": "sonner.tsx (the Sonner toast component generated by shadcn) gets overwritten by every `shadcn add` command with a fresh copy that breaks next-themes compatibility. The theme fix must be re-applied after each shadcn add. Consider a post-install script or a patch file to automate this.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "design",
      "lesson": "Lock the web rendering architecture (Next.js vs Vite, App Router vs Pages Router) in 00-architecture.md before authoring any frontend spec. The 04-web-foundation spec was originally written for Vite SPA and required a full task rewrite before Wave 0 after the architecture was corrected. Catching this in validation is good; never reaching this situation is better.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-web-foundation",
      "date": "2026-03-30",
      "category": "requirements",
      "lesson": "For UI specs, add a visual acceptance section with explicit values for key design decisions (sidebar width, icon size, background color tokens, border behavior). Unspecified visual decisions produce iterative fix commits \u2014 54% of all commits in 04-web-foundation were fixes, driven almost entirely by visual polish that lacked precise acceptance criteria.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-module-system",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Remove 'deferred to future spec' escape hatches from agent prompts. When an acceptance criterion says 'implement X', agents will log a warning instead of implementing if the prompt allows it. 05-module-system had 3 PARTIAL acceptance gaps (dropTables, to_update state, MigrationContext) all caused by agents choosing to defer rather than implement. All 3 were fixable in 15 minutes.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "05-module-system",
      "date": "2026-03-31",
      "category": "design",
      "lesson": "Split pipeline classes when step count exceeds 15. A single InstallPipeline class with 30 timed steps (15 install + 8 upgrade + 7 uninstall) produced a 757-line file. Design should have specified three sub-classes (InstallFlow, UpgradeFlow, UninstallFlow) sharing a base with hook execution and step timing.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-module-system",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Run spec-reviewer after complex waves (15+ pipeline steps, facade composition). 05-module-system skipped code review entirely for speed and the acceptance report found 5 human review items including an oversized file and inconsistent context interfaces. A review after wave 3 would have caught these early.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-module-system",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "100% first-pass success rate is achievable when task prompts include: (1) exact import manifests from completed waves, (2) exact type signatures, (3) explicit acceptance criteria, and (4) the test command to run. 05-module-system achieved 0 failures across 11 tasks by following this pattern consistently.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "05-module-system",
      "date": "2026-03-31",
      "category": "testing",
      "lesson": "Fix acceptance gaps immediately instead of accepting a lower score. Post-acceptance fixes in 05-module-system took 15 minutes and raised the score from 64/72 to 67/72 (89% to 93%). The remaining 5 gaps are genuinely blocked by future specs (cross-layer hooks, model/view inheritance).",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Tasks that ADD content to existing files (e.g., T-17 adding error classes to errors.ts) must run SEQUENTIALLY, not in parallel worktrees. Worktrees branch from pre-merge state, so the parallel agent recreates the whole file, causing content conflicts. In 06-auth-security, this produced a merge conflict on errors.ts that needed manual resolution.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Run the spec-validator BEFORE implementation begins and BLOCK on results. In 06-auth-security, the validator found 3 real errors (sessionId type mismatch, MFA error status code, junction table name) that would have been trivial to prevent during implementation but required 3 separate fix commits after. Total cost: ~20 minutes of rework vs ~2 minutes of upfront correction.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Plan for 2-3 post-acceptance fix rounds, not just 1. In 06-auth-security, the initial acceptance found 16 issues (5 FAIL + 8 PARTIAL + 3 UNTESTABLE). It took 4 fix rounds to resolve 13 of them, improving the score from 81% to 91%. Budget time for this iteration cycle in every spec execution.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "implementation",
      "lesson": "Challenge 'not fixable' classifications aggressively. In 06-auth-security, items classified as 'blocked by future specs' were re-examined and 9 of them were fixable immediately \u2014 including cross-spec issues in specs 01-05 (AsyncLocalStorage, MethodChain, transient vacuum, sys_ref trigger, seed xml_ids). The user's pushback 'is there anything we can fix?' uncovered that most 'blocked' items were actually lazy deferrals.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "design",
      "lesson": "When a spec extends an existing service (AuthService from spec 03), include the new method signature (loginById) in the task description. In 06-auth-security, the MFA challenge endpoint needed to issue tokens after verification, but AuthService had no loginById method. This required modifying spec 03's file post-acceptance, which could have been planned in the task design.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06-auth-security",
      "date": "2026-03-31",
      "category": "testing",
      "lesson": "Use acceptance testing as a cross-spec regression scanner. Running acceptance on spec 06 revealed stale issues in specs 01-05 that had been 'accepted' but never actually fixed. The pattern: after completing a spec, run acceptance not just for the current spec but also check upstream specs for newly-unblocked fixes.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "NEVER use biome check --write --unsafe on JSX/TSX files. The --unsafe flag renames variables with _ prefix and removes \"unused\" imports that are actually used in JSX returns (e.g., Card, CardHeader). In 07-view-engine, this broke KanbanRenderer and required 2 extra fix commits. Use --write (safe mode) only, or fix issues manually.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Every spec that creates Fastify routes MUST include an explicit bootstrap wiring task with the exact bootstrap.ts code changes. In 07-view-engine, registerViewRoutes and registerOnchangeRoutes were created but never called from bootstrap.ts. The \"Wire into: routes/index.ts\" instruction was insufficient \u2014 bootstrap.ts is where routes are actually registered. The post-acceptance fix required building ModelRegistryLike and ModelFactoryLike adapters with exactOptionalPropertyTypes handling.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Specify the API response envelope shape ({ success: true, data: T }) in every task description that involves both server routes and client fetch code. In 07-view-engine, useArchCache parsed response.json() directly as CompiledViewDTO, but the server wraps in { success, data }. Test mocks also used the wrong format, so the bug was invisible until documentation review.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Run a full-project lint check after the final wave completes, before acceptance. Per-wave quality gates only check the delta. In 07-view-engine, 20+ lint issues accumulated across 27 tasks (formatting, import ordering, a11y, hook-at-top-level) that no individual wave gate caught. Required 3 extra lint-fix commits post-acceptance.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "The shared barrel deferral pattern works at scale: tell parallel agents NOT to modify shared index.ts files, then reconcile the barrel after each wave. In 07-view-engine, this eliminated all merge conflicts across 11 waves and 27 tasks. The pattern is: agent creates the file, orchestrator updates the barrel.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "For large UI specs (20+ tasks, 77+ components), budget 2x the token cap. 07-view-engine used ~1.1M tokens against a 500K cap. The budget was exceeded at wave 4 (56% of tasks done). Large widget catalogs with per-widget descriptions consume tokens faster than typical backend specs.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Directory-based parallelism enables massive throughput for component catalogs. In wave 5, 6 tasks created 88 files across non-overlapping directories (basic/, selection/, date/, numeric/, media/, rich/, special/) with zero conflicts and 7,218 lines in a single wave. Structure component libraries with this pattern from the design phase.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "07-view-engine",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Update biome.json schema version BEFORE spec execution begins. In 07-view-engine, the schema was 2.0.0 but biome CLI was 2.4.9, causing rule name mismatches and suppression comment failures. Run \"biome migrate\" as a pre-execution step.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Always run /spec-validate immediately before /spec-loop, not days earlier. Spec 08 was written at git SHA c20f7498 (before specs 05-07). By execution time, all 6 referenced files had changed, requiring 5 error fixes. The codebase changes between validation and execution \u2014 stale validation is worse than no validation.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "When a UI component needs to call a service class (like ActionManager), include the exact instantiation/injection pattern in the task description. In 08-web-shell, ModuleMenuNav was supposed to call ActionManager.executeMenuAction but the agent only implemented setActiveMenu because ActionManager requires constructor injection ({pushRoute, openDialog}) and the component had no way to obtain an instance. Provide: (a) where the instance comes from (React context, prop, singleton), (b) exact import path, (c) constructor args.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "A dedicated bootstrap wiring task (T-30 pattern) eliminates the #1 acceptance failure mode. In spec 08, T-30 wired all 5 API routes into registerAuthPlugins() on first pass with zero issues. This directly applies the lesson from spec 07 where deferred route wiring was the critical acceptance blocker. Every spec with server routes MUST include this task.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Define Zod schemas as the first task in wave 0 (before routes or stores). In 08-web-shell, shell.schema.ts (8 schemas) was T-2 in wave 0. Every subsequent task (routes T-5-T-8, stores T-9-T-12, components T-13+) imported these schemas. Having them ready first eliminated all type-shape disagreements between parallel agents.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Fix commit ratio improved from 30% (spec 07) to 15% (spec 08) by applying three practices: (1) run full-project lint after final wave before acceptance, (2) never use biome --unsafe on JSX files, (3) pre-execution validation. These should be standard for every spec.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08-web-shell",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Track WebSocket-dependent features as explicit deferred items with the target spec noted. In 08-web-shell, 3 acceptance criteria were PARTIAL because they depend on spec 10 WebSocket support (menu invalidation, permission invalidation, notification push). Polling fallbacks were in place but the PARTIAL status was predictable \u2014 should have been documented upfront in requirements.md as \"deferred to spec 10\" ACs.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Include exact database column names from migration SQL in route handler task descriptions. In 09-search-system, the migration created a `shared` column but the route handler used `is_shared`, causing a runtime crash. Unit tests mocked the DB so this was invisible until acceptance cross-file validation. The fix: copy the CREATE TABLE column list into every task that writes SQL against that table.",
      "source": "retro",
      "severity": "high",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Every spec with Fastify routes MUST include an explicit bootstrap wiring task AND a barrel export task in the task list. In 09-search-system, registerSearchRoutes and SearchViewValidator were created but never called. Previous specs (07, 08) had the same issue. The pattern is now proven: T-N 'Wire routes into bootstrap.ts' with exact import/call code.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Verify debugger/fix agent changes land on the main branch, not just in a worktree. In 09-search-system, the setComparison fix was applied in an isolated worktree that was cleaned up. Always check git log on the main branch after a fix agent completes.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Pre-split hook files in the design when they will contain >10 functions or >400 lines. In 09-search-system, useSearchModel grew to 665 lines. Post-acceptance extraction into 3 files was straightforward but avoidable if planned in design.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "requirements",
      "lesson": "Every database column must appear in at least one acceptance criterion. In 09-search-system, the context column in sys_search_favorite was omitted from the Zod schema and INSERT SQL because no AC explicitly tested context persistence.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "09-search-system",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Panel-counts and similar aggregate endpoints must apply domain filtering, not return unfiltered totals. In 09-search-system, the panel-counts endpoint ignored the domain parameter, returning global counts instead of filtered counts.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When parallel tasks produce a utility (T-26 sanitizeHtml) and a consumer (T-4 MessagingService.postMessage), the consumer's task prompt MUST include an explicit instruction to import and call the utility. Otherwise the utility ships as dead code \u2014 exported but never invoked. In 10-messaging-automation, sanitizeHtml existed, was tested, and was exported from the barrel, but was never called in postMessage because T-4's prompt didn't mention it.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When two parallel agents define the same interface independently (Message in useChatter.ts vs MessageItem.tsx), date fields will diverge: hooks use string (from JSON API), components use Date. Always define shared interfaces in a single Wave 0 types file and import from there \u2014 even for frontend components. In 10-messaging-automation, this caused a post-acceptance type mismatch fix.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Parallel UI component agents that depend on hooks from sibling tasks will create local stubs (useChatterStub). After merge, nobody reconnects the stub to the real hook. Add a mandatory 'reconnection verification' step after each wave: grep for 'Stub' or 'stub' or 'coming soon' in all merged files.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "testing",
      "lesson": "Integration test tasks that test service internals (recursion depth, failure thresholds) MUST read the actual source file before writing tests. In 10-messaging-automation T-24, the agent assumed MAX_RECURSION_DEPTH was exported but it was a local const, causing 10 test failures. Add 'Read the implementation file first' as a mandatory step in integration test task prompts.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When a hook calls an API endpoint, verify the HTTP method matches the route definition. In 10-messaging-automation, useChatter called api.post() for unsubscribe but the route was DELETE. Unit tests mock fetch at the wrong layer (above the method check), making this invisible until acceptance. Add a 'method contract' comment in the hook: // DELETE /api/messaging/:model/:id/followers/:partnerId.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "12% fix commit ratio (7/59) is the best across all 10 specs, achieved by: (1) biome --write after each wave, (2) exactOptionalPropertyTypes handling in task prompts, (3) pre-acceptance wiring audit with grep verification, (4) dedicated T-20 bootstrap wiring task. These four practices should be standard for every spec.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Cross-spec file replacement (T-14 replacing spec-08 notification-routes.ts) works cleanly when the function signature is preserved. Document the existing signature in the task description and instruct the agent to maintain backward compatibility. In 10-messaging-automation, the replacement was seamless because registerNotificationRoutes kept the same (app, deps) signature.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Security NFRs (HTML sanitization, field group filtering) must be restated in the specific task prompt, not just listed in requirements.md. Agents don't cross-reference NFRs during implementation. In 10-messaging-automation, NFR-8 and NFR-9 were in requirements but absent from T-4 and T-5 task prompts, causing both to fail acceptance.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "10-messaging-automation",
      "date": "2026-04-04",
      "category": "requirements",
      "lesson": "When a spec deprecates a column name (sys_notification.read \u2192 is_read), add an enforceable check that greps for the old name in runtime code. In 10-messaging-automation, the migration handled the rename but the acceptance report noted a surviving reference in spec-08's historical migration file. While not a runtime issue, this pattern should be tracked.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Bootstrap wiring tasks must enumerate ALL services and routes that need registration, not just the task's immediate dependency. In 11-reporting, T-16 wired ImportExportService + batch job but omitted ReportEngine, ReportLoader, and 3 route registrations \u2014 caught at acceptance, required ~30 lines of post-acceptance fixup.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Agent prompts must include 'npx biome check --write <files>' as a required post-implementation step. In 11-reporting, every wave (6/6) required a follow-up style commit because agents ran typecheck and tests but not the formatter.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Barrel index files (index.ts) should either be deferred entirely to a dedicated finalization task, or the orchestrator should update them after each parallel group. Marking them as 'shared files' that agents can't touch works but requires manual reconciliation at every wave boundary.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "requirements",
      "lesson": "Budget caps for specs with >15 tasks should be set to at least tasks * 50k tokens. 11-reporting had 24 tasks and used ~1.1M tokens (2.2x the 500k cap). The cap was exceeded at Wave 3 (10/24 tasks) but execution continued per spec-loop rules.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Types-first Wave 0 (types.ts + errors.ts before any implementation) gives all subsequent waves a stable import contract. In 11-reporting, Wave 0 produced 46 exports that were imported without naming mismatches across 21 downstream tasks. Repeat this pattern for every spec with 10+ tasks.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "testing",
      "lesson": "Use describe.skipIf(!process.env.DATABASE_URL) for E2E tests that need a live database. This lets E2E tests coexist in the test suite without failing in CI. In 11-reporting, 15 E2E tests (T-21, T-22) use this pattern and skip cleanly when no DB is configured.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "When a migration defines a column as bytea but the route handler stores base64 strings, the types are mismatched. In 11-reporting, sys_import_wizard.file_data is bytea in the migration but the import route sends base64 via JSON. Either use actual bytea (Buffer) in the route or change the column to text.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Install pipeline fallback code that references non-existent DB columns (e.g., sys_report.arch) is unreachable dead code that can confuse reviewers and break if the fallback path is ever activated. Remove fallback stubs immediately when the proper loader is wired in.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "11-reporting",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Providing an import manifest (exact export names + file paths from completed waves) to parallel agents eliminates cross-agent naming mismatches. In 11-reporting, 7 parallel groups with 0 import/export name conflicts. This is the single most effective parallelization technique.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "12-ai-intelligence",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When a guard condition (e.g., config.isEnabled) applies to an entire block of if/else-if branches, wrap ALL branches in a single outer if block. Do not add the guard only to the first branch \u2014 else-if chains bypass it. The acceptance test caught this when embedding providers were instantiated despite AI being disabled.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "12-ai-intelligence",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Import manifests for parallel agents must document union types and their narrowing patterns. allFields returns Map<string, FieldDefinition | ComputedFieldDefinition> \u2014 agents accessing .selection must guard with !('compute' in field). Two agents hit this independently.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "12-ai-intelligence",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Subdirectory isolation enables maximum parallelism. Each feature service in its own directory (types, implementation, tests, barrel) with zero file overlap allowed 9 tasks to run in 3 parallel groups with zero merge conflicts.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "12-ai-intelligence",
      "date": "2026-04-04",
      "category": "testing",
      "lesson": "Bootstrap wiring tasks need regression tests that mock a configured provider with the feature disabled. The default mock (no provider configured) passes by accident \u2014 the guard is only exercised when a provider IS configured but the enable flag is false.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "12-ai-intelligence",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Dual-path implementation specs (AI path + fallback) in task descriptions prevent missing codepaths. Every feature service had both paths explicitly documented, resulting in 100% first-pass success rate across 8 feature services.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Create shared SQL identifier validation utilities (validateSqlIdentifier + quoteIdentifier) BEFORE implementation begins. The same raw-interpolation vulnerability appeared independently in 6+ services across 4 specs because no shared utility existed.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Every security-relevant default must be the restrictive option. Developers opt IN to permissive behavior. Empty JWT secrets, fail-open rate limiters, and default-allow IP rules all caused findings. Use z.string().min(32) not z.string().default('').",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Implement deny-by-default auth at the framework level (Fastify preHandler), not per-route. Routes that forget to add requireAuth() silently serve data to unauthenticated users. Make public routes opt-in via config: { public: true }.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "After parallel remediation by multiple agents, run a grep-based completeness check across the ENTIRE codebase. Agents fix the files they're told to fix but don't cross-check each other. Our first pass missed 5 items that a simple grep would have caught.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Never use regex to sanitize HTML. It's an OWASP anti-pattern bypassable through encoding tricks, nested tags, and parser differentials. Use DOM-parser-based sanitizers like DOMPurify. The regex sanitizer was in production across all messaging features.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Run security audits after EVERY spec completes, not as a batch after 12 specs. The same SQL injection pattern was independently introduced in specs 02, 05, 09, 11, and 12. Catching it in spec 02 would have prevented it in all later specs.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Internal kernel code quality directly impacts external security. The data engine (Layer 3) used raw SQL interpolation internally. When route handlers (Layer 4+) copied the pattern, it became externally reachable. Even internal APIs should use parameterized queries.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "Not every audit finding has a code fix. Encrypted embeddings at rest are incompatible with pgvector similarity search. The correct fix is PostgreSQL TDE at the deployment layer. Distinguish 'fix in code' from 'fix in deployment' early to avoid wasted effort.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "security",
      "lesson": "SSRF protection must check resolved IPs, not just hostnames. Pre-resolution hostname checks are bypassable via DNS rebinding. Always resolve the hostname first, then validate the IP against the private range blocklist. Also block cloud metadata IPs (169.254.x.x).",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "security-audit",
      "date": "2026-04-04",
      "category": "process",
      "lesson": "Post-remediation re-audit is essential. Our first fix pass resolved all CRITICALs and HIGHs but missed 5 items (view route auth, anomaly SQL, import columns, report auth, CSP). The second audit caught them all. One pass is never enough.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "requirements",
      "lesson": "Consult domain experts (e.g., Odoo version specialists) BEFORE execution when porting functionality from another system. Two experts with different version knowledge identified 30+ feature gaps including commercial_partner_id (critical for billing), company_id on partner (critical for multi-company), and partner.title as a model (not a char field).",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "Always read actual codebase type definitions before writing spec interface shapes. This spec used Odoo naming conventions (translatable, stored, inverse, groups_id) instead of the actual xoor names (translate, store, relationField, group_ids). The validation caught this, but it could have been prevented by grepping codebase types during design.",
      "source": "retro",
      "severity": "high",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Budget formula for spec-loop: (task_count * 40k) + (parallel_wave_overhead * 20k). Spec 13 had 20 tasks and was budgeted at 500k but consumed 880k. Wave 1 alone (11 parallel agents) used ~550k tokens.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Document codebase property name discrepancies in a DISCREPANCY section of tasks.md. Providing exact field name mappings (spec prose -> actual codebase) in every agent prompt prevents the naming mismatch failures seen in earlier specs. This achieved 100% first-pass success across 11 parallel agents.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "Never use SQL reserved words (index, order, group, user, table, select, etc.) as model field names. The API key model 'index' field caused ambiguity with the 'index: true' metadata property and was renamed to 'key_hash' during security review.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "testing",
      "lesson": "Security review during acceptance testing catches defense-in-depth gaps that unit tests miss. The tableName SQL injection in RecordRuleEngine was never reachable from user input but defense-in-depth requires validation at every SQL boundary. Always run security review before acceptance sign-off.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Seed data tasks are the most token-expensive in a module spec. T-10 (7 seed files, ~840 records) took 16 minutes and ~96k tokens. Budget seed data tasks separately and consider splitting by data domain if record count exceeds 500.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "A T-SWEEP task for deprecated field cleanup should always follow model extension tasks that rename fields. Even when it finds nothing, it provides auditable proof that stale references were checked. Cost is minimal (~20k tokens).",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "testing",
      "lesson": "Unit and integration tests passing does NOT mean the system works end-to-end. The first browser test of xoor v2 exposed 18 distinct bugs that all passed 2990 unit tests. Add an E2E boot test that starts the server, installs a module, and verifies tables/views/menus exist.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Every entry point (main.ts) must log fatal errors before calling process.exit(). A silent exit with code 1 is a debugging nightmare \u2014 you get zero information about what failed. The xoor main.ts swallowed errors for months.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "DDL generators must NEVER emit inline FK REFERENCES in CREATE TABLE. Circular FK dependencies (partner.company_id -> company, company.partner_id -> partner) make table creation impossible. All FKs must be deferred to ALTER TABLE ADD CONSTRAINT after all tables exist.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "Migrations must NEVER reference tables created by the module system (base_user, base_partner, etc.). Migrations run before module install \u2014 they can only reference other sys_* tables. This caused 3 separate failures in migrations 008 and 009.",
      "source": "retro",
      "severity": "critical"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "DataFileLoader @ref resolution must only process explicit { '@ref': '...' } objects, not scan all string values for dot patterns. The Venezuelan Bolivar symbol 'Bs.S' was interpreted as a reference, breaking the entire install pipeline.",
      "source": "retro",
      "severity": "critical",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "PostgreSQL bigint columns return as strings in the pg driver. All Zod schemas parsing API responses must use z.coerce.number() for numeric fields, not z.number(). This broke menu loading in the browser.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "With moduleResolution 'bundler' in tsconfig, NEVER use .js extensions in TypeScript imports. Turbopack (Next.js 16) cannot resolve .tsx files from .js extension imports. 91 files had to be fixed. Add a biome/lint rule to prevent this.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "The install pipeline wrapping everything in a single transaction is correct for production but brutal for debugging. Each fix requires the ENTIRE 13-file data load chain to succeed. Add a --dev-mode flag that commits after each step.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "Any file scanner that imports .ts files at runtime (install pipeline model loader, migration engine) must exclude .test.ts, .integration.test.ts, .e2e.test.ts files. Two separate systems (migrations AND install pipeline) failed because they tried to import test files.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "13-base-module",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "bootstrap.ts is an 850-line god function that orchestrates ALL initialization. Every spec adds more code to it. It is the #1 source of cross-spec integration failures. Consider splitting into lifecycle phases (infra -> auth -> modules -> intelligence) with clear interfaces.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "requirements",
      "lesson": "Threat-model [threat-model] criteria injected into requirements.md are NOT automatically mapped to task acceptance criteria. The tasker generates tasks from user stories, not from security annotations. Every [threat-model] criterion must be explicitly added to a task's acceptance criteria, or it will be silently skipped during implementation.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "design",
      "lesson": "Tasks with more than 5 integration points should be split. T-17 had 9 changes (editable mode, row click, new button, cell rendering, dirty styling, grouped view, footer aggregates, table-layout, dirty pagination check) and missed the most fundamental one \u2014 replacing the cell renderer. Keep integration tasks to 3-5 focused changes.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Pure utility modules (like keyboard-manager.ts) MUST have an explicit task that wires them into their consumer. 'Depends on T-6' in the task graph means 'uses T-6's output type' \u2014 it does NOT mean 'imports T-6's function'. Add 'Import createKeyboardHandler from T-6 and call it in ...' to the consumer task description.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Optional deps on route handlers (permissionService?, getModelFields?) enable graceful degradation but mask missing wiring. If a route gets a new optional dep, create a task to wire it in bootstrap.ts \u2014 even if the dep provider already exists. T-19 wired read-group-routes but not the new security deps on crudRouter.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "testing",
      "lesson": "Acceptance wiring verification must go deeper than 'is the component imported?' Check 'is it rendered/called in the production path?' EditableCell was imported by One2manyWidget but NOT by ListRenderer (the primary consumer). ConcurrencyDialog was imported by no one. Grep for the component name in JSX render returns, not just import statements.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "When an agent proactively does work beyond its task scope (T-8 wired bootstrap.ts which was T-19's job), log it immediately and mark T-19 as done. This happened correctly here but could cause double-wiring if not tracked.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "16-view-engine-advanced",
      "date": "2026-04-06",
      "category": "design",
      "lesson": "Dialog components need explicit consumer tasks. Creating a dialog (ConcurrencyDialog) without specifying which component imports and shows it guarantees it ships as dead code. The task that creates the dialog must name its consumer, or the consumer task must say 'import and show ConcurrencyDialog from T-14 when HTTP 409 received'.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-integration-hotfix",
      "date": "2026-04-06",
      "category": "testing",
      "lesson": "Verify that test skip conditions actually work. describe.skip is permanent \u2014 describe.skipIf(!process.env.DATABASE_URL) is conditional. The E2E boot test (the centerpiece of this spec) shipped with describe.skip, meaning it NEVER ran automatically. A test that never runs provides zero regression protection regardless of how well it's written.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-integration-hotfix",
      "date": "2026-04-06",
      "category": "testing",
      "lesson": "Write test assertions from requirements, not from observed database state. The E2E test checked >=20 menus because that's what the DB had, but the requirement said >=24. When the real count later exceeds 20 but stays below 24, the test passes while the requirement fails. Always copy threshold numbers from the AC, not from a SELECT COUNT(*).",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-integration-hotfix",
      "date": "2026-04-06",
      "category": "requirements",
      "lesson": "Threat-model [threat-model] criteria injected into requirements.md are NOT automatically included in task acceptance criteria. The tasker generates tasks from user stories but may miss security annotations. The JWT placeholder production guard (US-7 AC-8) was a threat-model criterion that had no implementing task. Every [threat-model] criterion must be explicitly verified in at least one task's AC section.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-integration-hotfix",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Retroactive state updates lose all quality signal. When tasks are implemented during live debugging outside the spec-engine loop, failure counts, quality gate results, and iteration data are lost. state.json showed 0 failures for spec 14, but DataFileLoader alone had 4 fix commits. If work must happen outside the loop, at minimum record which tasks each commit addresses.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "14-integration-hotfix",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Shell scripts need adversarial testing for edge cases. check-js-imports.sh only matched single-quoted imports because the grep pattern used literal single quotes. The codebase also uses double quotes. Test scripts against both quote styles, empty directories, and files with no matches before marking the task complete.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "requirements",
      "lesson": "Every [threat-model] acceptance criterion must have an implementing task with the specific check in its prompt. Spec 15 had T-6 assigned to US-6 AC6 but the task prompt allowed skipping the ACL check as a 'design decision', which acceptance rejected.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "requirements",
      "lesson": "Non-functional requirements (NFRs) must have explicit implementing tasks, not implicit coverage. NFR-6 (mobile header collapse) was specified but no task covered it, causing an acceptance blocker.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "testing",
      "lesson": "User-feedback acceptance criteria (success toasts, aria-live announcements, loading spinners) need explicit test assertions. The save flow worked but the success toast was missing \u2014 discovered by the documenter, not the acceptor or tests.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Run security reviewer per wave during execution, not retroactively during acceptance. Spec 15 had 0 security-review-wave-*.md files despite 8 completed waves, causing an acceptance blocker.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "design",
      "lesson": "When a spec runs out-of-order (spec 16 before spec 15), revise the spec at the task level: remove superseded tasks, update git_sha_start, re-verify all interfaces against actual source files. Do not block or re-plan from scratch.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "design",
      "lesson": "Wave 0 shared type contracts (form-store.types.ts) before parallel implementation eliminated all type mismatches across 17 tasks. Define all cross-task interfaces as a Wave 0 deliverable.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Zustand storeApi.getState() in event handlers eliminates stale closures entirely. Never close over record/values state in onChange/onSave callbacks \u2014 always read current state from the store.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Budget formula for large UI specs: (task_count * 30K) + (wave_count * 15K) + 50K overhead. Spec 15 budgeted 500K but used 619K. The 30% wave overhead (context rebuilding, gate checks) is not negligible.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Dynamic Tailwind classes like grid-cols-${col} constructed via template literals may not be detected by Tailwind's JIT/AOT compiler. Use a static class map or safelist instead. Verify in browser.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Client-side field security should default to deny, not allow. When userGroups is undefined and a field has groups restrictions, hide the field (return null). Server-side is authoritative, but permissive client fallback leaks UI information.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-formview-redesign",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "ACL checks on related model display names require threading permissionService through ModelDeps and ModelContext (uid) through the searchRead call chain. Use optional dependency injection \u2014 if permissionService is absent, degrade gracefully (backward compat).",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "When a task has 'Wire into' target AND a 'Wire at call sites' step, BOTH must be grep-verified during wave completion — not just at acceptance. In spec 17, ActionsDropdown existed as a component but had zero imports because the caller wiring step was skipped by the agent.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "design",
      "lesson": "Hooks that require React context providers (DndContext, FormStoreProvider, etc.) must have explicit task acceptance criteria: 'Verify the context provider wraps the consumer in the host component.' Without this, agents implement the hook but skip the DndContext/SortableContext wrapper, making drag-and-drop non-functional.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Never render field values with raw String() in view components. Always use widgetRegistry.get(fieldType, viewContext) to get the correct widget component. String() bypasses type-aware formatting (dates, many2one display names, selection labels) and the security sanitization pipeline.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Wave 0 should define all shared type contracts (Zod schemas + TypeScript interfaces) with exact export names. Including an import manifest (file path → exported names) in Wave 1+ agent prompts eliminates cross-agent import mismatches. Spec 17 achieved 100% first-pass success with this pattern.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "testing",
      "lesson": "When a component adds new hook dependencies (useColumnPreferences, useDragReorder), pre-existing test files for that component will fail unless those hooks are mocked. Add vi.mock() entries for all new hooks in the test file's mock section proactively during the wiring task.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "17-view-engine-polish",
      "date": "2026-04-06",
      "category": "implementation",
      "lesson": "Run 'git worktree prune' before starting spec-loop to clean stale worktrees from prior specs. 42 stale worktrees caused Agent isolation: 'worktree' to silently fall back to writing directly to the main working directory.",
      "source": "retro",
      "severity": "low"
    }
  ]
}