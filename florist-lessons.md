{
  "version": 1,
  "lessons": [
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "implementation",
      "lesson": "When a shadcn block is installed (e.g., dashboard-01, sidebar-07), agents MUST import and use the actual installed components (AppSidebar, NavMain, NavUser, SiteHeader) \u2014 not hand-roll custom sidebar/layout components. Always read the block's page.tsx file first to understand the component structure, then customize only the data props.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "implementation",
      "lesson": "Do NOT upgrade major framework versions (Tailwind 3\u21924, Next.js 15\u219216) during a spec implementation. Major upgrades (CSS config format changes, PostCSS plugin requirements, routing convention renames) cause more fix work than the entire spec. Do version upgrades as a separate, focused task before starting a new spec.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "design",
      "lesson": "NextAuth v5 CredentialsProvider does NOT support strategy: 'database'. Always use strategy: 'jwt' with CredentialsProvider. Embed roles in the JWT token via the jwt callback. The DrizzleAdapter is only needed for OAuth providers. Design documents must verify NextAuth version compatibility before specifying session strategy.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "implementation",
      "lesson": "After signIn() with redirect:false in a server action, auth() cannot read the new JWT cookie (it reads the original request cookies). To determine the user's roles for post-login redirect, query the database directly instead of relying on the session.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "implementation",
      "lesson": "@neondatabase/serverless neon() function only works with Neon cloud (HTTP API). For local Docker PostgreSQL, use the Pool class with neonConfig.wsProxy pointing to a wsproxy container. The wsProxy function must return an absolute host:port (e.g., 'localhost:5435/v1'), not append to the DATABASE_URL host. In Node.js contexts, set neonConfig.webSocketConstructor = require('ws').",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "implementation",
      "lesson": "Tailwind v4 requires: (1) @import 'tailwindcss' in globals.css to activate utility scanning, (2) @tailwindcss/postcss plugin in postcss.config.mjs, (3) @layer base rule to set border-color to var(--border) since preflight defaults to currentColor (black). CSS variables must use oklch() format directly \u2014 do NOT wrap in hsl().",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "testing",
      "lesson": "Structural/contract tests (grep-based file content checks) miss runtime integration issues like NextAuth callback errors, CSS rendering failures, and database connection problems. Include at least one live integration test (start server, hit endpoint, verify response) before claiming a spec is complete.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "foundation",
      "date": "2026-03-24",
      "category": "design",
      "lesson": "For florist admin dashboards, the expert-recommended widgets are: (1) KPI cards (revenue, orders, AOV, pending fulfillment), (2) delivery status by wave, (3) sales by channel donut, (4) 7-day revenue trend with YoY overlay, (5) waste/inventory alerts sorted by expiry urgency, (6) top products horizontal bar chart with margin indicators. The pending fulfillment count is florist-specific and critical for make-to-order businesses.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "POS/cashier screens used 100+ times/day MUST be prototyped or wireframed before implementation. The original scrollable single-page form was completely replaced by a split-panel modal (form left, summary right) because cashiers need to see the running total while adding items. Any high-frequency workflow screen needs layout validation with the end user before coding begins.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Classify admin entities by complexity before choosing the CRUD pattern. Simple entities (category, tag, occasion, stem type, product type) should use modal-based create/edit within the list page. Complex entities (product, customer, order) with images, sub-tables, or multi-section forms justify full dedicated pages. Do NOT apply a uniform '/new' + '/[id]/edit' page pattern to everything.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Product catalog specs MUST include: product images (multi-upload, default selection), product add-ons (linking upsell items), human-readable SKU/product ID, and separate show-in-POS vs show-on-web toggles. These are not nice-to-haves \u2014 they are essential for the admin product form to feel production-ready. The product form is the most-used admin screen.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Florists use ADDITIVE upgrade pricing (base price + delta), not independent variant pricing. A 'Deluxe' upgrade adds $15 to the base, not a separate $64.99 price. Name them 'upgrades' not 'variants' \u2014 the designer adds more stems to the same arrangement, not a different product. The upgrade model is: base_price + additionalPrice, not variant.price.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Seed data is product, not a checkbox. For a florist POS, the minimum viable seed requires: 60+ categories (with 2-level hierarchy), 100+ stem types (color-specific), 20+ occasions (with SEO descriptions and seasonal date ranges), and 100+ products covering every subcategory with realistic pricing, occasion tagging, and upgrade tiers. Consult domain experts (Teleflora, BloomNation, FSN) for industry-standard taxonomy.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Wave-based execution with quality gates (tsc + vitest) on every wave works extremely well when the dependency DAG is correct. This spec achieved 30/30 tasks with zero failures and zero regressions across 7 waves. The pattern: schema (wave 0) \u2192 infra (wave 1) \u2192 server actions (wave 2) \u2192 components (wave 3) \u2192 page assembly (wave 4) \u2192 e2e tests (wave 5) is reliable.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Pure-function state reducers with exhaustive unit tests are the one component type that survives post-spec rework without changes. The order-reducer (49 tests, pure inputs/outputs) needed zero modifications even when the entire POS UI was redesigned. Invest heavily in reducer test coverage \u2014 it pays dividends.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "catalog-pos-order-entry",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Occasions in a florist system need seasonStart/seasonEnd fields (MM-DD text format, year-agnostic) for automated web storefront toggling. Holiday occasions (Valentine's, Mother's Day, Christmas) should default showOnWeb:false and be auto-activated by date range. Include SEO-optimized descriptions (~155 chars) on both occasions and categories for Google meta tags.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Self-reported 'wired: yes' status by agents is unreliable. A component can have full test coverage, be marked wired, yet have ZERO imports in application code (dead code). Acceptance tests MUST include a grep-based wiring verification: for every UI component task marked 'wired: yes', grep for its import in non-test files and confirm at least one match. This caught RefundDialog being completely unreachable despite 9 passing tests.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Every new admin/POS page MUST have an explicit task for adding its navigation link to the sidebar. The sidebar file (app-sidebar.tsx) is a shared file \u2014 if no task explicitly owns 'add link to sidebar for /admin/X', it will not happen. Page tasks that say 'Wire into: sidebar' are insufficient because the page task agent focuses on the page itself, not the sidebar.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Functions that compute and store derived data (tax calculations, totals, summaries) MUST be idempotent. Use DELETE-then-INSERT or UPSERT, never bare INSERT. calculateOrderTax inserted new tax_line_items rows every call without deleting old ones, causing 27 duplicate rows after 3 invocations (page load + dialog open + retry), which inflated daily summary tax totals.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Never initialize SDK clients (Stripe, TaxJar, Resend, Twilio) at module top level with `new Stripe(process.env.KEY!)`. The non-null assertion passes undefined when the env var is missing, crashing at import time and breaking every file that transitively imports the module. Always use a lazy factory function: `let client: Stripe | null = null; export function getStripeClient() { if (!client) client = new Stripe(process.env.STRIPE_SECRET_KEY!); return client; }`.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Payment flow UX for POS must overlay the order context, not navigate away from it. The user needs to see order details while paying. Spec went through 3 iterations: separate page (lost context) -> full-screen modal (too heavy) -> compact dialog overlay (correct). For any checkout/payment screen, specify 'dialog overlay on current view' as the UX pattern in requirements, not 'navigate to /payment'.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Use business-friendly enum values from the start: 'unpaid' not 'pending_payment', 'cancelled' not 'voided'. Renaming a DB enum value after implementation required updating 15 source files + 7 test files. Get terminology sign-off during requirements phase. If the value would sound like jargon when read aloud to the shop owner, rename it before coding begins.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "When a new spec adds columns to existing tables (e.g., grand_total on orders), the design MUST specify how existing rows get backfilled and how the existing create/update actions get updated to set the new column. Spec 03 added grand_total to orders but only set it during tax calculation \u2014 orders created via createOrder showed $0 until payment page was visited.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Inngest SDK v3 changed createFunction to take 2 arguments (config object with id/name, handler function) instead of 3. Inngest v2 used createFunction(name, event, handler). Quality gates (tsc) caught this immediately. When using any SDK, verify the installed major version and check for breaking API changes before writing implementation code.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "drizzle-kit generate requires interactive TTY input for migration name prompts and cannot be run in non-interactive agent environments. When tasks include migration generation, either (a) write the migration SQL manually based on schema diff, or (b) run drizzle-kit generate as a manual step outside the agent loop.",
      "source": "debugging",
      "severity": "low"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Config services that read env vars should fail fast in production but return sensible defaults in development. getShopConfig() originally threw on missing SHOP_* vars, which crashed the entire app in dev when those vars weren't configured. Pattern: check NODE_ENV \u2014 in production, throw; in development, return defaults (shop name 'Dev Shop', address '123 Main St', etc.).",
      "source": "debugging",
      "severity": "low"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Tax provider integration must include a fallback chain: (1) configured provider (TaxJar/Avalara), (2) manual flat-rate entry by cashier, (3) null provider returning $0 for development. When TAXJAR_API_KEY is missing, the system should not crash \u2014 it should fall back to manual entry mode with a clear UI indicator that tax was manually entered.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Parallel agent execution requires that every wave's worktree is based on the merged output of the previous wave. When agents are launched from worktrees based on older commits (before Wave 0 merge), they cannot find shared type files and create local stubs instead. Ensure the worktree checkout SHA includes all completed prior waves.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03-payments-tax-daily-ops",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Task descriptions must explicitly list every shared file that the task must NOT modify. T-6 modified schema/index.ts (a shared file) because only T-1's description included the 'do NOT modify schema/index.ts' warning. Every task in a parallel wave needs a 'Do NOT modify' list for all files in the parallel.shared_files config.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Pre-execution validation (reviewing tasks against codebase reality before writing any code) is the highest-ROI step in spec execution. In spec 02, validation caught 5 issues: migration filename conflict, role API mismatch (session.user.role vs session.user.roles), architecturally impossible AC (toast on server redirect), unsafe module-level caching, and incomplete caller lists for async propagation. All 5 would have caused failures during execution. Always run validation before the first wave.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "When a task creates a new schema file (e.g., src/db/schema/settings.ts), the post-merge checklist in state.json must explicitly include adding the barrel export to src/db/schema/index.ts. Without the barrel export, Drizzle's relational query API (db.query.tableName) cannot find the table. Task descriptions correctly say 'do NOT modify index.ts' for parallel safety, but the post-merge step to add the export must be documented separately.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Modules that validate environment variables at import time (throwing on missing values) must include a dev-mode fallback. The encryption module threw when SETTINGS_ENCRYPTION_KEY was missing, which crashed the entire app in development because getSetting() is imported transitively by getShopConfig() which runs on every admin page. Pattern: in development (NODE_ENV !== 'production'), auto-generate a transient key and log a warning; in production, throw.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "When making a synchronous function async (e.g., getShopConfig, getTaxProvider, getStripe), the task description MUST include a grep command like `grep -r 'functionName' --include='*.ts' src/` so the implementer mechanically finds ALL callers. Relying on the spec author's memory to list callers is unreliable -- spec 02 missed refund-service.ts as a caller of getTaxProvider(), causing a TypeScript error after the wave completed.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "When multiple tabs/sections share identical structure (5 service credential forms with save + test connection), design a single generic component parameterized by props (ServiceSettingsTab with serviceGroup, title, settings) instead of 5 separate components. This reduced task count from ~20 to 15 and eliminated code duplication across Stripe/TaxJar/Resend/Twilio/Inngest tabs.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Next.js server-side redirect() cannot set toast messages, flash data, or any client-side state. Do not write acceptance criteria that require a toast or notification after a server-side redirect. If the user needs feedback on why they were redirected, use query parameters (?reason=unauthorized) or rely on the absence of the navigation link as the primary UX signal.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "02-admin-settings",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "When parallel tasks in the same wave both need to modify the same file (T-12 and T-13 both modified calculate-order-tax.ts), the execution engine must detect the overlap via file ownership and run them sequentially within the wave. This worked correctly in spec 02 because file lists were accurate. Always list every file a task will touch in its Files field -- omitting a shared file causes merge conflicts.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "When a spec reads data from tables defined in a prior spec, the design doc MUST include a 'Cross-Spec Data Dependencies' section listing exact table.column names (e.g., orders.street1, orders.zipCode). Verify these with grep before implementation. Spec 04 used addressLine1/postcode instead of street1/zipCode from the orders schema, causing route optimization to receive empty addresses.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "design",
      "lesson": "Any spec that introduces user-configurable values (max stops, poll interval, cache TTL) MUST use the DB-backed settings system (getSetting/setSetting) from the start, not hardcoded constants in a config.ts file. Hardcoded constants in Spec 04 required post-spec rework to migrate 7 values to the admin settings UI. Add a requirements checklist item: 'Would a shop owner want to change this value?'",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "testing",
      "lesson": "For UI components, write the component implementation first, then write tests that render the actual component. Do NOT write tests from the design doc specification alone. Spec 04 T-14 had 4 test failures because tests expected a driver name header and 'Yes, Cancel Dispatch' button text that the component did not render. Tests written against a spec are aspirational; tests written against code are reliable.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "state.json must be updated atomically with code changes -- in the same commit as the task implementation. Bulk-updating state.json at the end of execution makes it unreliable as a progress indicator. Spec 04 showed all tasks as 'pending' in tasks.md while code was fully implemented. The spec-exec loop should enforce: task is not 'completed' until state.json is committed with the implementation.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "requirements",
      "lesson": "Establish and document canonical schema field naming conventions in CLAUDE.md or a shared reference. Addresses: street1/street2/city/state/zipCode (not addressLine1/postcode/zip). Phone: phone (not phoneNumber/tel). This prevents cross-spec field name mismatches where one spec uses addressLine1 and the DB stores street1. All task descriptions must reference the canonical names.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "04-delivery-dispatch",
      "date": "2026-03-26",
      "category": "implementation",
      "lesson": "Pre-execution validation (spec-validate) must check all enum values and field names in task descriptions against the actual codebase. Spec 04 T-2 carried a stale 'pending_payment' enum value from an earlier design iteration, causing a merge conflict when the agent renamed 'unpaid' to 'pending_payment' in orders.ts. A grep-based validation would have caught the discrepancy before wave 0 started.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "design",
      "lesson": "For tablet/shop-floor displays, run a multi-expert domain review (UX, ERP, domain expert, floor management) AFTER v1 implementation. The build-then-review-then-enhance cycle produces better results than anticipating all needs upfront. The 4-expert panel for the designer display identified 22 improvements that no single perspective would have caught, including: container/vase info as a dealbreaker (florist), elapsed timer for bottleneck detection (floor mgmt), accidental claims from whole-card tap (UX), and order events log for timing data preservation (ERP).",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "testing",
      "lesson": "Client components with useEffect + setInterval (polling) cannot be reliably tested with vi.useFakeTimers(). The setInterval creates an infinite loop of state updates that hangs act() and waitFor(). Working pattern: use real timers, mock the async functions to resolve immediately, capture props via module-level variables in mock components, and use waitFor() on those captured props instead of DOM queries. Do NOT try to test the interval mechanism directly.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "design",
      "lesson": "When a spec has a universal UI constraint (e.g., 'all interactive buttons minimum 56px touch target'), it must be enforced structurally \u2014 not by memory. Options: a shared Tailwind class (btn-touch), a wrapper component, or a lint rule. Relying on each parallel agent to remember the constraint doesn't work. The acceptance test caught 2 buttons at 44px instead of 56px despite the spec clearly stating the requirement.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "implementation",
      "lesson": "When components render 'the first item' (lines[0], images[0]), always iterate ALL items instead. The OrderDetail component initially only showed the recipe for lines[0], missing subsequent line items in multi-product orders. Any pattern that reads array[0] without mapping the full array should be flagged during code review.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "implementation",
      "lesson": "Components created at the wrong route group path (src/app/pos/ vs src/app/(pos)/pos/) will not be served by Next.js. Always check the project's route group structure BEFORE creating page/layout files. In this spec, all 9 components had to be moved from src/app/pos/designer/ to src/app/(pos)/pos/designer/ during page assembly.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "design",
      "lesson": "For work queue displays (Kanban-style), use explicit action buttons (e.g., 'Claim') instead of making the entire card a tap target. Whole-card tap targets cause accidental claims in wet-hands/dirty-hands environments (florist back room, kitchen, warehouse). The UX expert and floor management expert independently flagged this as the #1 usability risk.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "design",
      "lesson": "State-changing actions (claim, complete, return to queue) should log to an append-only events table BEFORE nulling tracking columns. The returnToQueue action nulls claimedBy and claimedAt, permanently destroying timing data. An order_events log table with event_type + metadata preserves the full history for analytics (average arrangement time, return-to-queue rate, designer throughput).",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "05-designer-display-fulfillment",
      "date": "2026-03-27",
      "category": "requirements",
      "lesson": "Florist designer displays MUST show: container/vase type (first thing the designer reaches for), occasion (critical for Designer's Choice color palette), delivery type (affects packaging), and price (guides stem quality). These are all on paper tickets and their absence will drive designers back to paper within the first hour. Container type requires a catalog schema addition \u2014 plan for it early.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "Server actions CANNOT serialize JavaScript Date objects across the boundary. Drizzle mode:date returns Date objects. Every server action returning DB entities with timestamp columns must explicitly convert dates to ISO strings before returning. Create a standard serializeDates() utility in Wave 0 and use it in every action that returns entities.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "Client components (use client) must NEVER import from service modules that touch db, env.ts, or getSetting. This triggers Missing required environment variables at import time in the browser. Client components may only import from: server actions, pure type files, UI components, and utility functions that have no server-side dependencies.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "GL posting must run AFTER all async mutations (tax calculation, fee computation) complete, not inside the initial DB transaction. When the order confirmation transaction commits before calculateOrderTax() runs, the GL entry has taxAmount=0. Pattern: transaction commits then async operations complete then re-read entity with updated values then post GL entry.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "All list/table pages must follow a canonical template: server component page.tsx fetches data then passes to use client child with TanStack React Table with search, column filters, Group By dropdown with collapsible headers, pagination (50 default), row selection checkboxes, export (CSV/XLSX via DropdownMenu), delete in toolbar when rows selected.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "Never use UUID (.id) fields in user-facing text (memos, labels, descriptions). Always resolve to human-readable references: order.orderNumber instead of order.id, customer firstName+lastName instead of buyerId. Grep for template literals containing .id to catch violations.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Use DropdownMenu (not Select) for action menus like Export. Select retains its selected value so clicking the same option twice does not fire onValueChange. DropdownMenu fires onClick every time, which is correct for repeatable actions.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Financial report PDF exports should follow CPA standards: company name + report title + as-of date + Accrual Basis centered header. Two-column layout (description + amount), no account codes on external docs. Single underline above subtotals, double underline below grand totals (amount column only). No table grid lines. Unaudited disclaimer footer. Consult a CPA expert for layout.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "XLSX exports must contain raw numeric values (number type), not formatted currency strings. CPAs need to SUM, pivot, and reference values in Excel. Apply Excel number formatting via cell format codes, not by pre-formatting the value as a string.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "requirements",
      "lesson": "Spec validation (8 rounds for this spec) has extremely high ROI. Each round caught genuine errors that would have caused implementation failures. Budget for 2-4 validation rounds minimum. The cost is about 15 minutes per round; the savings are hours of debugging. Never skip validation.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06a-accounting-coa-gl-engine",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Journal entry detail should be a modal, not a separate page. Navigating away from a list loses context. Entity detail views from list pages should open as modals. Clicking document references should navigate to the source document. Clicking partner names should open an inline preview modal.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "When migrating a function signature (e.g., replacing getPaymentMethodAccountCode with resolvePaymentMethodAccount), ALL callers must be in some task's Files array \u2014 including indirect callers like server actions that pass parameters through. Validation caught 3 missing direct callers, but payment-actions.ts was still missed because it calls processCashPayment/processCardPayment which internally call the migrated function. Trace at least 2 levels deep: direct callers AND callers of those callers that pass parameters through.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "When a 'use server' action returns ActionResult<T>, the client must access result.data (not result.someFieldName). Field name mismatches between the ActionResult wrapper and the inner type are a common bug pattern in Next.js server actions. The corporate payment dialog used amountCents/paymentDate/balanceResult.remainingBalance while the action returned amount/date/balanceResult.data. Enforce explicit typing of action results in client component state \u2014 never use 'any' or untyped access.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "state.json must be updated atomically per-task during execution, in the same commit as the task implementation. Bulk-updating state.json at the end makes it useless as a progress indicator. Spec 03a showed 2/19 complete in the dashboard despite all code being fully implemented. The spec-exec loop should enforce: task is not 'completed' until state.json is committed with the implementation.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "testing",
      "lesson": "spec-documenter is an effective bug-finder \u2014 it reads both the design spec and the implementation, catching field name mismatches that unit tests miss because tests mock the boundary. The documenter caught 3 field name mismatches in the corporate payment dialog (amountCents vs amount, paymentDate vs date, balanceResult.remainingBalance vs balanceResult.data). Consider running spec-documenter as a quality gate, not just a documentation step.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "When adding a new column (paymentMethodId) to an existing table used by many callers, make it nullable in the Drizzle schema initially even if the design says NOT NULL. The migration can use nullable -> backfill -> ALTER SET NOT NULL, but the Drizzle schema must match the migration's initial state. Otherwise TypeScript types show 'string' while the DB allows null during the backfill window, causing runtime errors. Add .notNull() to the Drizzle column only after confirming the backfill migration has run.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "03a-payment-methods",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Post-spec UX improvements (like settings page redesign with left-nav) should be anticipated during design. If a settings page will have 6+ sections, design it with left-nav navigation from the start. The accounting settings page required a post-spec redesign because the single-scroll layout became unwieldy. Add a design checklist item: 'If this page has 6+ sections, use left-nav layout.'",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06b-ar-completion-tips-deposits",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Sub-ledger tagging is critical for AR reporting. The AR Aging report derives all data from journal_lines.subLedgerType + subLedgerEntityId. If any JE builder forgets to set sub-ledger tags on A/R lines, the aging report will be wrong. Every A/R journal line MUST have subLedgerType='customer' and subLedgerEntityId set. Verify this in unit tests for every JE builder that touches the A/R account.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06b-ar-completion-tips-deposits",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "Journal-only flows (no domain record) create reconciliation gaps. Tip payouts, tax remittance, and daily deposits initially had no table -- just a JE. This made bank reconciliation impossible and led to the document-first architectural decision: always create a domain record before posting a JE. The JE's sourceType/sourceId must point to a real table row. No 'naked' journal entries for operational flows.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06b-ar-completion-tips-deposits",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "Worktree merge conflicts on barrel files (index.ts) are predictable and happen every time a worktree adds exports. The mitigation is to never let worktree agents modify barrel files -- defer barrel file updates to a post-merge step instead. For shared page files, ensure only one task per wave modifies a given page file.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06b-ar-completion-tips-deposits",
      "date": "2026-03-28",
      "category": "design",
      "lesson": "650+ line service files are acceptable for complex accounting logic. credit-note-service.ts has 3 complex functions (createCreditNote, voidInvoice, cancelRemainingBalance) each with multi-step transaction logic. Splitting would hurt readability more than it helps because the functions share helper logic and types. The 500-line warning threshold should be relaxed for accounting service files with complex transactional business logic.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06b-ar-completion-tips-deposits",
      "date": "2026-03-28",
      "category": "implementation",
      "lesson": "spec-loop state.json updates must be atomic per-task, committed in the same commit as the task implementation. Batch-updating state.json at wave boundaries makes progress tracking unreliable and shows incorrect counts on the dashboard. This is the third spec (after 04 and 03a) to flag this issue -- it needs a structural fix in the spec-loop executor.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "01b-customer-types + 03b-payment-terms",
      "date": "2026-03-29",
      "category": "implementation",
      "lesson": "Catch blocks in server actions must propagate error messages: `catch {}` with generic 'Something went wrong' hides service-level validation errors (duplicate code, referential integrity). Always use `catch (e) { return { success: false, error: e instanceof Error ? e.message : 'Something went wrong' } }`. This was the #1 acceptance rejection cause across both 01b and 03b specs \u2014 rejected in both acceptance rounds. Must be codified as a mandatory pattern in the spec template.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "01b-customer-types",
      "date": "2026-03-29",
      "category": "implementation",
      "lesson": "Every new lookup table needs seed.ts wiring \u2014 creating the seed script file is not enough. It must also be imported and called from src/db/seed.ts. This was missed for customer types (01b) but correctly handled in payment terms (03b) because 03b learned from 01b's acceptance rejection. Add seed.ts to the T-1 file list for every lookup-table spec.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "01b-customer-types",
      "date": "2026-03-29",
      "category": "implementation",
      "lesson": "New pages must match the standard layout pattern: px-4 lg:px-6 container with rounded-md border table. Card-wrapped tables look different from the standard list page pattern. Every new list/settings page must follow the customers page layout, not invent a Card-based wrapper. Validate layout visually against an existing page during acceptance.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "01b-customer-types",
      "date": "2026-03-29",
      "category": "implementation",
      "lesson": "User-requested features added mid-implementation need immediate migration SQL updates. When isCorporate was added to the Drizzle schema during implementation, the handwritten migration SQL was not updated to match \u2014 causing a mismatch between 'new deployment' (migration) and 'existing deployment' (Drizzle push) paths. Any mid-spec schema change must update both the Drizzle schema file AND the migration SQL in the same commit.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "01b-customer-types + 03b-payment-terms",
      "date": "2026-03-29",
      "category": "design",
      "lesson": "The 03a payment-methods pattern is now a proven template across 3 implementations (payment_methods, payment_terms, customer_types). Future lookup-table specs should reference 03a explicitly and copy the pattern verbatim: schema+migration+seed (W0), service (W1), actions+UI+form-integration (W2-3), E2E (W3-4), legacy column TODO (W4-5). Zero task failures across all 3 specs using this pattern.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08-corporate-portal",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Any spec that includes a 'view' or 'download' feature (invoices, reports, receipts) MUST include explicit acceptance criteria for print layout \u2014 hiding sidebar/nav, resetting CSS layout, and page-break behavior. The corporate portal required 3+ fix commits for print CSS because the spec only specified CRUD, not print formatting. Add a print/PDF checklist item to every spec with document viewing.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-corporate-portal",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Invoices are stateful documents requiring a full lifecycle state machine (draft\u2192confirmed\u2192sent\u2192paid, with void/cancel transitions), not just CRUD. The corporate portal spec treated invoices as simple records and the full lifecycle was added post-spec. Any entity that has a 'status' column needs its state machine defined in requirements with valid transitions.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-corporate-portal",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Portal order creation actions must explicitly map which order columns they populate, cross-referencing the orders schema. Portal orders initially lacked buyerId, billingAddressSnapshot, and recipientId \u2014 all essential for invoicing. Create a 'field population matrix' in the design showing which columns each channel (POS, portal, admin) sets during order creation.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08-corporate-portal",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Neon serverless WebSocket connections have concurrency limits. Parallel DB queries that each open a connection (common in Promise.all patterns) can exhaust the pool. Batch parallel queries to max 4 concurrent. This is Neon-specific \u2014 other PostgreSQL providers may not have this limit.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "15-staff-user-management",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Features used daily (staff management, order entry) belong in the main sidebar, not buried under Settings. Staff management was initially placed at /admin/settings/staff and later moved to /admin/staff as a top-level sidebar item. During requirements, ask: 'Will this be used daily?' \u2014 if yes, it's a sidebar item, not a settings sub-page.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-staff-user-management",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Self-edit protection must distinguish between security-sensitive fields (role, status) and safe-to-edit fields (name, email). The initial implementation blocked ALL edits for the logged-in user, which was rejected at acceptance. Design docs should specify per-field editability for self-edit scenarios.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-staff-user-management",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Never use object references in React useEffect dependency arrays \u2014 always use primitive identifiers (e.g., staff.id instead of staff). Object identity changes on every render, causing infinite re-render loops. This caused a production-breaking bug in the staff dialog. Consider adding react-hooks/exhaustive-deps lint rule with object-dep warnings.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "16-order-status-separation",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "When a single column encodes multiple independent dimensions (order lifecycle + fulfillment + payment), split into separate columns with dedicated enums and state machines. The monolithic order_status enum made valid states like 'dispatched but unpaid' unrepresentable. 3-field model (orderStatus, fulfillmentStatus, paymentStatus) eliminated impossible-state bugs.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-order-status-separation",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Migrations for enum-to-multi-column refactors must include: (1) idempotency guards (IF NOT EXISTS) for safe re-runs, (2) explicit CASE expressions for EVERY existing enum value including edge cases (refunded, partially_refunded), (3) a test case per existing value. Consider 2-phase approach: add columns with defaults \u2192 backfill script \u2192 drop old column, rather than a single complex migration.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "16-order-status-separation",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Specs should describe WHAT information to display, not HOW to render it. The spec prescribed computeCompositeLabel() for status display, but the implementation used a two-badge approach that was better UX. Acceptance criteria should specify 'display order status, fulfillment status, and payment status' \u2014 not 'call computeCompositeLabel and render as a single string'.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "16-order-status-separation",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "When a spec deprecates or replaces a DB column (e.g., order.status replaced by documentStatus + paymentStatus + fulfillmentStatus), the spec MUST include a task that greps for ALL references to the old field across the entire codebase and migrates every consumer. Spec 16 only updated the orders list page and order creation, leaving the POS modal (isPaid check), refund service (status validation), refund dialog (button visibility), void invoice button, and payment completion flow all reading the stale legacy field. This caused paid orders to not show the Refund button, refunds to fail silently, and incorrect status transitions. The grep task should be in the final wave as a sweep.",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Specs that introduce a new data entity (e.g., store credit) must trace its FULL lifecycle: creation, storage, redemption at POS, redemption on portal, and reversal on refund. Spec 17 covered issuance and portal payment but missed POS redemption (balance display, amount cap, split payment, balance deduction) and refund reversal (returning credit to customer). This resulted in 16 post-spec fix commits \u2014 more than the spec itself.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "NEVER use React useTransition for server action calls. useTransition silently drops errors \u2014 if the action throws or returns an error, the UI shows nothing. This has caused bugs in: driver dispatch (start deliveries), AR action buttons (void, cancel remaining, apply deposit), and POS payment screen. Always use async/await with try/catch and toast.error() instead.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "Do not wrap an Input inside a shadcn Popover trigger. Popover's open/close state changes cause React to unmount and remount the trigger element, making the Input lose focus on every keystroke. Use a manually positioned dropdown div (absolute positioning) alongside a standalone Input instead.",
      "source": "debugging",
      "severity": "medium"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "When a spec introduces a payment method that can be used at POS, the spec must also update processGenericPayment (src/lib/payments/process-payment.ts) to handle the new method's side effects. Store credit required atomically deducting from customer balance \u2014 but this wasn't in the spec. The generic payment handler treats all methods the same by default, which is incorrect for methods with balance tracking.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Tax refund calculations must have a proportional fallback when the external tax provider (TaxJar/Avalara) is unavailable. The refund service was silently setting taxRefundAmount=0 on provider failure, meaning tax was never reversed in refund journal entries. Fallback: full refund = refund all tax; partial refund = tax * (refundAmount / grandTotal).",
      "source": "debugging",
      "severity": "high"
    },
    {
      "spec_name": "17-store-credit-credit-notes",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "Get domain expert (CPA) consultation BEFORE writing the spec when the feature has accounting or tax implications. Spec 17 consulted a CPA on Virginia sales tax law for store credit, which revealed: no tax reversal on store credit issuance, store credit is a liability (not revenue), and redemption is taxed on the new purchase. This shaped the entire design and prevented incorrect journal entries.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06c-accounts-payable",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "When designing page URLs for a new module, consider cross-spec user workflows and mental models, not just the technical domain. AP pages were initially at /admin/accounting/vendors and /admin/accounting/bills but were relocated to /admin/purchasing/ post-implementation because users think of vendors, bills, and POs as 'purchasing' \u2014 not 'accounting'. This required 3 fix commits (page moves, layout fixes, title restoration). During requirements, ask: 'Where would the user look for this?' and cross-reference with pages from adjacent specs.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06c-accounts-payable",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "The AR\u2192AP mirror pattern is highly effective. Copying 06b's document state machine (draft\u2192posted\u2192partially_paid\u2192paid), sub-ledger tagging (subLedgerType='vendor'), settings-based account resolution, and JE templates produced a flawless 62/62 acceptance with zero implementation failures. For any complementary module pair (sales/purchasing, AR/AP, income/expense), design the second by explicitly mirroring the first.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06c-accounts-payable",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Sub-ledger tagging on journal lines must be enforced structurally, not by convention. If any AP JE builder forgets subLedgerType='vendor' on the AP account line, the AP Aging report silently under-reports. Consider a builder pattern or wrapper function that always sets sub-ledger tags when the target account is AP or AR. Convention-based approaches have failed to prevent tag omission across 3 accounting specs.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06c-accounts-payable",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Include explicit JE templates (showing every debit/credit line with account names and amounts) in design docs for every financial transaction. The early payment discount 3-way JE (AP debit for full balance, bank credit for net amount, Purchase Discounts credit for discount) worked on first implementation because the template was unambiguous. Accounting specs without JE templates have a 50%+ bug rate on journal entry construction.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "14-rbac-module-permissions",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Cross-cutting refactors (like adding permission checks to all server actions) should use a canary approach: update 2-3 representative action files first, run quality gates, then batch the rest. Wave 4 updated 26 action files across 7 tasks in one wave. It worked, but the verification overhead was high and the risk of a regression affecting the entire app was concentrated in one wave. A 2-phase approach (canary wave + bulk wave) would be safer.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-rbac-module-permissions",
      "date": "2026-04-01",
      "category": "design",
      "lesson": "Critical shared files (auth.ts, middleware.ts) should be modified in single-task waves, never in waves with other tasks that also modify shared files. Wave 2 of the RBAC spec required a manual merge conflict resolution in auth.ts. Isolating shared-file modifications to their own wave eliminates merge risk and makes rollback trivial.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "14-rbac-module-permissions",
      "date": "2026-04-01",
      "category": "implementation",
      "lesson": "All server action files must use the standard ActionResult<T> return type. The designer module used a custom DesignerActionResult type, which required special handling during the RBAC refactor. Non-standard return types in action files should be flagged and normalized during validation, before any cross-cutting refactor begins.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "14-rbac-module-permissions",
      "date": "2026-04-01",
      "category": "requirements",
      "lesson": "When a spec creates UI components that depend on features from another spec (e.g., PermissionsTab needs staff CRUD from spec 15), track the cross-spec dependency explicitly in requirements.md. The PermissionsTab was 'ready but unwired' at acceptance because its mountpoint didn't exist yet. Cross-spec UI dependencies should be listed in a 'Depends On' section so acceptance testing knows which criteria to mark as deferred.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "18-po-approval-workflow",
      "date": "2026-04-03",
      "category": "design",
      "lesson": "When one component produces a URL with query params (e.g., dashboard card links to ?status=pending_approval) and another component consumes it (list page reads the param), both tasks must explicitly call out this URL contract. Missing this caused the only acceptance failure in spec 18.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "18-po-approval-workflow",
      "date": "2026-04-03",
      "category": "implementation",
      "lesson": "When adding fields to a shared interface (e.g., POWithDetails), expect test fixture updates across 5-15 files. The tasker should include an explicit blast-radius task for updating test fixtures rather than treating it as an implicit side effect of the type change task.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "18-po-approval-workflow",
      "date": "2026-04-03",
      "category": "design",
      "lesson": "Inngest event dispatch belongs in the server action layer, not the service layer. Services should be pure DB operations; actions orchestrate side effects (email notifications, background jobs). This keeps the service testable without mocking Inngest.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "18-po-approval-workflow",
      "date": "2026-04-03",
      "category": "implementation",
      "lesson": "This codebase has no SessionProvider/useSession. For client components needing role-based UI, create a getSessionContextAction server action that returns {userId, isManagerOrOwner}. Call it at page load alongside data fetching. If this pattern repeats in 2+ more specs, add SessionProvider globally instead.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Do not hardcode migration numbers in tasks.md. Use a placeholder like 00XX and resolve to the next available number at execution time by checking the migrations directory. Spec 18 and 19 ran concurrently and both claimed 0027.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Before starting spec-loop execution, verify that all quality gate commands actually run successfully. The lint gate was broken (Next.js 16 removed next lint) and was only discovered post-implementation. Run each gate command once in the init step.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "When making a NOT NULL column nullable, add a T-SWEEP task to grep all references and verify compatibility. In this spec, the sweep confirmed no changes were needed, but it would have caught issues if any code asserted non-null on the field.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "requirements",
      "lesson": "Detailed task descriptions with exact code snippets, line numbers, and import paths produce 100% first-pass success rates. The extra time spent in spec planning (verified interface registry, exact file locations) pays off dramatically in zero-retry execution.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "testing",
      "lesson": "Mocking db.transaction with nested tx.select/tx.insert chains is slow and error-prone. Consider creating a shared createMockTransaction() test utility that returns a pre-configured tx mock with chainable select/delete/insert methods.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "19-product-supply-link-and-material-logging",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Update state.json task statuses after EVERY task completion, not in a batch at the end. The acceptor flagged stale pending statuses because waves 2-6 were batch-updated after execution instead of incrementally.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06e-purchase-tracking-waste",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Use FK tables for categories from the start, not enums. Spec 06e used a 4-value InventoryCategory enum that was immediately replaced by a supply_categories table in spec 06k. Enums are appropriate for fixed states (order status), not for user-managed domain categories.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06e-purchase-tracking-waste",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Verify balance/aggregate formulas against accounting principles before coding. The getCategoryInventoryBalance formula initially omitted COGS recognized from the subtraction, requiring a post-acceptance fix.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06k-supply-item-categories",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When adding a FK to replace a deprecated enum field, use a backfill migration that maps old enum values to new FK rows. Mark the old field @deprecated but do not remove it immediately \u2014 downstream code may still reference it.",
      "source": "retro",
      "severity": "medium",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "stem-supply-item-linking",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "When designing a NOT NULL column, consider whether future specs will need it nullable. orderMaterialUsage.stemTypeId was NOT NULL but two specs later (19) needed it nullable for resale products and freeform materials. If the domain has obvious expansion paths, make it nullable from the start.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "stem-supply-item-linking",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Design reusable UI helpers without assuming a specific productType. buildPrePopulatedRows in the stem log form was generic enough to support both standard and custom product types, enabling spec 20 to reuse it without changes.",
      "source": "retro",
      "severity": "low"
    },
    {
      "spec_name": "20-custom-order-material-spec",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Server actions cannot return Map, Set, or other non-serializable types. Always use Record<string, T> or Array<T> for server action return types. Design.md specified Map but implementation required Record.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "20-custom-order-material-spec",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "For stock tracking, use fire-and-forget pattern for post-completion deductions. Stock counts should never block order completion \u2014 the cost of a blocked sale far exceeds the cost of a temporary stock discrepancy.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "20-custom-order-material-spec",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Allow negative stock quantities with warnings rather than blocking operations. Florist inventory counts are frequently inaccurate (missed receiving, unlogged waste), and blocking sales over stock count issues is unacceptable for the business.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-purchase-order-workflow",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Contract-first types in Wave 0 (all shared interfaces before parallel service work) produced 100% first-pass success across 3 parallel services. Always ship shared types as the first wave task.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "15-purchase-order-workflow",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "When a migration adds columns to a Drizzle-managed table, also add the columns to the Drizzle schema file \u2014 even if nullable. Raw SQL (db.execute) bypasses TypeScript type safety and breaks when columns are renamed. matching-service.ts had this issue with vendor_bills.po_id and match_status.",
      "source": "retro",
      "severity": "high",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "15-purchase-order-workflow",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Always check 'ls src/db/migrations/' before assigning a migration number. Spec 15-staff took 0019, so this spec correctly used 0020. Collision would have caused a runtime crash on startup.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "15-purchase-order-workflow",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "Assign each shared file (package.json, sidebar, schema index) to exactly one task per wave. Spec 15-PO isolated package.json to T-7 in Wave 2 and sidebar to T-17 in Wave 5 \u2014 zero merge conflicts across 18 tasks.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08a-unified-customers",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "When a migration removes table exports (corporateAccounts, corporateContacts, etc.), the task description must list every removed export by name AND include a grep command to discover all callers. This prevents surprise compile errors in downstream waves.",
      "source": "retro",
      "severity": "high",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "08a-unified-customers",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "When a session/context type changes shape (e.g., CorporateSession), group ALL consuming pages/components into a single task. Splitting session-dependent files across parallel tasks causes merge conflicts and inconsistent session shapes. Spec 08a handled 12 portal pages in one task (T-21) for this reason.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "08a-unified-customers",
      "date": "2026-04-04",
      "category": "implementation",
      "lesson": "Do not list files in a task's Files array if the task description says 'no change needed.' T-7 listed src/middleware.ts but didn't modify it, causing false negatives in file-existence verification. Use a comment in the description instead.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "08a-unified-customers",
      "date": "2026-04-04",
      "category": "design",
      "lesson": "For large migrations that remove or rename schema fields, add a dedicated final-wave cleanup task that runs grep verification for stale references. Spec 08a's T-24 (Wave 4) caught leftover references that would have broken at runtime.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "When two Wave-0 parallel tasks both need to define the same type, make one depend on the other or pre-create the type file as a separate task. Inline type definitions in parallel tasks cause type conflicts when a downstream file imports from both.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Client components (use client) cannot call server-side DB utilities (getAccountingToday, getAccountBalance). Any server utility needed by a client component must have a server action wrapper. Task descriptions for client component pages must anticipate this and list the wrapper action as a dependency.",
      "source": "retro",
      "severity": "high"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "All bank-related JE lines must include subLedgerType: \"bank_account\" and subLedgerEntityId: bankAccountId. This enables proper per-bank-account ledger filtering. Missing sub-ledger tags was caught by acceptance testing, not unit tests.",
      "source": "retro",
      "severity": "high",
      "enforceable": true,
      "check": "grep_for_old_field_references"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "design",
      "lesson": "Combining schema + foundational service in Wave 0 (e.g., 9 tables + resolveGlAccountId) eliminates a dependency bottleneck. Without this, every Wave 1 service would depend on a Wave 1 task, creating circular dependencies.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "When refactoring function return types (e.g., PostJournalEntryResult -> TipPayoutDocResult), keep the old file as a re-export shim. This provides backwards compatibility: import { buildAndPostTipPayout } from tip-payout-builder still works while new code imports from tip-payout-service.",
      "source": "retro",
      "severity": "medium"
    },
    {
      "spec_name": "06d-bank-recon-cc-settlement",
      "date": "2026-04-05",
      "category": "implementation",
      "lesson": "Import manifest (exact export names from completed waves) should be included in every parallel agent prompt. This eliminated 100% of cross-agent naming mismatches in a 23-task spec with 6-way parallelism.",
      "source": "retro",
      "severity": "high"
    }
  ]
}