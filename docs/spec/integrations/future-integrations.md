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

## GL / Accounting posting for contract value and payment schedules (govoo_contracts, addendum)
- **Status:** `[OPTIONAL]`, off by default (FR-CM-15, BR-CM-008) — same pattern and same
  confirmation discipline as the capital-events hook immediately above; this is a second instance
  of the identical "optional GL hook, disabled until a client accounting policy is confirmed"
  pattern, not a new integration concept.
- **If later confirmed:** implement as the hook scoped in `modules/govoo_contracts.md` FR-CM-15;
  do not build this ahead of confirmation.

## Contract intelligence — `govoo_ai` (govoo_contracts addendum §3.2 CM-F19/CM-F20, §8 step 3)
- **Status:** `[CONFIRM]` / out of scope for this addendum pass. The addendum's own build sequence
  (§8) places "Contract intelligence" as step 3, explicitly **after** both `govoo_ai` and
  `govoo_contracts` are independently stable — it is not part of `govoo_contracts`' core build.
  `govoo_ai` itself is **not specced anywhere in this repository** as of this addendum; only the
  fact that `govoo_contracts` is shaped to eventually support it (via `document_ids`/
  `obligation_ids`) is recorded here.
- **Non-negotiable constraints once `govoo_ai` is built** (addendum §4, §6, §7): AI retrieval must
  honour existing record rules/company scope — an AI query must never surface a contract the
  requesting user could not otherwise read; AI output is never auto-committed to a `govoo.contract`/
  `govoo.contract.obligation` field without human confirmation (human-in-the-loop); contract
  workflows must never depend on AI being available (graceful degradation, same discipline as
  Documents/Sign feature flags elsewhere in this repository).
- **Data residency / provider items:** addendum §9 items 1, 2, 6 (AI provider/hosting region/DPA,
  self-hosted-model necessity, token-cap/pricing metering) are recorded in
  `decisions/open-decisions.md` as unresolved, even though they belong to `govoo_ai` rather than
  `govoo_contracts` proper — the addendum bundles both modules in one source document, and the
  instruction to add "all of the addendum's open items" is not narrowed to only the
  `govoo_contracts`-specific ones.

## Approvals app
- **Status:** available in the Odoo standard-apps list (source §3.3) but not adopted for v1 — see
  rationale in `integrations/odoo-standard-apps.md`.

## Any integration not named in the source
Per source §25 ("Do Not Over-Engineer"), no additional integrations (mobile push, SMS gateways,
third-party e-KYC providers, etc.) should be introduced speculatively. If a future requirement
needs one, it should be added here first as a `[CONFIRM]`/proposed integration, following the
template in `integrations/odoo-standard-apps.md`, before any code is written against it.
