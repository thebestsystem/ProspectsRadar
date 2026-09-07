<!-- last_verified: 2026-09-07 -->
# Feature: ProspectsRadar Agency Dashboard

## Purpose
Provide e-commerce and SEO agencies with an actionable pipeline of pre-qualified leads based on AI visibility scores (0-100), accompanied by identified pain points, enriched decision-maker contacts, pre-written cold emails, and audit PDF downloads.

## Used By
- UI: `/` page (ProspectsRadar agency pipeline & live audit demo)
- API: `GET /leads`, `GET /leads/stats`, `POST /scan`, `POST /leads/batch`, `GET /leads/export.csv`, `GET /leads/{id}/pdf`

## Core Functions
- `apps/web/src/components/dashboard/radar-stats-cards.tsx` — 4 KPI cards (qualified leads count, critical pain rate < 40, average market score, top failing pillar)
- `apps/web/src/components/dashboard/prospects-table.tsx` — Interactive leads table with vertical filtering, pain badges, decision maker coordinates, modal cold pitch preview (1-click copy), and CSV/PDF export actions
- `apps/web/src/components/dashboard/live-scan-card.tsx` — Live 5-pillar instant auditor for prospect URLs with detailed breakdown
- `apps/web/src/lib/queries.ts` — `useLeads`, `useLeadsStats`, `useScanTarget`, `useLaunchBatchScan`

## Canonical Files
- Dashboard KPI pattern: `apps/web/src/components/dashboard/radar-stats-cards.tsx`
- Qualified prospects pipeline: `apps/web/src/components/dashboard/prospects-table.tsx`
- Live audit simulation: `apps/web/src/components/dashboard/live-scan-card.tsx`

## Inputs
- Vertical filter selection (`all`, `shopify_fr`, `mode_beaute`, `maison_deco`)
- Target URL for live instant scan (`POST /scan`)

## Outputs
- `GET /leads` → `ProspectLead[]` (filtered leads list)
- `GET /leads/stats` → `LeadsStats` (KPI aggregations)
- `POST /scan` → `AuditResult` (instant 5-pillar assessment)
- `GET /leads/export.csv` → Formatted CSV file for Instantly/Smartlead/HubSpot
- `GET /leads/{id}/pdf` → ReportLab white-label audit report PDF

## Flow
- Page loads → parallel query hooks (subscription, file stats, generation jobs,
  upload activity).
- KPI cards render plan + status badge, storage used, count of successful generations,
  count of failed generations.
- Recent-generations table shows the newest ~6 jobs with prompt, status badge,
  and created date; links to `/generate`.
- Storage activity chart renders server-aggregated daily counts.

## Edge Cases
- API unavailable → error/loading states; the activity chart does not show a
  false zero while loading.
- A KPI stat card whose query errors renders a muted `—`, never a default
  `FREE`/`0 B`/`0` — a transient blip must not confidently misreport a paying
  user's plan or storage.
- No subscription row → treated as the Free tier (status inactive).
- No generations yet → empty state in the recent table; counts show 0.

## UX States
- Loading: skeleton placeholders for cards, table, and chart
- Empty: "No generations yet" in the recent table
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_generation.py` (jobs feed the cards/table),
  `services/api/tests/test_billing.py`, `services/api/tests/test_upload_activity.py`
- Required cases: subscription present/absent, jobs with mixed statuses, empty
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: all pytest green, ruff/eslint clean, `next build` succeeds

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Admin](admin.md)
- [App Workflows](../app-workflows.md)
