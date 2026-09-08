# Module: Portal + Dashboard

Source: §2 (row "Administration"/portal), §6.2, §6.3, §12 of the source spec. Build order:
**Step 8** (depends on all custom modules).

## Module overview
- **Purpose:** External self-service access for directors and shareholders, plus a personalized
  internal dashboard.
- **Responsibility:** Portal controllers/views over `govoo_board` and `govoo_shares` data, gated by
  the record rules defined in each owning module's security file; a dashboard layer aggregating
  meetings, resolutions, compliance RAG status, and cap-table summaries per the logged-in user's
  access.
- **Depends on (Odoo):** `portal`, `website`; Spreadsheet Dashboards (Enterprise) or OCA
  `spreadsheet_dashboard_oca` (feature-flagged).
- **Depends on (custom):** all of `govoo_base`, `govoo_secretarial`, `govoo_shares`, `govoo_board`,
  `govoo_compliance`, `govoo_rw`, `govoo_evaluation`.
- **Owns:** portal controllers, portal-specific views/templates, dashboard aggregation views.
- **Must NOT own:** any new transactional data model — this layer is presentation over data owned
  elsewhere.

## Note on packaging
`[ENGINEERING DETAIL]` The source does not specify whether Portal + Dashboard is one module or
distributed as portal views shipped inside each owning module (`govoo_board` ships its own portal
templates, etc.) with a separate thin `govoo_dashboard` module for the aggregation layer. Either is
consistent with the source. **Recommended:** ship portal templates inside each owning module (so
`govoo_board`'s portal views live in `govoo_board/views/portal_templates.xml`), and create a single
thin `govoo_portal` (or `govoo_dashboard`) module only for the cross-module aggregated dashboard,
to avoid one module depending on every other module purely for UI.

## What it implements
### Director portal (FR-PORTAL-001)
- Views: meetings, board packs (redacted per authorization), minutes, resolutions — filtered to
  committees the logged-in partner belongs to.
- Actions: cast votes on eligible resolutions.
- Record rules: see `security/record-rules.md`.

### Shareholder portal (FR-PORTAL-002)
- Views: own `govoo.share.holding` rows, shareholder-type resolutions.
- Actions: cast votes on eligible shareholder resolutions.
- Record rules: see `security/record-rules.md`.

### Portal access-token security (FR-PORTAL-003)
- Every portal-exposed model uses `portal.mixin`, `_compute_access_url`, and controllers guarded by
  both a valid access token **and** the underlying record rule — never token-only or
  URL-obscurity-only exposure (BR-SEC-006).

### Dashboard
- Personalized internal dashboard: upcoming meetings, open resolutions requiring the user's vote,
  compliance RAG (red/amber/green) summary, cap-table snapshot (role-appropriate).
- Enterprise: Spreadsheet Dashboards. Community fallback: OCA `spreadsheet_dashboard_oca` or a
  simpler Kanban/list-based dashboard view — feature-flagged per
  `architecture/technology-standards.md` §8.

## Tests
- TC-SEC-005: portal record-rule enforcement (own-committee/own-holding only).
- TC-SEC-006: direct-URL/access-token guessing denied.

## Definition of Done checklist
See `implementation/module-checklists.md` — `Portal + Dashboard` section.
