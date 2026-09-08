# Future / Not-Yet-Confirmed Integrations

Source: §3.3, §8.4, §13 items 6-7 of the source spec. This file lists integrations that are either
explicitly out of scope for v1, or contingent on a `[CONFIRM]` decision — kept separate from the
active integrations in this directory so an implementer does not accidentally build against an
unconfirmed API.

## RDB / Irembo government filing API
- **Status:** `[CONFIRM]` — the source explicitly states no public filing API is confirmed
  available (§13 item 6).
- **Current behavior (v1):** `govoo_compliance` generates filing-pack exports for manual portal
  submission instead (`workflows/compliance.md`, FR-COMP-004).
- **If later confirmed:** the filing-pack export step and the "record filed" step
  (`reference_no`/`filed_date`) were deliberately kept as distinct steps in the workflow design
  precisely so that an automated submission call could be inserted between them without a breaking
  model change — see `modules/govoo_compliance.md` FR-COMP-004 failure-behavior note.

## RRA EBM/VSDC e-invoicing
- **Status:** described in the source as "the one confirmed real-time government API" available —
  but scoped entirely to the **optional** `govoo_rw_ebm` module, not the governance core.
- See `modules/optional-integrations.md` for detail. This is not a "future" integration in the
  sense of being unconfirmed — it is confirmed to exist, but deliberately out of the governance
  core's v1 scope.

## GL / Accounting posting for capital events
- **Status:** `[CONFIRM]` (source §13 item 7) — off by default (FR-SHARE-005, BR-SHARE-004).
- **If later confirmed:** implement as the hook already scoped in `modules/govoo_shares.md`
  FR-SHARE-005; do not build this ahead of confirmation.

## Approvals app
- **Status:** available in the Odoo standard-apps list (source §3.3) but not adopted for v1 — see
  rationale in `integrations/odoo-standard-apps.md`.

## Any integration not named in the source
Per source §25 ("Do Not Over-Engineer"), no additional integrations (mobile push, SMS gateways,
third-party e-KYC providers, etc.) should be introduced speculatively. If a future requirement
needs one, it should be added here first as a `[CONFIRM]`/proposed integration, following the
template in `integrations/odoo-standard-apps.md`, before any code is written against it.
